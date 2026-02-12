def generate_prime_numbers(n):
    def isPrime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False

        return True

    return [x for x in range(2, n+1) if isPrime(x)]

assert generate_prime_numbers(10) == [2, 3, 5, 7]