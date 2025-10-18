import dedup
import stats
import params
import pathlib


if __name__ == "__main__":
    filepath = pathlib.Path("test/01. Barricades.flac")

    with dedup.Storage(
        "mongodb://root:root@localhost:27017/", "sabd-cw", "refs", "test/data.bin"
    ) as storage:
        with (
            open(filepath, "rb") as file,
            open(params.fmt_ref(filepath), "wb") as ref_file,
        ):
            stats.store_operation_stats(file, params.chunk_size, ref_file, storage)

        with (
            open(params.fmt_ref(filepath), "rb") as ref_file,
            open(params.fmt_deref(filepath), "wb") as out_file,
        ):
            stats.get_operation_stats(ref_file, out_file, storage)
