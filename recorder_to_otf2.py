import constants
import util
import otf2
import argparse
import subprocess
import os
import Events


def write_otf2_trace(fp_in, fp_out, timer_res):

    with otf2.writer.open(fp_out, timer_resolution=timer_res) as trace:
        files, functions, events, rank_count = util.get_stats_from_recorder(fp_in)
        root_node = trace.definitions.system_tree_node("root_node")
        generic_system_tree_node = trace.definitions.system_tree_node("dummy", parent=root_node)
        posix_paradigm = trace.definitions.io_paradigm(identification="POSIX",
                                                               name="POSIX I/O",
                                                               io_paradigm_class=otf2.IoParadigmClass.SERIAL,
                                                               io_paradigm_flags=otf2.IoParadigmFlag.NONE)

        isoc_paradigm = trace.definitions.io_paradigm(identification="ISOC",
                                                               name="ISOC I/O",
                                                               io_paradigm_class=otf2.IoParadigmClass.SERIAL,
                                                               io_paradigm_flags=otf2.IoParadigmFlag.NONE)

        mpi_paradigm = trace.definitions.io_paradigm(identification="MPI",
                                                       name="MPI I/O",
                                                       io_paradigm_class=otf2.IoParadigmClass.PARALLEL,
                                                       io_paradigm_flags=otf2.IoParadigmFlag.NONE)

        paradigms = {"POSIX": posix_paradigm, "ISOC": isoc_paradigm, "MPI": mpi_paradigm}
        regions = {}

        offset_attribute = trace.definitions.attribute("Offset", description='Absolute read/write offset within a file.', type=otf2.Type.UINT64)
        io_files = {file_name: trace.definitions.io_regular_file(file_name, scope=generic_system_tree_node) for file_name in files}

        io_handles = {}
        # io_handles = {file_name: trace.definitions.io_handle(file=io_files.get(file_name),
        #                                                                         name=file_name,
        #                                                                         io_paradigm=generic_paradigm,
        #                                                                         io_handle_flags=otf2.IoHandleFlag.NONE) for file_name in files}

        location_groups = {f"rank {rank_id}": trace.definitions.location_group(f"rank {rank_id}",
                                                                               system_tree_parent=generic_system_tree_node) for rank_id in range(rank_count)}

        locations = {f"rank {rank_id}": trace.definitions.location("Master Thread", group=location_groups.get(f"rank {rank_id}")) for rank_id in range(rank_count)}
        t_start = 0

        for rank_id in range(rank_count):
            print(f"rank {rank_id}/{rank_count}")
            writer = trace.event_writer_from_location(locations.get(f"rank {rank_id}"))
            for event in sorted([e for e in events if e.rank_id == rank_id and not (e.function.startswith("__") or e.function == "MPI_Bcast")], key=lambda x: x.start_time):
                # if event.start_time > event.end_time:
                #     print("SUS:", event.function)
                #     continue

                # print(event.function, event.start_time, event.end_time, event.rank_id)
                if regions.get(event.function) is None:
                    s = "MPI I/O" if event.function.startswith("MPI") else "POSIX I/O"
                    regions[event.function] = trace.definitions.region(event.function,
                                                                       source_file=s,
                                                                       region_role=otf2.RegionRole.FILE_IO)
                print(event.function)
                writer.enter(event.get_start_time_ticks(timer_res) - t_start,
                             regions.get(event.function))

                if isinstance(event, Events.IoEvent):
                    atr = None if event.offset is None else offset_attribute

                    writer.io_operation_begin(time=event.get_start_time_ticks(timer_res) - t_start,
                                              handle=io_handles.get(event.path_name),
                                              mode=otf2.IoOperationMode(event.type),
                                              operation_flags=otf2.IoOperationFlag.NONE,
                                              bytes_request=event.size,
                                              matching_id=event.level,
                                              )

                    writer.io_operation_complete(time=event.get_end_time_ticks(timer_res) - t_start,
                                                 handle=io_handles.get(event.path_name),
                                                 bytes_result=event.size,
                                                 matching_id=event.level,
                                                 attributes={atr: event.offset})

                if isinstance(event, Events.IoSeekEvent):
                    writer.io_seek(time=event.get_start_time_ticks(timer_res) - t_start,
                                   handle=io_handles.get(event.path_name),
                                   offset_request=event.offset,
                                   # IoSeekOption ?
                                   whence=otf2.IoSeekOption(event.whence),
                                   offset_result=event.offset)

                elif isinstance(event, Events.IoCreateHandleEvent):

                    # create handle:
                    if io_handles.get(event.path_name) is None:
                        io_handles[event.path_name] = trace.definitions.io_handle(file=io_files.get(event.path_name),
                                                                                  name=event.path_name,
                                                                                  io_paradigm=paradigms.get(event.paradigm),
                                                                                  io_handle_flags=otf2.IoHandleFlag.NONE)

                    writer.io_create_handle(time=event.get_start_time_ticks(timer_res) - t_start,
                                            handle=io_handles.get(event.path_name),
                                            mode=otf2.IoAccessMode(event.mode),
                                            # we take only the first flag for both because the python bindings limitations
                                            creation_flags=tuple(otf2.IoCreationFlag(x) for x in event.creation)[0],
                                            status_flags=tuple(otf2.IoStatusFlag(x) for x in event.status)[0])


                elif isinstance(event, Events.IoDestroyHandleEvent):
                    writer.io_destroy_handle(time=event.get_start_time_ticks(timer_res) - t_start,
                                             handle=io_handles.get(event.path_name))

                writer.leave(event.get_end_time_ticks(timer_res) - t_start,
                             regions.get(event.function))


def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=str, help="file path to the darshan trace file")
    ap.add_argument("-o", "--output", type=str, help="specifies different output path, default is ./trace_out")
    ap.add_argument("-t", "--timer", type=int, help="sets timer resolution, default is 1e9")
    args = ap.parse_args()

    fp_in = args.file
    fp_out = "./trace_out" if args.output is None else args.output
    timer_res = int(1e7) if args.timer is None else args.timer

    if os.path.isdir(fp_out):
        #exit(1)
        subprocess.run(["rm", "-rf", fp_out])

    write_otf2_trace(fp_in, fp_out, timer_res)


if __name__ == '__main__':
    main()
