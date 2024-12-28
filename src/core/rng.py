import hashlib
import math

class LCG:
    """
    Linear Congruential Generator for pseudo-random numbers.

    This is not cryptographically secure, but is used here
    as a transparent, deterministic RNG seeded by a secret.

    Attributes:
        a, c, m: Standard LCG parameters.
        state: Current internal state.
    """
    def __init__(self, seed: int, a=1664525, c=1013904223, m=2**32):
        self.a = a
        self.c = c
        self.m = m
        self.state = seed % m
        self.box_muller_spare = None  # For storing the spare normal value

    def next_random(self) -> int:
        """
        Generate the next pseudo-random integer in [0, m-1].

        :return: Pseudo-random integer.
        """
        self.state = (self.a * self.state + self.c) % self.m
        return self.state
    
    def random_float(self) -> float:
        """
        Generate a pseudo-random float in [0, 1).

        :return: Pseudo-random float.
        """
        return self.next_random() / self.m

    def random_normal(self, mu=0.0, sigma=1.0) -> float:
        """
        Generate a normally distributed random number using the Box-Muller transform.

        :param mu: Mean of the distribution.
        :param sigma: Standard deviation of the distribution.
        :return: Normally distributed float.
        """
        if self.box_muller_spare is not None:
            normal = self.box_muller_spare
            self.box_muller_spare = None
            return normal * sigma + mu

        u1 = self.random_float()
        u2 = self.random_float()

        # Avoid taking log(0)
        u1 = max(u1, 1e-10)

        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        z1 = math.sqrt(-2.0 * math.log(u1)) * math.sin(2.0 * math.pi * u2)

        self.box_muller_spare = z1
        return z0 * sigma + mu

def secret_to_seed(secret: bytes) -> int:
    """
    Convert a secret to an integer seed by hashing it.

    :param secret: The secret bytes.
    :return: Integer seed derived from the secret.
    """
    seed_hash = hashlib.sha256(secret).digest()
    return int.from_bytes(seed_hash, 'big')
