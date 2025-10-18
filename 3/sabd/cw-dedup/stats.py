import datetime
import pymongo
import typing
import dedup
import params
import pathlib
import pydantic
import json


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
    Total memory diff: {self.mem_diff / 2**20} MB
    Dedup ratio: {self.dedup_ratio}
    Stored {self.user_stats.file_size / 2**20} MB in {self.storage_stats_diff.time_seconds} s, {self.speed / 2**20} MB/s"""


class GetStats(BaseStats):
    def __str__(self):
        return f"""Get:
    Get {self.user_stats.file_size / 2**20} MB in {self.storage_stats_diff.time_seconds} s, {self.speed / 2**20} MB/s"""


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


class CalcChunkSizeParams:
    begin_part: float = 0.05 / 100
    end_part: float = 0.5 / 100
    count: int = 20


class CalcChunkSizeResult(pydantic.BaseModel):
    chunk_size: int
    file_size: int
    store_stats: StoreStats
    get_stats: GetStats


def fmt_stat(filename: pathlib.Path) -> pathlib.Path:
    return filename.with_name(filename.name + ".json")


def graphs(
    storage: dedup.Storage,
    files: typing.List[pathlib.Path],
    calc_params: CalcChunkSizeParams,
):
    for file in files:
        if file.is_file():
            file_size = get_size(file)
            if file_size == 0:
                continue

            file_name = file.relative_to(pathlib.Path.cwd())

            storage.clean()

            beg = int(file_size * calc_params.begin_part)
            end = int(file_size * calc_params.end_part)
            step = int((end - beg) / calc_params.count)

            result = []

            for chunk_size in range(beg, end, step):
                ref_filepath = params.fmt_ref(file_name)
                out_filepath = params.fmt_deref(file_name)
                with (
                    open(file_name, "rb") as file_s,
                    open(ref_filepath, "w+b") as ref_file,
                    open(out_filepath, "wb") as out_file,
                ):
                    store_stats = store_operation_stats(
                        file_s, chunk_size, ref_file, storage
                    )
                    get_stats = get_operation_stats(ref_file, out_file, storage)

                    result.append(
                        CalcChunkSizeResult(
                            chunk_size=chunk_size,
                            file_size=file_size,
                            store_stats=store_stats,
                            get_stats=get_stats,
                        )
                    )
                ref_filepath.unlink()
                out_filepath.unlink()

            result_json = [res.model_dump() for res in result]
            with open(fmt_stat(file_name), "w") as stat_file:
                json.dump(result_json, stat_file, indent=4)
