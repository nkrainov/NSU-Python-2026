import timeit
import tracemalloc

import bitarray

def eratosthenes_sieve_list(n):
    if n <= 1:
        return []

    isPrimeList = [True for _ in range(n)]
    res = [2]
    for i in range(3, n, 2):
        if isPrimeList[i]:
            res.append(i)
            for j in range(i, n, i):
                isPrimeList[j] = False

    return res

assert eratosthenes_sieve_list(1) == []
assert eratosthenes_sieve_list(2) == [2]
assert eratosthenes_sieve_list(12) == [2, 3, 5, 7, 11]

def eratosthenes_sieve_dict(n):
    if n <= 1:
        return []

    isPrimeDict = {i: True for i in range(2, n + 1)}
    res = [2]
    for i in range(3, n, 2):
        if isPrimeDict[i]:
            res.append(i)
            for j in range(i, n, i):
                isPrimeDict[j] = False

    return res

assert eratosthenes_sieve_dict(1) == []
assert eratosthenes_sieve_dict(2) == [2]
assert eratosthenes_sieve_dict(12) == [2, 3, 5, 7, 11]

def eratosthenes_sieve_bitarray(n):
    if n <= 1:
        return []

    isPrimeBitarray = bitarray.bitarray(n)
    isPrimeBitarray.setall(True)
    res = [2]
    for i in range(3, n, 2):
        if isPrimeBitarray[i]:
            res.append(i)
            for j in range(i, n, i):
                isPrimeBitarray[j] = False

    return res

assert eratosthenes_sieve_bitarray(1) == []
assert eratosthenes_sieve_bitarray(2) == [2]
assert eratosthenes_sieve_bitarray(12) == [2, 3, 5, 7, 11]

n = 10**6
iterations = 100

for i, func in enumerate([eratosthenes_sieve_list, eratosthenes_sieve_dict, eratosthenes_sieve_bitarray], 1):
    print(f"func:{func}")
    t = timeit.timeit(lambda: func(n), number=iterations)
    print(f"Average time: {t/iterations}")

    tracemalloc.start()
    func(n)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"memory peak: {peak}")
    print(f"current: {current}")