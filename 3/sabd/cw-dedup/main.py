import dedup
import stats


if __name__ == "__main__":
    filepath: str = "test.txt"

    with dedup.Storage(
        "mongodb://root:root@localhost:27017/", "sabd-cw", "refs", "data.bin"
    ) as storage:
        with (
            open(filepath, "rb") as file,
            open(f"{filepath}.ref", "wb") as ref_file,
        ):
            stats.store_operation_stats(file, 4, ref_file, storage)

        with (
            open(f"{filepath}.ref", "rb") as ref_file,
            open(f"{filepath}.ref.out", "wb") as out_file,
        ):
            stats.print_exec_time(
                stats.bind(
                    dedup.extract_file,
                    ref_file,
                    dedup.get_hash_size(),
                    out_file,
                    storage
                )
            )
