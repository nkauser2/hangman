# Spec Project 2

This program is a hangman game that can be played by the user. What it prints or outputs depends on the user's actions, such as blanks for the unguessed letters in the word, the hangman figure after each wrong guess, and the letters that are already guessed. 

This program reads the word list file (word.txt, each line has the word, then a comma and then its category), and selects one word per round. It also reads the letters the player types.

Blank lines in word.txt (empty or only spaces) are skipped with no message. Bad lines are skipped and the game keeps going with the good words. A line is bad if it has no comma, nothing before the comma, nothing (or only spaces) after the comma, is just a comma by itself, or has a word with no letters in it. For each skipped bad line, the program prints a warning that includes the line number and the line's text, in this format:
`Warning: skipped line <number> of word.txt (<reason>): '<line text>'`
For example:
`Warning: skipped line 2 of word.txt (missing comma between word and category): 'broken'`
If word.txt has no good words at all, the program prints this message and exits without starting a game:
`Problem reading the word list: word.txt has no usable words`

The program prints or shows the board, the hangman figure, the hints, and the win message after word is guessed correctly or loss message at the end after 5 missed guesses. It prints an "Already guessed" message if user types a repeat letter (repeats are not counted as a miss, so 5-miss limit isn't affected). 

It will print first hint that is the first letter of the word after 2 missed guesses, and second hint is the category of the word after 4 missed guesses. 