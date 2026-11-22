"""Automated tests for hangman.py. Run with:  python -m pytest"""

import pytest

import hangman
from hangman import ALREADY_GUESSED, CORRECT, INVALID, WRONG, Game


# ---------- Reading word.txt and splitting lines ----------

def test_parse_line_splits_word_and_category():
    assert hangman.parse_line("apple,fruit\n") == ("apple", "fruit")


def test_parse_line_trims_spaces_and_lowercases_word():
    assert hangman.parse_line("  Tiger , Animal  ") == ("tiger", "Animal")


def test_parse_line_splits_only_on_first_comma():
    assert hangman.parse_line("pear,fruit, green") == ("pear", "fruit, green")


def test_parse_line_blank_returns_none():
    assert hangman.parse_line("   \n") is None


@pytest.mark.parametrize(
    "bad", ["apple", ",fruit", "apple,", "apple,   ", ",", "123,numbers"]
)
def test_parse_line_rejects_malformed(bad):
    with pytest.raises(ValueError):
        hangman.parse_line(bad)


def write_words(tmp_path, text):
    f = tmp_path / "word.txt"
    f.write_text(text, encoding="utf-8")
    return f


def test_load_words_skips_blank_lines_silently(tmp_path):
    f = write_words(tmp_path, "apple,fruit\n\n   \ntiger,animal\nchair,furniture\n")
    warnings = []
    assert hangman.load_words(f, warn=warnings.append) == [
        ("apple", "fruit"),
        ("tiger", "animal"),
        ("chair", "furniture"),
    ]
    assert warnings == []


def test_load_words_skips_bad_lines_and_keeps_good_words(tmp_path):
    f = write_words(
        tmp_path,
        "apple,fruit\nbroken\n,fruit\napple,\napple,   \n,\n123,numbers\ntiger,animal\n",
    )
    warnings = []
    words = hangman.load_words(f, warn=warnings.append)
    assert words == [("apple", "fruit"), ("tiger", "animal")]
    assert len(warnings) == 6


def test_warning_for_category_of_only_spaces(tmp_path):
    f = write_words(tmp_path, "apple,fruit\npear,   \n")
    warnings = []
    assert hangman.load_words(f, warn=warnings.append) == [("apple", "fruit")]
    assert warnings == [
        "Warning: skipped line 2 of word.txt "
        "(word and category must both be filled in): 'pear,   '"
    ]


def test_warning_for_line_that_is_just_a_comma(tmp_path):
    f = write_words(tmp_path, ",\napple,fruit\n")
    warnings = []
    assert hangman.load_words(f, warn=warnings.append) == [("apple", "fruit")]
    assert warnings == [
        "Warning: skipped line 1 of word.txt "
        "(word and category must both be filled in): ','"
    ]


def test_exact_warning_text_for_other_bad_lines(tmp_path):
    f = write_words(tmp_path, "apple,fruit\nbroken\n123,numbers\n")
    warnings = []
    hangman.load_words(f, warn=warnings.append)
    assert warnings == [
        "Warning: skipped line 2 of word.txt "
        "(missing comma between word and category): 'broken'",
        "Warning: skipped line 3 of word.txt "
        "(word must contain at least one letter): '123,numbers'",
    ]


def test_player_sees_exact_warning_and_game_still_starts(tmp_path, monkeypatch, capsys):
    f = write_words(tmp_path, "broken\nhi,greeting\n")
    guesses = iter(["h", "i"])
    monkeypatch.setattr("builtins.input", lambda _: next(guesses))
    assert hangman.main(f) == 0
    out = capsys.readouterr().out
    assert out.startswith(
        "Warning: skipped line 1 of word.txt "
        "(missing comma between word and category): 'broken'\n"
    )
    assert "Congratulations! You spelled 'hi' correctly!" in out


def test_load_words_only_blank_lines_raises(tmp_path):
    f = write_words(tmp_path, "\n\n")
    with pytest.raises(ValueError, match="no usable words"):
        hangman.load_words(f, warn=lambda _: None)


def test_load_words_all_bad_lines_warns_then_raises(tmp_path):
    f = write_words(tmp_path, "broken\n,\n")
    warnings = []
    with pytest.raises(ValueError, match="no usable words"):
        hangman.load_words(f, warn=warnings.append)
    assert len(warnings) == 2


def test_player_sees_message_when_no_usable_words(tmp_path, capsys):
    f = write_words(tmp_path, "broken\n")
    assert hangman.main(f) == 1
    out = capsys.readouterr().out
    assert out.endswith(
        "Problem reading the word list: word.txt has no usable words\n"
    )

# ---------- Checking guesses ----------

def test_correct_guess_reveals_letter():
    g = Game("apple", "fruit")
    assert g.guess("p") == CORRECT
    assert g.masked_word() == "_ p p _ _"
    assert g.misses == 0


