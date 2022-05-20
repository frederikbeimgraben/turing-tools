"""
Includes general functions for the project.
"""

from printf import *

ALLOWED = [
    '#', '_'
]

def strip_state(string, silent=False):
    """
    Strips the string of all non alphanumeric characters.
    """
    
    stripped = ''
    for char in string:
        if allowed_state(char):
            stripped += char
    
    if stripped != string:
        warning(f'Invalid state \'{string}\'! Corrected to \'{stripped}\'')

    return stripped

def allowed_state(string: str):
    """
    Checks if the string is a valid state.
    """

    for char in string:
        if not char.isalnum() and char != '.':
            return False
    return True

def allowed_transition(string: str):
    """
    Checks if the string contains invalid characters.
    """

    for char in string:
        if (not char.isalnum()) and char not in ALLOWED + ['.', '*']:
            return False
    return True

def allowed_tape(string: str):
    """
    Checks if the string contains invalid characters.
    """

    for char in string:
        if not char.isalnum() and char not in ALLOWED:
            return False
    return True

def strip_tape(string):
    """
    Strips the string of all forbidden characters.
    """
    
    stripped = ''
    for char in string:
        if allowed_tape(char):
            stripped += char

    if stripped != string:
        warning(f'Invalid tape \'{string}\'! Corrected to \'{stripped}\'')
    
    return stripped