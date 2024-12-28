"""
This module defines a Deck class that:
- Creates a standard 52-card deck.
- Uses a linear congruential generator (LCG) from `core.rng` to shuffle deterministically.
- Builds a Merkle tree over the final deck order for provable fairness.
- Provides card dealing and Merkle proof retrieval capabilities.
"""

from typing import List, Tuple
from core.rng import LCG, secret_to_seed
from core.commit_reveal import build_merkle_tree, get_merkle_root, get_merkle_proof

# Standard 52-card deck: 13 ranks in each of 4 suits
# Note: this differs from what I had in Blackjack where '10' was used instead of 'T'
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
SUITS = ['h', 'd', 'c', 's']  # Hearts, Diamonds, Clubs, Spades

def create_standard_deck() -> List[str]:
    """
    Create a standard 52-card deck in a canonical order (not shuffled).

    :return: A list of strings, each representing a card (e.g. "Ah", "Td", "Ks").
    """
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]

class Deck:
    """
    A class representing a provably fair deck of cards. The deck is shuffled deterministically
    using an LCG seeded from a secret, and a Merkle tree is built over the deck order to provide
    proofs of fairness for each revealed card.

    Attributes:
        cards (List[str]): The deck of cards after shuffling.
        merkle_tree (MerkleTools): The Merkle tree built over the deck order.
        merkle_root (str): The Merkle root hash.
        current_index (int): The index of the next card to deal.
    """

    def __init__(self, secret: bytes):
        """
        Initialize and shuffle a deck of cards, building a Merkle tree for provable fairness.

        :param secret: The secret bytes used to seed the LCG that shuffles the deck.
        """
        self.secret = secret
        self.cards = create_standard_deck()
        self._shuffle_deck()
        self.merkle_tree = build_merkle_tree(self.cards)
        self.merkle_root = get_merkle_root(self.merkle_tree)
        self.current_index = 0

    def _shuffle_deck(self):
        """
        Shuffle the deck deterministically using the LCG seeded from the secret.
        Uses a Fisher-Yates shuffle algorithm to ensure uniform permutation.
        """
        seed = secret_to_seed(self.secret)
        rng = LCG(seed)
        # Fisher-Yates shuffle
        for i in range(len(self.cards) - 1, 0, -1):
            j = int(rng.random_float() * (i + 1))
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]

    def deal_card(self) -> Tuple[str, List[dict], int]:
        """
        Deal the top card from the deck, returning the card and its Merkle proof.

        :return: A tuple (card, proof, index) where
            card is the card string,
            proof is a Merkle proof (list of dictionaries),
            index is the card's index in the deck.
        :raises IndexError: If no cards remain in the deck.
        """
        if self.current_index >= len(self.cards):
            raise IndexError("No cards left in the deck.")
        card = self.cards[self.current_index]
        proof = get_merkle_proof(self.merkle_tree, self.current_index)
        deal_index = self.current_index
        self.current_index += 1
        return card, proof, deal_index

    def get_merkle_root(self) -> str:
        """
        Get the Merkle root of the deck order.

        :return: Hex-encoded Merkle root string.
        """
        return self.merkle_root
