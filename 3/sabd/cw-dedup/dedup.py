import typing
import pymongo
import pydantic
import hashlib
import os

Chunk = bytearray
Hash = bytes
Position = int


class Ref(pydantic.BaseModel):
    hash_val: Hash
    position: Position
    ref_count: int
    size: int


def calc_hash(chunk: Chunk) -> Hash:
    return hashlib.md5(chunk).digest()


def to_end_position(datafile: typing.BinaryIO) -> Position:
    return datafile.seek(0, os.SEEK_END)


def new_datafile_chunk(chunk: Chunk, datafile: typing.BinaryIO, position: Position):
    datafile.seek(position)
    datafile.write(chunk)


def insert_chunk(
    collection: pymongo.collection.Collection, datafile: typing.BinaryIO, chunk: Chunk
) -> Hash:
    hash_val: Hash = calc_hash(chunk)

    # Используется только при добавлении нового элемента
    position: Position = to_end_position(datafile)
    new_ref = Ref(
        hash_val=hash_val,
        datafile="data.bin",
        position=position,
        ref_count=1,
        size=len(chunk),
    )

    # Нужно удалить ref_count, т.к. он будет создан в '$inc'
    new_ref_dump = new_ref.model_dump()
    new_ref_dump.pop("ref_count")

    update_result = collection.update_one(
        {"hash": hash_val},
        {"$inc": {"ref_count": 1}, "$setOnInsert": new_ref_dump},
        upsert=True,
    )

    # Такого хэша не было - нужно добавить чанк в хранилище данных
    if update_result.upserted_id:
        new_datafile_chunk(chunk, datafile, position)

    return hash_val


def store_file(
    file: typing.BinaryIO,
    chunk_size: int,
    ref_file: typing.BinaryIO,
    collection: pymongo.collection.Collection,
    datafile: typing.BinaryIO,
):
    while True:
        chunk: Chunk = file.read(chunk_size)
        if not chunk:
            break

        hash_val = insert_chunk(collection, datafile, chunk)
        ref_file.write(hash_val)


def extract_file(
    ref_file: typing.BinaryIO,
    hash_len: int,
    out_file: typing.BinaryIO,
    collection: pymongo.collection.Collection,
    datafile: typing.BinaryIO,
):
    while True:
        hash_val: Hash = ref_file.read(hash_len)
        if not hash_val:
            break

        found = collection.find_one({"hash": hash_val})
        if not found:
            raise RuntimeError("Hash not found")

        ref = Ref(**found)
        datafile.seek(ref.position)
        out_file.write(datafile.read(ref.size))
