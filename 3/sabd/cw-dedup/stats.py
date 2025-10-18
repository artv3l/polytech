import datetime
import pymongo
import typing
import dedup
import dataclasses
import params


def get_collection_size(collection: pymongo.collection.Collection) -> int:
    return collection.database.command("collstats", collection.name)["size"]


def get_file_size(file) -> int:
    old_position = file.tell()
    dedup.to_end_position(file)
    size = file.tell()
    file.seek(old_position)
    return size


def get_size(obj) -> int:
    if isinstance(obj, pymongo.collection.Collection):
        return get_collection_size(obj)
    else:
        return get_file_size(obj)


@dataclasses.dataclass
class StorageStatsDiff:
    datafile_size: int
    db_size: int
    time: datetime.timedelta


@dataclasses.dataclass
class StorageStats:
    datafile_size: int
    db_size: int
    time: datetime.datetime

    def __sub__(self, other: "StorageStats") -> StorageStatsDiff:
        return self.__class__(
            *[getattr(self, f) - getattr(other, f) for f in self.__dataclass_fields__]
        )


@dataclasses.dataclass
class UserStats:
    file_size: int
    ref_file_size: int


@dataclasses.dataclass
class BaseStats:
    storage_stats_diff: StorageStatsDiff
    user_stats: UserStats
    speed: float  # Скорость выполнения операции (B/s)

    def __init__(self, storage_stats_diff: StorageStatsDiff, user_stats: UserStats):
        self.storage_stats_diff = storage_stats_diff
        self.user_stats = user_stats
        self.speed = user_stats.file_size / storage_stats_diff.time.total_seconds()


@dataclasses.dataclass
class StoreStats(BaseStats):
    dedup_ratio: float  # Процент дедупликации
    mem_diff: int  # Общее изменение памяти (B)

    def __init__(self, storage_stats_diff: StorageStatsDiff, user_stats: UserStats):
        super().__init__(storage_stats_diff, user_stats)

        self.dedup_ratio = 1 - (storage_stats_diff.datafile_size / user_stats.file_size)
        self.mem_diff = (
            storage_stats_diff.datafile_size
            + storage_stats_diff.db_size
            - user_stats.file_size
            + user_stats.ref_file_size
        )

    def __str__(self):
        return f"""Store:
    Total memory diff: {self.mem_diff / 2**20} MB
    Dedup ratio: {self.dedup_ratio}
    Stored {self.user_stats.file_size / 2**20} MB in {self.storage_stats_diff.time.total_seconds()} s, {self.speed / 2**20} MB/s"""


@dataclasses.dataclass
class GetStats(BaseStats):
    def __init__(self, storage_stats_diff: StorageStatsDiff, user_stats: UserStats):
        super().__init__(storage_stats_diff, user_stats)

    def __str__(self):
        return f"""Get:
    Get {self.user_stats.file_size / 2**20} MB in {self.storage_stats_diff.time.total_seconds()} s, {self.speed / 2**20} MB/s"""


def get_storage_stats(storage: dedup.Storage) -> StorageStats:
    return StorageStats(
        get_size(storage.datafile),
        get_size(storage.collection),
        datetime.datetime.now(),
    )


def get_user_stats(file: typing.BinaryIO, ref_file: typing.BinaryIO) -> UserStats:
    return UserStats(get_size(file), get_size(ref_file))


def store_operation_stats(
    file: typing.BinaryIO,
    chunk_size: int,
    ref_file: typing.BinaryIO,
    storage: dedup.Storage,
):
    storage_stats = get_storage_stats(storage)
    dedup.store_file(file, chunk_size, ref_file, storage)
    storage_stats = get_storage_stats(storage) - storage_stats

    print(StoreStats(storage_stats, get_user_stats(file, ref_file)))


def get_operation_stats(
    ref_file: typing.BinaryIO, out_file: typing.BinaryIO, storage: dedup.Storage
):
    storage_stats = get_storage_stats(storage)
    dedup.get_file(ref_file, params.hash_len, out_file, storage)
    storage_stats = get_storage_stats(storage) - storage_stats

    print(GetStats(storage_stats, get_user_stats(out_file, ref_file)))
