import pymongo
import dedup
import stats


if __name__ == "__main__":
    filepath: str = "test.txt"

    client = pymongo.MongoClient("mongodb://root:root@localhost:27017/")
    db = client["sabd-cw"]
    collection = db["refs"]

    with (
        open("data.bin", "a+b") as datafile,
        open(filepath, "rb") as file,
        open(f"{filepath}.ref", "wb") as ref_file,
    ):
        stats.store_operation_stats(file, 10 * 1024, ref_file, collection, datafile)

    with (
        open("data.bin", "a+b") as datafile,
        open(f"{filepath}.ref", "rb") as ref_file,
        open(f"{filepath}.ref.out", "wb") as out_file,
    ):
        stats.print_exec_time(
            stats.bind(dedup.extract_file, ref_file, 16, out_file, collection, datafile)
        )
