import datetime
import pymongo
import typing
import dedup
import params
import pathlib
import pydantic
import json
import matplotlib.pyplot as plt
import matplotlib.figure
import functools


def get_collection_size(collection: pymongo.collection.Collection) -> int:
    return collection.database.command("collstats", collection.name)["size"]


def get_file_size(file) -> int:
    old_position = file.tell()
    dedup.to_end_position(file)
    size = file.tell()
    file.seek(old_position)
    return size


def get_size(obj) -> int:
    if isinstance(obj, pathlib.Path):
        return obj.stat().st_size
    elif isinstance(obj, pymongo.collection.Collection):
        return get_collection_size(obj)
    else:
        return get_file_size(obj)


class StorageStatsDiff(pydantic.BaseModel):
    datafile_size: int
    db_size: int
    time_seconds: float


class StorageStats(pydantic.BaseModel):
    datafile_size: int
    db_size: int
    time: datetime.datetime

    def __sub__(self, other: "StorageStats") -> StorageStatsDiff:
        return StorageStatsDiff(
            datafile_size=self.datafile_size - other.datafile_size,
            db_size=self.db_size - other.db_size,
            time_seconds=(self.time - other.time).total_seconds(),
        )


class UserStats(pydantic.BaseModel):
    file_size: int
    ref_file_size: int


class BaseStats(pydantic.BaseModel):
    storage_stats_diff: StorageStatsDiff
    user_stats: UserStats

    # Скорость выполнения операции (B/s)
    @pydantic.computed_field
    @property
    def speed(self) -> float:
        return self.user_stats.file_size / self.storage_stats_diff.time_seconds


class StoreStats(BaseStats):
    # Процент дедупликации
    @pydantic.computed_field
    @property
    def dedup_ratio(self) -> float:
        return 1 - (self.storage_stats_diff.datafile_size / self.user_stats.file_size)

    # Общее изменение памяти (B)
    @pydantic.computed_field
    @property
    def mem_diff(self) -> int:
        return (
            self.storage_stats_diff.datafile_size
            + self.storage_stats_diff.db_size
            - self.user_stats.file_size
            + self.user_stats.ref_file_size
        )

    def __str__(self):
        return f"""Store:
    Total memory diff: {self.mem_diff / 2**20:.2f} MB
    User memory diff: {self.user_stats.file_size / 2**20:.2f} MB -> {self.user_stats.ref_file_size / 2**10:.2f} KB
    Dedup ratio: {self.dedup_ratio * 100:.2f} %
    Stored {self.user_stats.file_size / 2**20:.2f} MB in {self.storage_stats_diff.time_seconds:.2f} s, {self.speed / 2**20:.2f} MB/s"""


class GetStats(BaseStats):
    def __str__(self):
        return f"""Get:
    Get {self.user_stats.file_size / 2**20:.2f} MB in {self.storage_stats_diff.time_seconds:.2f} s, {self.speed / 2**20:.2f} MB/s"""


def get_storage_stats(storage: dedup.Storage) -> StorageStats:
    return StorageStats(
        datafile_size=get_size(storage.datafile),
        db_size=get_size(storage.collection),
        time=datetime.datetime.now(),
    )


def get_user_stats(file: typing.BinaryIO, ref_file: typing.BinaryIO) -> UserStats:
    return UserStats(file_size=get_size(file), ref_file_size=get_size(ref_file))


def store_operation_stats(
    file: typing.BinaryIO,
    chunk_size: int,
    ref_file: typing.BinaryIO,
    storage: dedup.Storage,
) -> StoreStats:
    storage_stats = get_storage_stats(storage)
    dedup.store_file(file, chunk_size, ref_file, storage)
    storage_stats_diff = get_storage_stats(storage) - storage_stats

    return StoreStats(
        storage_stats_diff=storage_stats_diff, user_stats=get_user_stats(file, ref_file)
    )


def get_operation_stats(
    ref_file: typing.BinaryIO, out_file: typing.BinaryIO, storage: dedup.Storage
) -> GetStats:
    storage_stats = get_storage_stats(storage)
    dedup.get_file(ref_file, params.hash_len, out_file, storage)
    storage_stats = get_storage_stats(storage) - storage_stats

    return GetStats(
        storage_stats_diff=storage_stats, user_stats=get_user_stats(out_file, ref_file)
    )


class CalcChunkSizeParams(pydantic.BaseModel):
    begin: int
    end: int
    count: int = 50


class FileInfo(pydantic.BaseModel):
    file_name: str
    file_size: int
    store_stats: StoreStats
    get_stats: GetStats


CalcChunkSizeResult = typing.Dict[int, typing.List[FileInfo]]


def fmt_stat(filename: pathlib.Path) -> pathlib.Path:
    return filename.with_name(filename.name + ".json")


