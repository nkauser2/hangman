# Spec Project 2

This program is a hangman game that can be played by the user. What it prints or outputs depends on the user's actions, such as blanks for the unguessed letters in the word, the hangman figure after each wrong guess, and the letters that are already guessed. 

This program reads the word list file (word.txt, each line has the word, then a comma and then its category), and selects one word per round. It also reads the letters the player types.

The program prints or shows the board, the hangman figure, the hints, and the win message after word is guessed correctly or loss message at the end after 5 missed guesses. It prints an "Already guessed" message if user types a repeat letter (repeats are not counted as a miss, so 5-miss limit isn't affected). 

It will print first hint that is the first letter of the word after 2 missed guesses, and second hint is the category of the word after 4 missed guesses. 