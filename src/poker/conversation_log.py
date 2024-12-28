class ConversationLogger:
    """
    Logs all conversation lines (public and private) to a text file.
    The private lines of one agent remain invisible to the other agent,
    but everything is stored in the same log file for debugging/hilarity.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        # Clear the file when we start
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("** POKER GAME LOG **\n\n")

    def log(self, speaker: str, message: str, is_private: bool = False):
        """
        :param speaker: e.g. "Alice" or "Bob" or "Dealer"
        :param message: the content
        :param is_private: if True, indicates this is an internal monologue
        """
        with open(self.file_path, "a", encoding="utf-8") as f:
            if is_private:
                f.write(f"{speaker}-internal-monologue: {message}\n")
            else:
                f.write(f"{speaker}: {message}\n")
        # Optional: print to stdout if you want to see it live
        print(f"[{'PRIVATE' if is_private else 'PUBLIC'}] {speaker}: {message}")
