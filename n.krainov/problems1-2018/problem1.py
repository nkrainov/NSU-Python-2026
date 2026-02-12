def factorize(n):
    if n < 2:
        return []

    result = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            k = 0
            while n % d == 0:
                n //= d
                k += 1
            result.append([d, k])
        d += 1 if d == 2 else 2

    if n > 1:
        result.append([n, 1])
    return result

assert factorize(12) == [[2, 2], [3, 1]]
assert factorize(60) == [[2, 2], [3, 1], [5, 1]]
assert factorize(97) == [[97, 1]]
assert factorize(1) == []