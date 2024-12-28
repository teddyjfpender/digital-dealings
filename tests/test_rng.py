"""
Unit tests for the MissionUncrossableGame class and related functionality.
"""

import time
import unittest
from core.commit_reveal import build_merkle_tree, generate_secret, commit_secret, get_merkle_root, verify_normal_sequence, verify_normal_sequence_with_merkle, verify_secret
from core.rng import LCG, secret_to_seed

class TestRNGSequence(unittest.TestCase):
    def setUp(self):
        """
        Set up a common game instance for testing.
        """
        self.secret = generate_secret()
        self.commitment = commit_secret(self.secret)
        seed = secret_to_seed(self.secret)
        self.lcg = LCG(seed)

    def test_commit_reveal_flow(self):
        """
        Test the commit-reveal process.
        """
        self.assertTrue(verify_secret(self.secret, self.commitment))
        # Modify the secret and ensure verification fails
        modified_secret = bytearray(self.secret)
        modified_secret[0] ^= 0xFF  # Flip first byte
        self.assertFalse(verify_secret(bytes(modified_secret), self.commitment))

    def test_sequence_verifier(self):
        """
        Test the sequence verifier with a known sequence.
        """
        num_samples = 1000000
        mu = 1.0
        sigma = 0.2
        generated_sequence = [self.lcg.random_normal(mu=mu, sigma=sigma) for _ in range(num_samples)]

        start_time = time.time()
        is_valid = verify_normal_sequence(self.secret, self.commitment, generated_sequence, mu=mu, sigma=sigma)
        end_time = time.time()
        verification_time = end_time - start_time
        print(f"Time taken for verify_normal_sequence: {verification_time:.6f} seconds")
        self.assertTrue(is_valid)

        # Modify the secret and ensure verification fails
        modified_secret = bytearray(self.secret)
        modified_secret[0] ^= 0xFF
        self.assertFalse(verify_normal_sequence(bytes(modified_secret), self.commitment, generated_sequence, mu=mu, sigma=sigma))

    def test_sequence_verifier_merkle(self):
        """
        Test the sequence verifier with a known sequence and Merkle tree.
        """
        num_samples = 1000000
        mu = 1.0
        sigma = 0.2
        generated_sequence = [self.lcg.random_normal(mu=mu, sigma=sigma) for _ in range(num_samples)]
        
        mt = build_merkle_tree(generated_sequence)
        merkle_root = get_merkle_root(mt)

        # Step 4: Verify specific elements using Merkle proofs
        # Let's verify the first 5 elements
        indices_to_verify = [0, 1, 2, 3, 4]
        sequence_to_verify = [generated_sequence[i] for i in indices_to_verify]
        proofs = [mt.get_proof(i) for i in indices_to_verify]

        start_time = time.time()
        is_valid = verify_normal_sequence_with_merkle(
            secret=self.secret,
            commitment=self.commitment,
            merkle_root=merkle_root,
            sequence=sequence_to_verify,
            proofs=proofs,
            indices=indices_to_verify,
            mu=mu,
            sigma=sigma,
            tolerance=1e-6
        )
        end_time = time.time()
        verification_time = end_time - start_time
        print(f"Time taken for verify_normal_sequence_with_merkle: {verification_time:.6f} seconds")
        self.assertTrue(is_valid)

        # Step 5: Attempt verification with an altered element
        altered_sequence = sequence_to_verify.copy()
        altered_sequence[0] += 0.1  # Introduce a small change
        is_valid_altered = verify_normal_sequence_with_merkle(
            secret=self.secret,
            commitment=self.commitment,
            merkle_root=merkle_root,
            sequence=altered_sequence,
            proofs=proofs,
            indices=indices_to_verify,
            mu=mu,
            sigma=sigma,
            tolerance=1e-6
        )
        self.assertFalse(is_valid_altered)



if __name__ == '__main__':
    unittest.main()