"""
Demonstrates a possible flow of a Hold'em game with two AI Agents
who each have:
 - public speech (shared publicly)
 - private monologue (hidden from the other)
We log everything in a single .txt for debugging/hilarity.
"""

import json
import os
from core.commit_reveal import generate_secret, commit_secret
from deck import Deck
from game import ProvablyFairHoldEm
from utils import PokerSolver
from personalities import persons
from dotenv import load_dotenv

from agents import LangChainPokerAgent
from conversation_log import ConversationLogger

load_dotenv()

def player_turn(game, player, solver, player_public_chat, opponent_public_chat, logger, public_dealer_chat="", player_private_chat=""):
        # Player acts
        result = player.decide_and_speak(
            hole_cards=game.player_one_hand if player.name == game.player_one_name else game.player_two_hand,
            community_cards=game.community_cards,
            opponent_message=opponent_public_chat,
            solver=solver,
            player_chips=game.player_one_stack,
            opponent_chips=game.player_two_stack,
            current_bet=game.current_bet,
            pot_amount=game.pot,
            public_dealer_chat=public_dealer_chat,
            player_private_chat=player_private_chat
        )
        logger.log(player.name, result["internal_monologue"], is_private=True)
        logger.log(player.name, result["public_message"])
        player_public_chat += "\n" + result["public_message"]
        player_private_chat += "\n" + result["internal_monologue"]

        # Execute action
        if result["action"] == "call":
            game.call_player_action(player.name)
            logger.log(f"{player.name}-action", "call")
        elif result["action"] == "raise":
            game.raise_player_action(player.name, amount=result["amount"])
            logger.log(f"{player.name}-action", f"raise to {result["amount"]}")
        elif result["action"] == "all-in":
            game.all_in_player_action(player.name)
            logger.log(f"{player.name}-action", "all-in")
        elif result["action"] == "fold":
            winner = game.fold_player_action(player.name)
            logger.log(f"{player.name}-action", "fold")
            logger.log("Dealer", f"{winner} wins the pot immediately. Game over.")
            return result, logger, player_public_chat, game, True, player_private_chat
        
        return result, logger, player_public_chat, game, False, player_private_chat

def betting_round(game, player, solver, player_public_chat, opponent_public_chat, logger, public_dealer_chat="", player_private_chat=""):
    """
    A single betting round for a player in a game of poker.
    """
    result, logger, player_public_chat, game, hand_over, player_private_chat = player_turn(
            game=game,
            player=player,
            solver=solver,
            player_public_chat=player_public_chat,
            opponent_public_chat=opponent_public_chat,
            logger=logger,
            public_dealer_chat=public_dealer_chat,
            player_private_chat=player_private_chat
    )
    return result, logger, player_public_chat, opponent_public_chat, game, hand_over, player_private_chat

def write_end_state(balances, deck_instance, game, logger, player_one_wins=None, split_pot=0.0, secret=None):
    if player_one_wins is not None:
        if player_one_wins:
            game.player_one_stack += game.pot + split_pot
            game.player_two_stack -= game.pot
        else:
            game.player_two_stack += game.pot + split_pot
            game.player_one_stack -= game.pot

    logger.log("Dealer", "Game Over! Final stacks:")
    logger.log("Dealer", f"{game.player_one_name}: {game.player_one_stack}")
    logger.log("Dealer", f"{game.player_two_name}: {game.player_two_stack}")
    logger.log("Dealer", "This game was seeded with the secret: " + secret.hex())
    current_game_index = balances[game.player_one_name][-1][0] + 1
    balances[game.player_one_name].append([current_game_index, deck_instance.merkle_root, game.player_one_stack])
    balances[game.player_two_name].append([current_game_index, deck_instance.merkle_root, game.player_two_stack])
    with open(f"./balances/balances.json", "w") as f:
        json.dump(balances, f)

