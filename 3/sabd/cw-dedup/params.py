import hashlib
import dataclasses

insert_cache_size = 100
get_cache_size = 50

hash_func = hashlib.md5

@dataclasses.dataclass(frozen=True)
class DbNames:
    hash_val: str = "hash_val"
    ref_count: str = "ref_count"
    position: str = "position"
    size: str = "size"
db_names = DbNames()
