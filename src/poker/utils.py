import subprocess
from typing import List, Dict, Optional
from pathlib import Path
import os
import re

class PokerSolverError(Exception):
    """Custom exception for poker solver related errors"""
    pass

class PokerSolver:
    def __init__(self, solver_path: Optional[str] = None):
        """
        Initialize the poker solver integration.
        
        Args:
            solver_path: Path to the poker-solver executable. If None, will try to build from source.
        """
        self.solver_path = solver_path
        if not solver_path:
            self._build_solver()
        else:
            self.solver_path = Path(solver_path)
            if not self.solver_path.exists():
                raise PokerSolverError(f"Poker solver not found at {solver_path}")

    def _build_solver(self) -> None:
        """Build the Rust poker solver from source"""
        # Clone the repository if it doesn't exist
        if not Path("poker-solver").exists():
            result = subprocess.run(
                ["git", "clone", "https://github.com/hucancode/poker-solver.git"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise PokerSolverError(f"Failed to clone repository: {result.stderr}")

        # Build the project
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd="poker-solver",
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise PokerSolverError(f"Failed to build poker-solver: {result.stderr}")

        # Set the solver path to the built executable
        self.solver_path = Path("poker-solver/target/release/poker-solver")
        if os.name == "nt":  # Windows
            self.solver_path = self.solver_path.with_suffix(".exe")

    def _format_cards(self, cards: List[str]) -> str:
        """Convert card list to space-separated string format"""
        return "".join(cards)

    def calculate_probabilities(
        self,
        hand: List[str],
        community_cards: List[str],
        opponent_hand: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Calculate winning probabilities using the poker solver.
        
        Args:
            hand: List of cards in your hand (e.g., ["As", "Ad"])
            community_cards: List of community cards (e.g., ["2s", "3s", "4d"])
            opponent_hand: Optional list of opponent's cards
            
        Returns:
            Dictionary containing win/tie/lose probabilities as decimals between 0 and 1
            {
                "win": float,    # Winning probability
                "lose": float,   # Losing probability
                "tie": float,    # Tie probability
                "total_hands": int  # Total number of hands evaluated
            }
        """
        # Input validation
        if not hand or len(hand) != 2:
            raise ValueError("Hand must contain exactly 2 cards")
        if not community_cards:
            raise ValueError("Community cards cannot be empty")

        # Prepare command
        cmd = [str(self.solver_path)]
        cmd.extend([self._format_cards(community_cards)])
        cmd.extend([self._format_cards(hand)])
        if opponent_hand:
            cmd.extend([self._format_cards(opponent_hand)])
        # Run the solver
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise PokerSolverError(f"Poker solver failed: {e.stderr}")

        # Parse the output using regular expressions
        output = result.stdout

        if re.search(r'Invalid game!', output):
            raise PokerSolverError("Invalid game state provided to solver")

        # Extract the raw counts and percentage
        win_count = int(re.search(r'Win:\s+(\d+)', output).group(1))
        lose_count = int(re.search(r'Lose:\s+(\d+)', output).group(1))
        tie_count = int(re.search(r'Tie:\s+(\d+)', output).group(1))
        
        # Calculate total hands analyzed
        total_hands = win_count + lose_count + tie_count
        
        # Calculate probabilities as decimals
        probabilities = {
            "win": win_count / total_hands,
            "lose": lose_count / total_hands,
            "tie": tie_count / total_hands,
            "total_hands": total_hands
        }
        
        return probabilities

def gto_strategy(hand: List[str], community_cards: List[str]) -> str:
    """
    Invoke a GTO (Game Theory Optimal) strategy for Texas Hold 'em.
    
    Args:
        hand: The player's hand (list of cards)
        community_cards: The community cards on the table (list of cards)
        
    Returns:
        Dictionary containing win/tie/lose probabilities
    """
    solver = PokerSolver()
    return solver.calculate_probabilities(hand, community_cards)