def calculate_player_stats(players):
    """
    Calculate percentage wins and expected value for each player.

    Parameters:
        players (dict): Dictionary with player names as keys and a list of game records as values.

    Returns:
        dict: Dictionary with player names as keys and their stats as values.
    """
    stats = {}
    for player, games in players.items():
        if len(games) < 2:
            # Not enough data to calculate stats
            stats[player] = {"percentage_win": None, "expected_value": None}
            continue
        
        net_changes = []
        wins = 0
        
        for i in range(1, len(games)):
            prev_balance = games[i-1][2]
            current_balance = games[i][2]
            change = current_balance - prev_balance
            net_changes.append(change)
            
            if change > 0:
                wins += 1
        
        total_games = len(net_changes)
        percentage_win = (wins / total_games) * 100 if total_games > 0 else 0
        expected_value = sum(net_changes) / total_games if total_games > 0 else 0
        
        stats[player] = {
            "percentage_win": round(percentage_win, 2),
            "expected_value": round(expected_value, 2)
        }
    
    return stats

def run_game(player_one_details, player_two_details):
    # 1) Setup secrets & deck
    secret = generate_secret() 
    commitment = commit_secret(secret)
    deck_instance = Deck(secret)
    deck = deck_instance.cards

    # For demonstration:
    initial_player_one_cards = [deck[0], deck[2]]
    initial_player_two_cards = [deck[1], deck[3]]

    # Load the balances
    with open(f"./balances/balances.json", "r") as f:
        balances = json.load(f)
    print("Balances:", balances)
    # 5) Create two agents
    #    Supply your own OpenAI key in the ./env file
    openai_api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI")  
    player_one = LangChainPokerAgent(
        name=player_one_details['name'],
        personality=player_one_details["personality"],
        openai_api_key=openai_api_key,
        temperature=0.7
    )
    player_two = LangChainPokerAgent(
        name=player_two_details['name'],
        personality=player_two_details["personality"],
        openai_api_key=openai_api_key,
        temperature=0.7
    )

    # 2) Create the game
    game = ProvablyFairHoldEm(commitment, deck_instance.merkle_root,
                              initial_player_one_hand=initial_player_one_cards,
                              initial_player_two_hand=initial_player_two_cards,
                              player_one_stack=float(balances[player_one.name][-1][2]), # Get the last balance
                              player_two_stack=float(balances[player_two.name][-1][2]), # Get the last balance
                              player_one_name=player_one.name,
                              player_two_name=player_two.name)
    
    
    # 3) Setup the conversation logger
    logger = ConversationLogger(f"./conversations/{balances[player_one.name][-1][0] + 1}-{deck_instance.merkle_root}.txt")
    
    # 4) Instantiate solver
    solver = PokerSolver()

    # Basic historical game winning statistics 
    stats = calculate_player_stats(balances)
    # We keep track of the last public message from each player
    public_dealer_chat = f"""This is game number {balances[player_one.name][-1][0] + 1} and as it stands the {player_one.name} has won {stats[player_one.name]["percentage_win"]}% of their games and the {player_two.name} has won {stats[player_two.name]["percentage_win"]}% of their games."""

    logger.log("Dealer", "**GAME STARTS**")
    logger.log("Dealer", "Welcome to the game!")
    logger.log("Dealer", public_dealer_chat)
    logger.log("Dealer", f"The game's commitment is {game.commitment}")
    logger.log("Dealer", f"The deck's merkle root is {deck_instance.merkle_root}")
    logger.log("Dealer", "**HOLE CARDS DEALT**")
    logger.log("Dealer", f"{player_one.name}'s Hole Cards: {game.player_one_hand}")
    logger.log("Dealer", f"{player_two.name}'s Hole Cards: {game.player_two_hand}")

    player_one_public_chat = ""
    player_one_private_chat = ""
    player_two_public_chat = ""
    player_two_private_chat = ""

    # 6) Pre-Flop round: 
    #    Each agent "speaks" once, then we handle an action
    #    TODO: set up small blind/big blind etc. 
    #    For now, let's just assume there's a minimal current_bet of 10 to call.

    game.current_bet = 10.0
    # Player One acts first
    _, logger, player_one_public_chat, player_two_public_chat, game, hand_over, player_one_private_chat = betting_round(game, player_one, solver, player_one_public_chat, player_two_public_chat, logger, public_dealer_chat, player_one_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=False, secret=secret)
        return
    # Now Player Two acts
    _, logger, player_two_public_chat, player_one_public_chat, game, hand_over, player_two_private_chat = betting_round(game, player_two, solver, player_two_public_chat, player_one_public_chat, logger, public_dealer_chat, player_two_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=True, secret=secret)
        return

    # 7) Deal the Flop
    flop_cards = [deck[4], deck[5], deck[6]]
    game.deal_flop(flop_cards)
    logger.log("Dealer", f"**FLOP DEALT**: {flop_cards}")

    # Agents talk and act again if desired
    _, logger, player_one_public_chat, player_two_public_chat, game, hand_over, player_one_private_chat = betting_round(game, player_one, solver, player_one_public_chat, player_two_public_chat, logger, public_dealer_chat, player_one_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=False, secret=secret)
        return
    _, logger, player_two_public_chat, player_one_public_chat, game, hand_over, player_two_private_chat = betting_round(game, player_two, solver, player_two_public_chat, player_one_public_chat, logger, public_dealer_chat, player_two_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=True, secret=secret)
        return 

    # 8) Deal the Turn
    turn_card = deck[7]
    game.deal_turn(turn_card)
    logger.log("Dealer", f"**TURN DEALT**: {turn_card}")
    
    # Agents talk and act again if desired
    _, logger, player_one_public_chat, player_two_public_chat, game, hand_over, player_one_private_chat = betting_round(game, player_one, solver, player_one_public_chat, player_two_public_chat, logger, public_dealer_chat, player_one_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=False, secret=secret)
        return
    _, logger, player_two_public_chat, player_one_public_chat, game, hand_over, player_two_private_chat = betting_round(game, player_two, solver, player_two_public_chat, player_one_public_chat, logger, public_dealer_chat, player_two_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=True, secret=secret)
        return

    # 9) Deal the River
    river_card = deck[8]
    game.deal_river(river_card)
    logger.log("Dealer", f"**RIVER DEALT**: {river_card}")
    # Agents talk and act again if desired

    _, logger, player_one_public_chat, player_two_public_chat, game, hand_over, player_one_private_chat = betting_round(game, player_one, solver, player_one_public_chat, player_two_public_chat, logger, public_dealer_chat, player_one_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=False, secret=secret)
        return
    _, logger, player_two_public_chat, player_one_public_chat, game, hand_over, player_two_private_chat = betting_round(game, player_two, solver, player_two_public_chat, player_one_public_chat, logger, public_dealer_chat, player_two_private_chat)
    if hand_over:
        write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=True, secret=secret)
        return

    # 10) Evaluate final results
    p1_eval = solver.calculate_probabilities(
        hand=game.player_one_hand, 
        community_cards=game.community_cards, 
        opponent_hand=game.player_two_hand
    )

    logger.log("Dealer", f"Final probabilities: {p1_eval}")
    logger.log("Dealer", "Game Over - The Winner is ...")
    # check p1_eval and determine winner the p1_eval looks like {'win': 0.0, 'lose': 1.0, 'tie': 0.0, 'total_hands': 1} in the context of player one
    split_pot = 0.0
    player_one_wins = None
    player_two_wins = None
    if p1_eval["win"] > 0.95:
        logger.log("Dealer", f"{player_one.name}!")
        player_one_wins = True
    elif p1_eval["win"] < 0.05:
        logger.log("Dealer", f"{player_two.name}!")
        player_one_wins = False
    else:
        logger.log("Dealer", "It's a tie!")
        split_pot = game.pot / 2

    # 11) Distribute the pot
    if player_one_wins is not None:
        if player_one_wins:
            game.player_one_stack += game.pot + split_pot
            game.player_two_stack -= game.pot
        else:
            game.player_two_stack += game.pot + split_pot
            game.player_one_stack -= game.pot

    # Append the new balances file with index of the game
    write_end_state(balances, deck_instance, game, logger=logger, player_one_wins=player_one_wins, split_pot=split_pot, secret=secret)

    logger.log("Dealer", "Thanks for playing, see you next time!")

if __name__ == "__main__":
    player_one_details = {'name': "Jonny Meta", 'personality': persons["Jonny Meta"]["personality"]}
    player_two_details = { 'name': "Professor Paradox", 'personality': persons["Professor Paradox"]["personality"] }
    run_game(player_one_details=player_one_details, player_two_details=player_two_details)
