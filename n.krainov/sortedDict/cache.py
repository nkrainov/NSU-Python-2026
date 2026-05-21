import sys
import random
from typing import Union
from sortedDict import SortedDict


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python cache.py [sorted|random]")
        sys.exit(1)

    mode: str = sys.argv[1].lower()
    if mode not in ("sorted", "random"):
        print("Mode must be 'sorted' or 'random'")
        sys.exit(1)

    N: int = 10_000_000
    cache_size: int = 1024

    print(f"Starting {N} insertions, mode = {mode}, cache size = {cache_size}")

    tree: SortedDict[int, int] = SortedDict[int, int](cache_size=cache_size)

    keys: Union[range, list[int]]
    if mode == "sorted":
        keys = range(N)
    else:
        keys = list(range(N))
        random.shuffle(keys)

    i: int
    k: int
    for i, k in enumerate(keys):
        tree[k] = k
        if (i + 1) % 1_000_000 == 0:
            print(f"Inserted {i+1} elements...")

    hits: int
    misses: int
    hits, misses = tree.get_cache_stats()
    total_accesses: int = hits + misses
    hit_rate: float = hits / total_accesses * 100 if total_accesses else 0.0

    print("\n=== Cache statistics ===")
    print(f"Hits:   {hits}")
    print(f"Misses: {misses}")
    print(f"Total accesses: {total_accesses}")
    print(f"Hit rate: {hit_rate:.2f}%")
    print(f"Miss rate: {100 - hit_rate:.2f}%")


if __name__ == "__main__":
    main()