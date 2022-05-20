"""
Functions for printing formatted strings to the console.
"""

import subprocess
from typing import List, Union
# from model import Transition
import re


def visible(string: str) -> str:
    """
    Returns a string with all non-printable characters and ANSI escape sequences
    removed.
    """
    return re.sub(r'\x1b[^m]*m', '', string)



def foreground(r, g, b) -> str:
    """
    Returns the ansi instruction for setting the foreground color.
    """

    return f'\x1B[38;2;{r};{g};{b}m'


def background(r, g, b) -> str:
    """
    Returns the ansi instruction for setting the background color.
    """

    return f'\x1B[48;2;{r};{g};{b}m'


def reset() -> str:
    """
    Returns the ansi instruction for resetting the colors.
    """

    return '\x1B[0m'


def bold() -> str:
    """
    Returns the ansi instruction for setting the bold font.
    """

    return '\x1B[1m'


def underline() -> str:
    """
    Returns the ansi instruction for setting the underline font.
    """

    return '\x1B[4m'


def italic() -> str:
    """
    Returns the ansi instruction for setting the italic font.
    """

    return '\x1B[3m'


def strikethrough() -> str:
    """
    Returns the ansi instruction for setting the strikethrough font.
    """

    return '\x1B[9m'


def inverse() -> str:
    """
    Returns the ansi instruction for setting the inverse font.
    """

    return '\x1B[7m'


def debug(header: str, *info: str) -> None:
    """
    Prints a debug message to the console. (light gray text, bold)
    """

    print(f'{foreground(200, 200, 200)}[DEBUG]\t{header}')

    for i in info:
        for l in str(i).split('\n'):
            print(f'\t┊ {l}')

    print(reset())


def info(header: str, *info: str) -> None:
    """
    Prints an info message to the console. (light blue text, bold)
    """

    print(f'{bold()}{foreground(0, 0, 255)}[INFO]\t{reset()}{header}')

    for i in info:
        for l in str(i).split('\n'):
            print(f'\t┊ {l}')


def warning(header: str, *info: str) -> None:
    """
    Prints a warning message to the console. (yellow text, bold)
    """

    print(f'{bold()}{foreground(255, 255, 0)}[WARNING]\t{reset()}{header}')

    for i in info:
        for l in str(i).split('\n'):
            print(f'\t┊ {l}')


def error(header: str, *info: str) -> None:
    """
    Prints an error message to the console. (red text, bold)
    """

    print(f'{bold()}{foreground(255, 0, 0)}[ERROR]\t{reset()}{header}')

    for i in info:
        for l in str(i).split('\n'):
            print(f'\t┊ {l}')


def print_step(machine, transtition, step: int) -> None:
    """
    Prints the current step to the console.
    """

    redraw(
        f'{bold()}{foreground(0, 255, 0)}Step {step}{reset()}\n' +
        f'{bold()}{foreground(0, 255, 0)}Tape{reset()}\n' +
        f'{machine.tape.fancy()}\n' +
        f'{bold()}{foreground(0, 255, 0)}Transition{reset()}\n' +
        f'\t{transition_string(transtition)}'
    )


def yes_no(question: str, default: bool = False) -> bool:
    """
    Asks the user a yes/no question.
    """

    while True:
        answer = input(f'{question} [{("Y" if default else "y")}/{("N" if not default else "n")}]: ')

        if answer == '':
            return default

        if answer.lower() == 'y':
            return True

        if answer.lower() == 'n':
            return False

        print('Please answer with either "y" or "n".')

def highlight_index(string: Union[str, List], index: int):
    """
    Highlights the given index in the given string.
    """

    if isinstance(string, list):
        string = ''.join(string)

    if index < 0 or index >= len(string):
        return string
    return string[:index] + f'{bold()}{foreground(0,255,0)}{string[index]}{reset()}' + string[index + 1:]

def print_highlight(string: str, index: int) -> None:
    """
    Prints the given string with the given index highlighted.
    """

    print(highlight_index(string, index))

def redraw(string: str) -> None:
    """
    Redraws the console with the given tape and index highlighted.
    """

    print(f'\x1b[2J\x1b[H')
    print(string)

def get_terminal_width() -> int:
    """
    Returns the width of the terminal.
    """

    return int(subprocess.check_output(['tput', 'cols']))

def transition_string(transition) -> str:
    """
    Returns a string representation of the given transition.
    """

    return f'{transition.state.name} : {transition.char} -> {transition.new_state.name} : {transition.char} : {transition.direction}'