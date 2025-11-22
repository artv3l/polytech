from dataclasses import dataclass

@dataclass(frozen=True)
class Names:
    coll_analyzes: str = "analyzes"
    coll_results: str = "results"

names = Names()