def calc_chunk_size(
    storage: dedup.Storage,
    files: typing.List[pathlib.Path],
    calc_params: CalcChunkSizeParams,
):
    result: CalcChunkSizeResult = {}

    step = int((calc_params.end - calc_params.begin) / calc_params.count)
    for chunk_size in range(calc_params.begin, calc_params.end, step):
        storage.clean()
        result[chunk_size] = []

        for file in files:
            if not file.is_file():
                return
            file_size = get_size(file)
            if file_size == 0:
                continue

            file_name = file.relative_to(pathlib.Path.cwd())

            ref_filepath = params.fmt_ref(file_name)
            out_filepath = params.fmt_deref(file_name)
            with (
                open(file_name, "rb") as file_s,
                open(ref_filepath, "wb") as ref_file,
            ):
                store_stats = store_operation_stats(
                    file_s, chunk_size, ref_file, storage
                )
            with (
                open(ref_filepath, "rb") as ref_file,
                open(out_filepath, "wb") as out_file,
            ):
                get_stats = get_operation_stats(ref_file, out_file, storage)

            result[chunk_size].append(
                FileInfo(
                    file_name=file_name.name,
                    file_size=file_size,
                    store_stats=store_stats,
                    get_stats=get_stats,
                )
            )

            ref_filepath.unlink()
            out_filepath.unlink()

    result_json = {
        chunk_size: [file_info.model_dump() for file_info in file_infos]
        for chunk_size, file_infos in result.items()
    }
    json_filename = fmt_stat(file_name)
    with open(json_filename, "w") as stat_file:
        json.dump(result_json, stat_file, indent=4)


def extract_values(result: CalcChunkSizeResult, extract_func):
    values = {}
    for file_infos in result.values():
        for file_info in file_infos:
            if file_info.file_name not in values:
                values[file_info.file_name] = []
            values[file_info.file_name].append(extract_func(file_info))
    return values


PltFigure = matplotlib.figure.Figure
CalcFunc = typing.Callable[
    [typing.Any], typing.Any
]  # Подготавливает данные для построения графика
PlotFunc = typing.Callable[
    [typing.Any], typing.List[PltFigure]
]  # Строит график по подготовленным данным
OutFunc = typing.Callable[
    [PltFigure], None
]  # Обработка графика: вывод на экран, сохранение в файл
bind = functools.partial


def process_data(
    data, calc_func: CalcFunc, plot_funcs: typing.List[typing.Tuple[PlotFunc, OutFunc]]
):
    calc_result = calc_func(data) if (calc_func is not None) else data
    for plot_func, out_func in plot_funcs:
        figure = plot_func(calc_result)
        out_func(figure)
        plt.close(figure)


def save_to_file(figure: PltFigure, title: str):
    figure.tight_layout()
    path = "plots"
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    figure.savefig(f"{path}/{title}.png", dpi=300)


def binded_save(title: str):
    return functools.partial(save_to_file, title=title)


def show(figure: PltFigure):
    figure.show()
    plt.show()


def plot_values_by_chunk_size(data, extract_func, ylabel) -> PltFigure:
    fig, ax = plt.subplots(nrows=1, ncols=1)

    chunk_sizes = [int(chunk_size) / 2**10 for chunk_size in data.keys()]
    store_speeds = extract_values(data, extract_func)
    for file_name, vals in store_speeds.items():
        ax.plot(chunk_sizes, vals, label=file_name)
    ax.legend()
    ax.set_xlabel("chunk_size, KB")
    ax.set_ylabel(ylabel)
    return fig


def make_graph(json_filename: pathlib.Path):
    with open(json_filename, "r") as stat_file:
        data = json.load(stat_file)
    data = {
        chunk_size: [FileInfo(**file_info) for file_info in file_infos]
        for chunk_size, file_infos in data.items()
    }

    process_data(
        data,
        None,
        [
            (
                bind(
                    plot_values_by_chunk_size,
                    extract_func=lambda file_info: file_info.store_stats.speed / 2**20,
                    ylabel="store_speed, MB/s",
                ),
                binded_save("store_speeds"),
            ),
            (
                bind(
                    plot_values_by_chunk_size,
                    extract_func=lambda file_info: file_info.store_stats.dedup_ratio
                    * 100,
                    ylabel="dedup_ratio, %",
                ),
                binded_save("dedup_ratios"),
            ),
            (
                bind(
                    plot_values_by_chunk_size,
                    extract_func=lambda file_info: file_info.get_stats.speed / 2**20,
                    ylabel="get_speed, MB/s",
                ),
                binded_save("get_speeds"),
            ),
            (
                bind(
                    plot_values_by_chunk_size,
                    extract_func=lambda file_info: file_info.store_stats.mem_diff / 2**20,
                    ylabel="mem_diff, MB",
                ),
                binded_save("mem_diffs"),
            ),
        ],
    )
