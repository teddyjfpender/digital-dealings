import os
from typing import Dict, Any

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain


class LangChainPokerAgent:
    """
    A simple poker agent that uses two separate LLM calls:
    1) One for internal monologue (hidden thoughts).
    2) One for public message to the opponent.
    """

    def __init__(self, 
                 name: str,
                 personality: str,
                 openai_api_key: str,
                 temperature: float = 0.7):
        """
        :param name: The agent's name (e.g., 'Alice', 'Bob').
        :param personality: A short descriptor of the agent's personality/strategy.
        :param openai_api_key: Your OpenAI API key to call the LLM.
        :param temperature: The creativity parameter for the LLM.
        """
        self.name = name
        self.personality = personality
        # In a real app, you might store/pull secrets from a vault, not in code.
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # 1) Internal monologue LLM
        self._internal_prompt = ChatPromptTemplate.from_template(
            """You are {name}, playing a game of poker.

            Your history with the opponent so far has been: {public_dealer_chat}.
            
            So far your internal monologue throughout the game has been: {player_private_chat}.
            
            You have the following hole cards: {hole_cards}.
                The current table state of the game is as follows:
                - Your chip count: {player_chips}
                - Opponent's chip count: {opponent_chips}
                - Current bet to call: {current_bet}
                - Current pot amount: {pot_amount}
                
                Your Game Theory Optimal (GTO) probabilities from the solver are are: {gto_result}.
                Your personality/strategy: {personality}.
                The community cards so far are: {community_cards}.
                The opponent's last public message was: {opponent_message}.

                In your hidden internal monologue (NOT visible to the opponent):
                - Reason about whether you think the opponent is bluffing or strong.
                - Decide your best move (call, raise, fold, or go all-in).
                - Keep it concise but elaborate enough to demonstrate your reasoning.

                OUTPUT:
                (1) Your hidden thoughts
                (2) A final single word for your action, e.g. "call" or "raise" or "fold" or "all-in"
                (3) If you want to raise, specify the amount, e.g. "raise 100"
                """
        )
        self._internal_chain = LLMChain(
            prompt=self._internal_prompt,
            llm=ChatOpenAI(model="gpt-4o", temperature=temperature),
        )

        # 2) Public speech LLM
        self._public_prompt = ChatPromptTemplate.from_template(
            """You are {name}, playing poker. Your personality/strategy: {personality}.
            Your Game Theory Optimal (GTO) probabilities from the solver are: {gto_result}.
            The community cards so far are: {community_cards}.
            The opponent's last public message was: {opponent_message}.

            Your internal monolgue on this situation was: {hidden_thoughts}

            Please produce a short sentence to say publicly. (Try to maintain your persona.)

            OUTPUT:
            Your public message:
            """
        )
        self._public_chain = LLMChain(
            prompt=self._public_prompt,
            llm=ChatOpenAI(temperature=temperature),
        )

    def decide_and_speak(
        self, 
        hole_cards: list,
        community_cards: list,
        opponent_message: str,
        solver: Any,
        player_chips: float,
        opponent_chips: float,
        current_bet: float,
        pot_amount: float,
        public_dealer_chat: str,
        player_private_chat: str
    ) -> Dict[str, Any]:
        """
        Calls two LLMs:
        1) The internal chain -> returns hidden thoughts + action
        2) The public chain -> returns public message

        :return: A dict with keys: 'internal_monologue', 'action', 'public_message'
        """

        # Compute GTO probabilities
        gto_result = solver.calculate_probabilities(hand=hole_cards, community_cards=community_cards) if len(community_cards) > 0 else "You're pre-flop so no GTO data yet, go with your gut."

        # 1) Internal monologue
        internal_result = self._internal_chain.run(
            name=self.name,
            personality=self.personality,
            hole_cards=", ".join(hole_cards),
            community_cards=", ".join(community_cards) if len(community_cards) > 0 else "You're pre-flop.",
            gto_result=gto_result,
            opponent_message=opponent_message,
            player_chips=player_chips,
            opponent_chips=opponent_chips,
            current_bet=current_bet,
            pot_amount=pot_amount,
            public_dealer_chat=public_dealer_chat,
            player_private_chat=player_private_chat
        )
        # We expect the LLM to produce something like:
        # "My hidden thoughts ... \ncall"
        # We'll split out the last line as the action:
        lines = internal_result.strip().split("\n")
        hidden_thoughts = "\n".join(lines[:-1]).strip()
        # The final line is the action (call/raise/fold):
        final_line = lines[-1].lower().strip()
        action = "call"  # default
        amount = ""
        if "raise" in final_line:
            action = "raise"
            amount = final_line.split(" ")[-1]
        elif "fold" in final_line:
            action = "fold"
        elif "call" in final_line:
            action = "call"
        elif "all-in" in final_line:
            action = "all-in"

        # 2) Public speech
        public_result = self._public_chain.run(
            name=self.name,
            personality=self.personality,
            community_cards=", ".join(community_cards),
            opponent_message=opponent_message,
            gto_result=gto_result,
            hidden_thoughts=hidden_thoughts,
        )
        public_message = public_result.strip()

        return {
            "internal_monologue": hidden_thoughts,
            "action": action,
            "amount": amount,
            "public_message": public_message
        }
