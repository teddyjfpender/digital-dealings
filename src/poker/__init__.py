"""
The blackjack module provides a provably fair implementation of a blackjack game,
using commit-reveal, deterministic RNG, and Merkle proofs from the `core` library.

It includes:
- A Deck class for managing a deck of cards.
- A ProvablyFairBlackjack class for setting up and running a blackjack game.

Players can verify fairness by:
1. Checking the secret commitment at the start.
2. Observing each dealt card along with its Merkle proof.
3. At the end of the game, the secret is revealed.
4. Using the secret to recreate the deck order and verify that it matches all revealed cards and their proofs.
"""
