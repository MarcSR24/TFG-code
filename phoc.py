import numpy as np
import math as m
import re

# Related to size of histograms
LETTERS = "abcdefghijklmnopqrstuvwxyzñç0123456789"
LETTERS_LIST = np.asarray([l for l in LETTERS],str)
LETTERS_SET = set(LETTERS)
LEVELS = 3

# Related to cleaning the words
SYMBOLS_REGEX = re.compile(r'[,;.:¡!¿?@#$%&[\](){}<>~=+\-*/|\\_^`"\']')
SUBSTITUTION_REGEX = [
    (re.compile('á'),'a'),
    (re.compile('é'),'e'),
    (re.compile('í|ï'),'i'),
    (re.compile('ó'),'o'),
    (re.compile('ú|ü'),'u'),
]

def clean_word(word : str) -> str:
    """
    For a given word, deletes special characters and substitutes special letters for their usual form

    Parameters:
        word : string
            The word to be cleaned
    Returns:
        l_word : string
            The word after cleaning
    """
    assert(type(word)==str)

    c_word = SYMBOLS_REGEX.sub('',word)
    l_word = c_word.lower()
    for regex, replace in SUBSTITUTION_REGEX:
        l_word = regex.sub(replace,l_word)
    return l_word


def get_splits(word : str, level : int) -> list[list[str]]:
    """
    Given a word and the level to which PHOC will be created, returns the word split in level parts

    Parameters:
        word : string
            The word to which PHOC is going to be applied
        level : integer
            The number of levels of histograms for the PHOC
    """
    assert(type(word) == str)
    assert(type(level) == int)

    # Get the number of letters for each split
    splits = []
    curr_level = 0
    splits.append([word])
    # Split the word in level splits
    while(curr_level < level-1):
        new_split = []
        for sp in splits[curr_level]:
            new_split.append(sp[:m.ceil(len(sp)/2)])
            new_split.append(sp[m.ceil(len(sp)/2):]) 
        splits.append(new_split)   
        curr_level += 1
    return splits

def initialize_hist() -> list[int]:
    """
    Creates the data structure for one histogram

    Returns:
        hist : list of integer
            A list of size len(LETTERS) with all values initialized at 0
    """
    hist = [0] * len(LETTERS)
    return hist

def create_hist(word : str, level_split : list) -> list[int]:
    """
    Creates the histogram vector of the given level for the word

    Parameters:
        word : string
            The word to which PHOC is being applied
        level_split : list of strings
    Returns:
        hist_list : list of list of integers
            A list containing the concatenation of the level's histograms of each split
    """
    assert(type(word) == str)

    hist_list = []
    # For each split in the word
    for split in level_split:
        hist = initialize_hist()
        # For each character in the split
        for letter in split:
           # Check if the character is in the abecedary
            if letter in LETTERS_SET:
                idx = LETTERS.index(letter)
                # If the character exists, increase the number of repetitions
                hist[idx] += 1
        # Add the histogram of the current split to the PHOC of the level's vector
        hist_list = hist_list + hist
    return hist_list

def PHOC(o_word : str, last_level : int = LEVELS) -> list[int]:
    """
    Creates the PHOC of given levels for the word

    Parameters:
        o_word : string
            The word to which PHOC is being applied to
        last_level : integer
            The number of levels wanted for PHOC
    Returns:
        pyramid : list of integers
            A list containing the concatenation of each level's histogram
    """
    assert(type(o_word) == str)
    assert(type(last_level) == int)

    word = clean_word(o_word)
    splits = get_splits(word,last_level)
    pyramid = []
    for i in range(0,last_level):
        pyramid = pyramid + create_hist(word,splits[i])
    return pyramid
