import util
import otf2
import argparse
import subprocess
import os


def write_otf2_trace(fp_in, fp_out, timer_res):

    with otf2.writer.open(fp_out, timer_resolution=timer_res) as trace:
        files, functions, events, rank_count = util.get_stats_from_recorder(fp_in)
        root_node = trace.definitions.system_tree_node("root_node")
        generic_system_tree_node = trace.definitions.system_tree_node("dummy", parent=root_node)
        generic_paradigm = trace.definitions.io_paradigm(identification="generic",
                                                               name="GENERIC I/O",
                                                               io_paradigm_class=otf2.IoParadigmClass.SERIAL,
                                                               io_paradigm_flags=otf2.IoParadigmFlag.NONE)

        regions = {name: trace.definitions.region(name) for name in functions}
        io_files = {file_name: trace.definitions.io_regular_file(file_name, scope=generic_system_tree_node) for file_name in files}
        io_handles = {file_name: trace.definitions.io_handle(file=io_files.get(file_name),
                                                                                name=file_name,
                                                                                io_paradigm=generic_paradigm,
                                                                                io_handle_flags=otf2.IoHandleFlag.NONE) for file_name in files}

        location_groups = {f"rank {rank_id}": trace.definitions.location_group(f"rank {rank_id}",
                                                                               system_tree_parent=generic_system_tree_node) for rank_id in range(rank_count)}

        locations = {f"rank {rank_id}": trace.definitions.location("Master Thread", group=location_groups.get(f"rank {rank_id}")) for rank_id in range(rank_count)}

        events.sort(key=lambda x: x.start_time)
        t_last = 0
        if len(events) > 0:
            t_start = events[0].get_start_time_ticks(timer_res)
        for event in events:
            if event.function not in ["read", "write", "lseek"]:
                continue
            if event.function == "write":
                io_mode = otf2.IoOperationMode.WRITE
            elif event.function == "read":
                io_mode = otf2.IoOperationMode.READ

            writer = trace.event_writer_from_location(locations.get(f"rank {event.rank_id}"))

            writer.enter(event.get_start_time_ticks(timer_res) - t_start,
                         regions.get(event.function))

            if event.function in ["read", "write"]:
                file_name = event.args[0].decode("utf-8")
                size = int.from_bytes(event.args[2], "big")
                writer.io_operation_begin(time=event.get_start_time_ticks(timer_res) - t_start,
                                          handle=io_handles.get(file_name),
                                          mode=io_mode,
                                          operation_flags=otf2.IoOperationFlag.NONE,
                                          bytes_request=size,
                                          matching_id=event.level)

                writer.io_operation_complete(time=event.get_end_time_ticks(timer_res) - t_start,
                                             handle=io_handles.get(file_name),
                                             bytes_result=size,
                                             matching_id=event.level)

            elif event.function == "lseek":
                #whence = otf2.IoSeekOption(int.from_bytes(event.args[2], "big"))
                file_name = event.args[0].decode("utf-8")
                whence = otf2.IoSeekOption(int.from_bytes(event.args[2], "big"))
                size = int.from_bytes(event.args[1], "big")
                writer.io_seek(time=event.get_start_time_ticks(timer_res) - t_start,
                               handle=io_handles.get(file_name),
                               offset_request=size,
                               whence=whence,
                               offset_result=size)
            else:
                print(event.function)

            writer.leave(event.get_end_time_ticks(timer_res) - t_start,
                         regions.get(event.function))

            t_last = event.get_end_time_ticks(timer_res) - t_start


def main():

    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=str, help="file path to the darshan trace file")
    ap.add_argument("-o", "--output", type=str, help="specifies different output path, default is ./trace_out")
    ap.add_argument("-t", "--timer", type=int, help="sets timer resolution, default is 1e9")
    args = ap.parse_args()

    fp_in = args.file
    fp_out = "./trace_out" if args.output is None else args.output
    timer_res = int(1e9) if args.timer is None else args.timer

    if os.path.isdir(fp_out):
        subprocess.run(["rm", "-rf", fp_out])

    write_otf2_trace(fp_in, fp_out, timer_res)


if __name__ == '__main__':
    main()
