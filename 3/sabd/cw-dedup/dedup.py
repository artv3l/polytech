import typing
import pymongo
import pydantic
import hashlib
import os

Chunk = bytearray
Hash = bytes
Position = int
Hashes = typing.List[Hash]


def _calc_hash(chunk: Chunk):
    return hashlib.md5(chunk)


def calc_hash(chunk: Chunk) -> Hash:
    return _calc_hash(chunk).digest()


def get_hash_size() -> int:
    return _calc_hash(b"").digest_size


def to_end_position(datafile: typing.BinaryIO) -> Position:
    return datafile.seek(0, os.SEEK_END)


def new_datafile_chunk(chunk: Chunk, datafile: typing.BinaryIO, position: Position):
    datafile.seek(position)
    datafile.write(chunk)


class Ref(pydantic.BaseModel):
    hash_val: Hash
    position: Position
    ref_count: int
    size: int


class Storage:
    def __init__(
        self, url: str, db_name: str, collection_name: str, datafile_name: str
    ):
        self.url = url
        self.db_name = db_name
        self.collection_name = collection_name
        self.datafile_name = datafile_name
        self.chunk_cache = []

    def __enter__(self):
        self.client = pymongo.MongoClient(self.url)
        self.collection = self.client[self.db_name][self.collection_name]
        self.collection.create_index("hash_val", unique=True)
        self.datafile = open(self.datafile_name, "a+b")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.close()
        self.datafile.close()

    def flush(self) -> typing.Optional[Hashes]:
        hashes = [calc_hash(chunk) for chunk in self.chunk_cache]

        operations = []
        for hash_val, chunk_len in zip(
            hashes, [len(chunk) for chunk in self.chunk_cache]
        ):
            new_ref = Ref(hash_val=hash_val, position=0, ref_count=0, size=chunk_len)
            operations.append(
                pymongo.UpdateOne(
                    {"hash_val": hash_val},
                    {"$setOnInsert": new_ref.model_dump()},
                    upsert=True,
                )
            )
        result = self.collection.bulk_write(operations, ordered=False)

        operations = []
        for index, chunk in enumerate(self.chunk_cache):
            oper = {"$inc": {"ref_count": 1}}
            if index in result.upserted_ids:
                position: Position = to_end_position(self.datafile)
                new_datafile_chunk(chunk, self.datafile, position)
                oper["$set"] = {"position": position}
            operations.append(pymongo.UpdateOne({"hash_val": hashes[index]}, oper))
        self.collection.bulk_write(operations, ordered=False)

        self.chunk_cache = []
        return hashes

    def insert_chunk(self, chunk: Chunk) -> typing.Optional[Hashes]:
        self.chunk_cache.append(chunk)
        if len(self.chunk_cache) >= 100:
            return self.flush()
        return None


def store_file(
    file: typing.BinaryIO,
    chunk_size: int,
    ref_file: typing.BinaryIO,
    storage: Storage,
):
    while True:
        chunk: Chunk = file.read(chunk_size)
        if not chunk:
            break
        hashes = storage.insert_chunk(chunk)
        if hashes:
            ref_file.write(b"".join(hashes))
    hashes = storage.flush()
    if hashes:
        ref_file.write(b"".join(hashes))


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

        found = collection.find_one({"hash_val": hash_val})
        if not found:
            raise RuntimeError("Hash not found")

        ref = Ref(**found)
        datafile.seek(ref.position)
        out_file.write(datafile.read(ref.size))
