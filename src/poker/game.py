from typing import List, Optional

class ProvablyFairHoldEm:
    """
    Represents a partially revealed, provably fair Texas Hold'em game.
    """

    def __init__(self, commitment: str, merkle_root: str,
                 initial_player_one_hand: Optional[List[str]] = None,
                 initial_player_two_hand: Optional[List[str]] = None,
                 player_one_stack: float = 1000.0,
                 player_two_stack: float = 1000.0,
                 player_one_name: str = "Alice",
                 player_two_name: str = "Bob"):
        """
        Initialize the Texas Hold 'em game with pre-committed data.
        """
        self.commitment = commitment
        self.merkle_root = merkle_root

        self.player_one_hand = initial_player_one_hand if initial_player_one_hand is not None else []
        self.player_two_hand = initial_player_two_hand if initial_player_two_hand is not None else []
        self.community_cards = []

        self.player_one_name = player_one_name
        self.player_two_name = player_two_name

        # Let's track these for demonstration (extremely simplified)
        self.current_bet = 0.0  # the current bet to call
        self.pot = 0.0
        self.player_one_stack = player_one_stack
        self.player_two_stack = player_two_stack

        self.round = 0

    def deal_flop(self, flop: List[str]) -> None:
        """
        Deal the flop cards (first three community cards).
        """
        self.community_cards.extend(flop)

    def deal_turn(self, turn_card: str) -> None:
        """
        Deal the turn card.
        """
        self.community_cards.append(turn_card)

    def deal_river(self, river_card: str) -> None:
        """
        Deal the river card.
        """
        self.community_cards.append(river_card)

    def call_player_action(self, player: str):
        """
        Player calls the current bet. 
        For demonstration, we simply match the bet and add to pot.
        """
        if player == self.player_one_name:
            needed = self.current_bet
            if self.player_one_stack >= needed:
                self.player_one_stack -= needed
                self.pot += needed
        elif player == self.player_two_name:
            needed = self.current_bet
            if self.player_two_stack >= needed:
                self.player_two_stack -= needed
                self.pot += needed

    def raise_player_action(self, player: str, amount: float):
        """
        Player raises. We update the pot, the current bet, etc.
        """
        if float(amount) <= float(self.current_bet):
            # minimal sanity check
            amount = float(self.current_bet) + 10.0

        if player == self.player_one_name:
            if self.player_one_stack >= float(amount):
                self.player_one_stack -= float(amount)
                self.pot += float(amount)
                self.current_bet = float(amount)
        elif player == self.player_two_name:
            if self.player_two_stack >= float(amount):
                self.player_two_stack -= float(amount)
                self.pot += float(amount)
                self.current_bet = float(amount)
    
    def all_in_player_action(self, player: str):
        """
        Player goes all-in. We update the pot, the current bet, etc.
        """
        if player == self.player_one_name:
            amount = self.player_one_stack
            self.player_one_stack = 0.0
            self.pot += amount
            self.current_bet = max(self.current_bet, amount)
        elif player == self.player_two_name:
            amount = self.player_two_stack
            self.player_two_stack = 0.0
            self.pot += amount
            self.current_bet = max(self.current_bet, amount)

    def fold_player_action(self, player: str) -> str:
        """
        Player folds. The other player wins the pot automatically (simple version).
        Return which player won.
        """
        if player == self.player_one_name:
            # Player Two wins
            self.player_two_stack += self.pot
            self.pot = 0.0
            return self.player_two_name
        else:
            # Player One wins
            self.player_one_stack += self.pot
            self.pot = 0.0
            return self.player_one_name
