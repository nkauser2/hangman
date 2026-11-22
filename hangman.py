"""Hangman - a low-stress spelling practice game.

Run from the terminal with:  python hangman.py

Words are read from word.txt (same folder). Each line holds a word, a comma,
and the word's category, for example:  apple,fruit
"""

import random
import sys
from pathlib import Path

MAX_MISSES = 5
FIRST_HINT_AT = 2   # misses before the first-letter hint appears
SECOND_HINT_AT = 4  # misses before the category hint appears

WORD_FILE = Path(__file__).with_name("word.txt")

# Result codes returned by Game.guess()
INVALID = "invalid"
ALREADY_GUESSED = "already_guessed"
CORRECT = "correct"
WRONG = "wrong"

# One drawing per miss count (0..MAX_MISSES). The last one is the full figure.
HANGMAN_STAGES = [
    # 0 misses
    """
  +---+
  |   |
      |
      |
      |
      |
=========""",
    # 1 miss: head
    """
  +---+
  |   |
  O   |
      |
      |
      |
=========""",
    # 2 misses: body
    """
  +---+
  |   |
  O   |
  |   |
      |
      |
=========""",
    # 3 misses: arms
    """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
=========""",
    # 4 misses: left leg
    """
  +---+
  |   |
  O   |
 /|\\  |
 /    |
      |
=========""",
    # 5 misses: right leg (complete)
    """
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
=========""",
]


def parse_line(line):
    """Split one word-file line into (word, category).

    Returns None for blank lines. Raises ValueError for a malformed line.
    """
    line = line.strip()
    if not line:
        return None
    if "," not in line:
        raise ValueError("missing comma between word and category")
    word, category = line.split(",", 1)
    word = word.strip().lower()
    category = category.strip()
    if not word or not category:
        raise ValueError("word and category must both be filled in")
    if not any(ch.isalpha() for ch in word):
        raise ValueError("word must contain at least one letter")
    return word, category


def skip_warning(filename, number, text, reason):
    """The exact warning shown to the player for a skipped word-file line."""
    return f"Warning: skipped line {number} of {filename} ({reason}): {text!r}"


def load_words(path=WORD_FILE, warn=print):
    """Read the word file and return a list of (word, category) tuples.

    Blank lines are skipped silently. Bad lines are skipped, and `warn` is
    called with a warning that gives the line number and the line's text.
    Raises ValueError only if no usable words are left.
    """
    entries = []
    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f, start=1):
            text = line.rstrip("\r\n")
            try:
                entry = parse_line(text)
            except ValueError as err:
                warn(skip_warning(Path(path).name, number, text, err))
                continue
            if entry is not None:
                entries.append(entry)
    if not entries:
        raise ValueError(f"{Path(path).name} has no usable words")
    return entries


class Game:
    """The state and rules of a single round of hangman."""

    def __init__(self, word, category, max_misses=MAX_MISSES):
        self.word = word.lower()
        self.category = category
        self.max_misses = max_misses
        self.guessed = []  # every letter guessed, in order
        self.misses = 0

    @staticmethod
    def normalize(raw):
        """Return the guess as a single lowercase letter, or None if invalid."""
        if raw is None:
            return None
        text = raw.strip().lower()
        if len(text) == 1 and "a" <= text <= "z":
            return text
        return None

    def guess(self, raw):
        """Apply one guess and return INVALID, ALREADY_GUESSED, CORRECT or WRONG.

        Invalid input and repeated letters do not count as a miss.
        """
        if self.is_over():
            raise RuntimeError("the game is already over")
        letter = self.normalize(raw)
        if letter is None:
            return INVALID
        if letter in self.guessed:
            return ALREADY_GUESSED
        self.guessed.append(letter)
        if letter in self.word:
            return CORRECT
        self.misses += 1
        return WRONG

    def masked_word(self):
        """The word with unguessed letters shown as underscores."""
        return " ".join(
            ch if (not ch.isalpha() or ch in self.guessed) else "_"
            for ch in self.word
        )

    def hints(self):
        """Hints unlocked so far, based on the number of misses."""
        found = []
        if self.misses >= FIRST_HINT_AT:
            found.append(f"The word starts with '{self.word[0].upper()}'.")
        if self.misses >= SECOND_HINT_AT:
            found.append(f"Category: {self.category}")
        return found

    def is_won(self):
        return all(ch in self.guessed for ch in self.word if ch.isalpha())

    def is_lost(self):
        return self.misses >= self.max_misses and not self.is_won()

    def is_over(self):
        return self.is_won() or self.is_lost()

    def figure(self):
        return HANGMAN_STAGES[min(self.misses, len(HANGMAN_STAGES) - 1)]


def render(game):
    """Build the full board text shown to the player each turn."""
    lines = [
        game.figure(),
        "",
        f"Word:    {game.masked_word()}",
        f"Guessed: {', '.join(game.guessed) if game.guessed else '(none yet)'}",
        f"Misses:  {game.misses}/{game.max_misses}",
    ]
    for hint in game.hints():
        lines.append(f"Hint:    {hint}")
    return "\n".join(lines)


def play(game, read=None, write=print):
    """Run one round. `read`/`write` can be swapped out for testing."""
    if read is None:
        read = input
    write("Welcome to Hangman! Guess the word one letter at a time.")
    while not game.is_over():
        write(render(game))
        result = game.guess(read("\nGuess a letter: "))
        if result == INVALID:
            write("Please type a single letter (a-z).")
        elif result == ALREADY_GUESSED:
            write("Already guessed! Try a different letter.")
        elif result == CORRECT:
            write("Nice, that letter is in the word!")
        else:
            write("Sorry, that letter is not in the word.")
    write(render(game))
    if game.is_won():
        write(f"\nCongratulations! You spelled '{game.word}' correctly!")
    else:
        write(f"\nThe word was '{game.word}'. Try again next time!")
    return game.is_won()


def main(path=WORD_FILE):
    try:
        words = load_words(path)
    except FileNotFoundError:
        print(f"Could not find {Path(path).name}. Put it next to hangman.py.")
        return 1
    except ValueError as err:
        print(f"Problem reading the word list: {err}")
        return 1
    word, category = random.choice(words)
    try:
        play(Game(word, category))
    except (KeyboardInterrupt, EOFError):
        print(f"\n\nGoodbye! The word was '{word}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
