import hashlib
import dataclasses
import pathlib

chunk_size = 1024
insert_cache_size = 100
get_cache_size = 50

hash_func = hashlib.md5
hash_len = hash_func(b"").digest_size


@dataclasses.dataclass(frozen=True)
class DbNames:
    hash_val: str = "hash_val"
    ref_count: str = "ref_count"
    position: str = "position"
    size: str = "size"
db_names = DbNames()


def fmt_ref(filename: pathlib.Path) -> pathlib.Path:
    return filename.with_name(filename + ".ref")
def fmt_deref(filename: pathlib.Path) -> pathlib.Path:
    return filename.with_name(filename.stem + "_deref" + filename.suffix)
