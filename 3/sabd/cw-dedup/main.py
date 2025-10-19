import dedup
import stats
import params
import pathlib


def stats_one(file: pathlib.Path, storage: dedup.Storage):
    print(file.name)
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
    print()


if __name__ == "__main__1":
    folder = pathlib.Path.cwd() / pathlib.Path("test")

    files = [
        # folder / pathlib.Path("01. Barricades.flac"),
        # folder / pathlib.Path("Fedora-KDE-Desktop-Live-42-1.1.x86_64.iso"),
        folder / pathlib.Path("img.bmp"),
        folder / pathlib.Path("img2.bmp"),
    ]

    with dedup.Storage(
        "mongodb://root:root@localhost:27017/", "sabd-cw", "refs", "test/data.bin"
    ) as storage:
        #for file in files:
        #    stats_one(file, storage)

        stats.calc_chunk_size(storage, files, stats.CalcChunkSizeParams(begin=2048, end=2048 * 10, count=30))

if __name__ == "__main__":
    folder = pathlib.Path.cwd() / pathlib.Path("test")
    for file in folder.iterdir():
        if file.suffix == ".json":
            jsons = stats.make_graph(file)