def test_wrong_guess_counts_a_miss():
    g = Game("apple", "fruit")
    assert g.guess("z") == WRONG
    assert g.misses == 1


def test_guess_is_case_insensitive_and_trimmed():
    g = Game("apple", "fruit")
    assert g.guess("  A ") == CORRECT
    assert "a" in g.guessed


def test_guessed_letters_are_tracked_right_and_wrong():
    g = Game("apple", "fruit")
    g.guess("a")
    g.guess("z")
    assert g.guessed == ["a", "z"]


# ---------- Invalid input and repeated guesses ----------

@pytest.mark.parametrize("bad", ["", "   ", "ab", "1", "?", "é", None])
def test_invalid_input_is_rejected_without_a_miss(bad):
    g = Game("apple", "fruit")
    assert g.guess(bad) == INVALID
    assert g.misses == 0
    assert g.guessed == []


def test_repeated_correct_guess_is_already_guessed():
    g = Game("apple", "fruit")
    g.guess("a")
    assert g.guess("a") == ALREADY_GUESSED
    assert g.guess("A") == ALREADY_GUESSED
    assert g.misses == 0


def test_repeated_wrong_guess_does_not_add_a_miss():
    g = Game("apple", "fruit")
    g.guess("z")
    assert g.guess("z") == ALREADY_GUESSED
    assert g.misses == 1


def test_play_prints_already_guessed_message():
    g = Game("hi", "greeting")
    inputs = iter(["h", "h", "i"])
    out = []
    hangman.play(g, read=lambda _: next(inputs), write=out.append)
    assert any("Already guessed" in line for line in out)


# ---------- Hints after 2 and 4 misses ----------

def test_no_hints_before_two_misses():
    g = Game("apple", "fruit")
    g.guess("z")
    assert g.hints() == []


def test_first_letter_hint_after_two_misses():
    g = Game("apple", "fruit")
    g.guess("z")
    g.guess("x")
    hints = g.hints()
    assert len(hints) == 1
    assert "A" in hints[0]
    assert "fruit" not in hints[0]


def test_category_hint_only_after_four_misses():
    g = Game("apple", "fruit")
    for letter in "zxw":
        g.guess(letter)
    assert len(g.hints()) == 1
    g.guess("v")
    hints = g.hints()
    assert len(hints) == 2
    assert "fruit" in hints[1]


def test_repeats_and_invalid_input_do_not_unlock_hints():
    g = Game("apple", "fruit")
    g.guess("z")
    g.guess("z")
    g.guess("12")
    assert g.hints() == []


def test_hints_appear_on_rendered_board():
    g = Game("apple", "fruit")
    for letter in "zxwv":
        g.guess(letter)
    board = hangman.render(g)
    assert "starts with 'A'" in board
    assert "Category: fruit" in board


# ---------- Win / loss at the right time ----------

def test_win_when_all_letters_guessed():
    g = Game("apple", "fruit")
    for letter in "apl":
        assert not g.is_won()
        g.guess(letter)
    g.guess("e")
    assert g.is_won()
    assert not g.is_lost()
    assert g.is_over()


def test_not_lost_after_four_misses():
    g = Game("apple", "fruit")
    for letter in "zxwv":
        g.guess(letter)
    assert not g.is_lost()
    assert not g.is_over()


def test_lost_exactly_at_five_misses():
    g = Game("apple", "fruit")
    for letter in "zxwvu":
        g.guess(letter)
    assert g.misses == 5
    assert g.is_lost()
    assert g.is_over()


def test_win_on_last_chance_after_four_misses():
    g = Game("hi", "greeting")
    for letter in "zxwv":
        g.guess(letter)
    g.guess("h")
    g.guess("i")
    assert g.is_won()
    assert not g.is_lost()


def test_no_guesses_allowed_after_game_over():
    g = Game("hi", "greeting")
    g.guess("h")
    g.guess("i")
    with pytest.raises(RuntimeError):
        g.guess("a")


def test_play_win_shows_congratulations():
    g = Game("hi", "greeting")
    inputs = iter(["h", "i"])
    out = []
    assert hangman.play(g, read=lambda _: next(inputs), write=out.append) is True
    assert "Congratulations" in out[-1]


def test_play_loss_reveals_word_and_says_try_again():
    g = Game("hi", "greeting")
    inputs = iter(list("abcde"))
    out = []
    assert hangman.play(g, read=lambda _: next(inputs), write=out.append) is False
    assert "Try again next time" in out[-1]
    assert "hi" in out[-1]


# ---------- Hangman figure ----------

def test_figure_changes_with_each_miss_and_is_complete_at_five():
    g = Game("apple", "fruit")
    seen = [g.figure()]
    for letter in "zxwvu":
        g.guess(letter)
        seen.append(g.figure())
    assert len(set(seen)) == 6
    assert seen[-1] == hangman.HANGMAN_STAGES[-1]
