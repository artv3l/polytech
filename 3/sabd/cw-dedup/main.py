import dedup
import stats
import params
import pathlib


if __name__ == "__main__":
    folder = pathlib.Path.cwd() / pathlib.Path("test")

    files = [
        folder / pathlib.Path("test.txt")
    ]

    with dedup.Storage(
        "mongodb://root:root@localhost:27017/", "sabd-cw", "refs", "test/data.bin"
    ) as storage:
        with (
            open(files[0], "rb") as file,
            open(params.fmt_ref(files[0]), "wb") as ref_file,
        ):
            print(stats.store_operation_stats(file, params.chunk_size, ref_file, storage))

        with (
            open(params.fmt_ref(files[0]), "rb") as ref_file,
            open(params.fmt_deref(files[0]), "wb") as out_file,
        ):
            print(stats.get_operation_stats(ref_file, out_file, storage))

        stats.graphs(storage, files, stats.CalcChunkSizeParams())
