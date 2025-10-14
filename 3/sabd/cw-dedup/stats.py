import datetime
import pymongo
import functools
import typing
import dedup

bind = functools.partial


def get_func_name(f):
    if isinstance(f, bind):
        return f.func.__name__
    else:
        return f.__name__


def get_exec_time(func):
    start_time = datetime.datetime.now()
    func()
    return datetime.datetime.now() - start_time


def print_exec_time(func):
    print(f"'{get_func_name(func)}' exec time: {get_exec_time(func)}")


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


def store_operation_stats(
    file: typing.BinaryIO,
    chunk_size: int,
    ref_file: typing.BinaryIO,
    storage: dedup.Storage,
):
    init_datafile_size = get_size(storage.datafile)
    init_collection_size = get_size(storage.collection)

    exec_time = get_exec_time(
        bind(dedup.store_file, file, chunk_size, ref_file, storage)
    )

    diff_datafile_size = get_size(storage.datafile) - init_datafile_size
    diff_collection_size = get_size(storage.collection) - init_collection_size

    print(
        f"Total memory diff: {diff_datafile_size + diff_collection_size - get_size(file) + get_size(ref_file)}"
    )
    file_size_KB = get_size(file) / 1024
    print(
        f"Stored: {file_size_KB} KB in {exec_time}, {file_size_KB / exec_time.total_seconds()} KB/s"
    )
