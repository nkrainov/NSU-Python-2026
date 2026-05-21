import sys
import random
from sortedDict import SortedDict, SortedDictStats

N: int = 10_000_000



def build_keys(mode: str) -> list[int]:
    print(f"Key generation  [mode={mode}, n={N:,}]")
    keys: list[int]
    if mode == "random":
        keys = random.sample(range(N * 10), N)
        print(f"  Generated {N:,} unique random keys.")
    else:
        keys = list(range(N))
        print(f"  Generated {N:,} sequential keys (0 … {N - 1}).")
    return keys


def phase_insert(d: SortedDict[int, int], keys: list[int]) -> None:
    print("Phase 1 — INSERT")
    print(f"  Inserting {N:,} nodes...")
    step: int = N // 10
    for i, k in enumerate(keys, start=1):
        d[k] = k
        if i % step == 0:
            print(f"  {i:>{len(str(N))},} / {N:,}  ({100 * i // N:3d}%)")
    stats: SortedDictStats = d.get_stats()
    print(stats)
    d.reset_stats()
    print("  → Stats reset.")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("random", "sorted"):
        print("Usage: python analysis.py [random|sorted]")
        sys.exit(1)

    mode: str = sys.argv[1]

    keys: list[int] = build_keys(mode)

    d: SortedDict[int, int] = SortedDict[int, int]()

    phase_insert(d, keys)

    print("Done")
    print(f"  Phase completed in mode '{mode}'.")
    print()


if __name__ == "__main__":
    main()