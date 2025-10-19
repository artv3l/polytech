import dedup
import stats
import params
import pathlib
import sys

def stats_one(file: pathlib.Path, storage: dedup.Storage):
    print(file.name)
    with (
        open(file, "rb") as in_file,
        open(params.fmt_ref(file), "wb") as ref_file,
    ):
        print(stats.store_operation_stats(in_file, params.chunk_size, ref_file, storage))

    with (
        open(params.fmt_ref(file), "rb") as ref_file,
        open(params.fmt_deref(file), "wb") as out_file,
    ):
        print(stats.get_operation_stats(ref_file, out_file, storage))
    print()


if __name__ == "__main__":
    with dedup.Storage(
        "mongodb://root:root@localhost:27017/", "sabd-cw", "refs", "test/data.bin"
    ) as storage:
        stats_one(pathlib.Path(sys.argv[1]), storage)
