import recorder_viz
from Events import Event


def get_stats_from_recorder(fp):
    events = []
    reader = recorder_viz.RecorderReader(fp)
    func_names = reader.funcs
    files = set()
    for lm in reader.LMs:
        files = files.union(lm.filemap)

    for rank_id, rank in enumerate(range(reader.GM.total_ranks)):
        records = reader.records[rank]
        for i in range(reader.LMs[rank].total_records):

            record = records[i]
            start_time, end_time, level, function, tid, arg_count, args = record.tstart, record.tend, record.level, func_names[record.func_id], record.tid, record.arg_count, record.args
            largs = []
            for j in range(arg_count):
                largs.append(args[j])

            events.append(Event.get_event(rank_id, function, start_time, end_time, level, tid, largs))

    return files, func_names, events, reader.GM.total_ranks


def split_evenly(size: int, num_chunks: int) -> list[int]:
    part_size = size // num_chunks
    residue = size % num_chunks
    factors = [part_size for x in range(num_chunks)]
    i = 0
    while residue > 0:
        factors[i] += 1
        residue -= 1
    return sorted(factors)
