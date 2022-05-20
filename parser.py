"""
Parse a turing machine saved as a .tur file
"""

import os
from tkinter import ALL
from typing import List, Union
from model import Tape, Transition, State, TransitionTable, TuringMachine, BLANK, ANY
from printf import *
from tools import allowed_state, allowed_tape, allowed_transition, strip_state, ALLOWED

IGNORE = [
    '\t',
    ' '
]




class Scopes:
    """
    Interpreter Scope / Scopes.NSPC
    """

    TSTR = 'TSTR' # Tape string
    ASTS = 'ASTS' # Add states
    ATRS = 'ATRS' # Add transition
    INIT = 'INIT' # Initial state
    HLTS = 'HALT' # Halt state
    ALPH = 'ALPH' # Alphabet
    FNSP = 'FNSP' # Find name space start
    NSPC = 'NSPC' # Name space
    CMNT = 'CMNT' # Comment
    SCRF = 'SCRF' # Sacrifice Constant (?)

    scopes: List[str]

    def __init__(self):
        """
        Initialize the scope
        """
        self.scopes = []

    def exit(self, scope: str=None):
        """
        Exit the current scope
        """

        if self.scopes:
            if not scope:
                return self.scopes.pop()
            elif self.scopes[-1][0] == scope:
                return self.scopes.pop()
            else:
                error(f'Tried to exit {scope} but found {self.scopes[-1][0]}')
                raise ValueError(f'Tried to exit {scope} but found {self.scopes[-1][0]}')
        else:
            error('Cannot exit scope. At root level!', self.scopes, scope)
            raise ValueError('Cannot exit scope. At root level!')

    def enter(self, scope: str, name: str=None):
        """
        Enter a new scope
        """

        self.scopes.append((scope, name))

    def extend_name(self, name: str):
        """
        Extend the current scope with names
        """

        count = 0

        prefix = [
            name if name else str(count := count + 1) 
            for scope, name in self.scopes 
            if scope == Scopes.NSPC
        ]

        return '.'.join(prefix + [name] if name != '' else prefix)

    @property
    def top(self) -> str:
        """
        Get the current Scopes.NSPC
        """

        return self.scopes[-1][0] if self.scopes else Scopes.NSPC

class Parser:
    """
    Parse a turing machine saved as a .tur file

    Syntax:
        &<tape-string>;
            A tape string
        
        @<char>:<char>:...;
            Tape alphabet

        $<state>:<char> -> <new_state>:<new_char>:<direction>;
            Transition

        !<state>;
            Initial state

        ~<state>:<state>:...;
            Halt state(s)
        
        *<state>:<state>:...;
            Any state(s)

        ':' are separators -> List of ...;

        :<namespace> {
            *<state>:...;            # Local State (later registered as <namespace>.<state>)

            $<namespace>:... -> ...; # namespace init function
            $<state>:... -> ...;     # Transition function
            ...
        }
    """

    file: str
    tape: str
    transitions: TransitionTable
    alphabet: List[str]
    initial: State
    halt: List[State]

    def __init__(self, file: str):
        """
        Parse a turing machine saved as a .tur file
        """

        # Assert that the file exists and is accessible
        if not os.path.isfile(file):
            error(f'File {file} not found!')
            exit()
        # Warn if it is not a .tur file
        elif not file.endswith('.tur'):
            warning(f'File {file} is not a .tur file:', file)
            # Ask if the user wants to continue
            if not yes_no('Continue anyway?'):
                error('Aborting')
                exit()
        # Assert that the file is readable
        elif not os.access(file, os.R_OK):
            error(f'File {file} is not readable!')
            exit()
        
        self.file = file
        self.tape = None
        self.transitions = TransitionTable([], None)
        self.initial = None
        self.halt = []
        self.alphabet = []

    def parse(self, verbose=False):
        """
        Parse file
        """

        # global Scopes.NSPC, Scopes.TSTR, Scopes.ASTS, Scopes.ATRS, Scopes.INIT, Scopes.HLTS, Scopes.ALPH, Scopes.FNSP, Scopes.NSPC, Scopes.CMNT

        # Open file
        with open(self.file, 'r') as file:
            # Read file
            text = file.read()
            queue = list(text)
            lines = text.split('\n')

        line_count = 1
        ch_index = 0

        buffer: List[str] = []
        subbuffer: str = ''
        scopes: Scopes = Scopes()
        history: List[str] = []

        errors = 0

        # Parse file
        while queue:
            try:
                char = queue.pop(0)

                # Ignores
                if char in IGNORE:
                    continue
                
                ch_index += 1

                # New Line
                if char == '\n':
                    line_count += 1
                    ch_index = 0
                
                match (char, scopes.top):
                    case ('&', Scopes.NSPC):
                        if Scopes.TSTR in history:
                            warning('Multiple tape strings defined! Overwriting previous definition!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        scopes.enter(Scopes.TSTR)
                    case ('@', Scopes.NSPC):
                        scopes.enter(Scopes.ALPH)
                    case ('$', Scopes.NSPC):
                        scopes.enter(Scopes.ATRS)
                    case ('!', Scopes.NSPC):
                        scopes.enter(Scopes.INIT)
                    case ('~', Scopes.NSPC):
                        scopes.enter(Scopes.HLTS)
                    case ('*', Scopes.NSPC):
                        scopes.enter(Scopes.ASTS)
                    case ('#', Scopes.NSPC):
                        scopes.enter(Scopes.CMNT)
                    case ('{', Scopes.FNSP):
                        if not subbuffer:
                            subbuffer = ''
                            buffer = []
                            error(f'Invalid Scopes.NSPC \'{subbuffer}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid Scopes.NSPC \'{subbuffer}!\'', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        scopes.enter(Scopes.NSPC, subbuffer)
                        if State(subbuffer) in self.transitions:
                            subbuffer = ''
                            buffer = []
                            warning(f'State \'{state}\' already defined!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            # raise ValueError(f'State \'{state}\' already defined!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        self.transitions.append(State(subbuffer))
                        subbuffer = ''
                        buffer = []
                    case ('}', Scopes.NSPC):
                        try:
                            scope, _ = scopes.exit(Scopes.NSPC)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)
                    case (':', Scopes.NSPC):
                        scopes.enter(Scopes.FNSP)
                    # Exit scopes
                    case (';', Scopes.TSTR):
                        try:
                            scope, _ = scopes.exit(Scopes.TSTR)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)

                        if not subbuffer:
                            subbuffer = ''
                            buffer = []
                            error(f'Invalid tape string \'{subbuffer}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid tape string \'{subbuffer}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        for char in subbuffer:
                            if char not in self.alphabet:
                                subbuffer = ''
                                buffer = []
                                error(f'Character not in alphabet \'{char}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                                raise ValueError(f'Character not in alphabet \'{char}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        self.tape = subbuffer
                        subbuffer = ''
                        buffer = []
                    case (';', Scopes.ALPH):
                        try:
                            scope, _ = scopes.exit(Scopes.ALPH)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)

                        buffer.append(subbuffer)
                        if not subbuffer:
                            subbuffer = ''
                            buffer = []
                            error(f'Invalid Scopes.ALPH {buffer}!')
                            raise ValueError(f'Invalid Scopes.ALPH {buffer}!')
                        for char in buffer:
                            if char in self.alphabet:
                                warning(f'Character \'{char}\' already defined in Scopes.ALPH!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            if (not char.isalnum()) and (char not in ALLOWED):
                                subbuffer = ''
                                buffer = []
                                error(f'Invalid character \'{char}\' in Scopes.ALPH!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                                raise ValueError(f'Invalid character \'{char}\' in Scopes.ALPH!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        self.alphabet = buffer
                        if not '_' in self.alphabet:
                            self.alphabet.append('_')
                        subbuffer = ''
                        buffer = []
                        
                    case (';', Scopes.ATRS):
                        try:
                            scope, _ = scopes.exit(Scopes.ATRS)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)

                        buffer.append(subbuffer)
                        if not len(buffer) == 5:
                            subbuffer = ''
                            buffer = []
                            error(f'Invalid transition {buffer}!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid transition {buffer}!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        
                        buffer[0] = scopes.extend_name(buffer[0] if buffer[0] != '*' else '')

                        if buffer[2][0] == '.':
                            if State(buffer[2][1:]) in self.transitions:
                                buffer[2] = State(buffer[2][1:])
                            else:
                                subbuffer = ''
                                buffer = []
                                error(f'Invalid transition {buffer}!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                                raise ValueError(f'Invalid transition {buffer}!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        else:
                            buffer[2] = State(scopes.extend_name(buffer[2]))
                            
                        self.transitions.append(buffer)
                        subbuffer = ''
                        buffer = []
                        
                    case (';', Scopes.INIT):
                        try:
                            scope, _ = scopes.exit(Scopes.INIT)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)

                        if not subbuffer:
                            subbuffer = ''
                            buffer = []
                            error(f'Invalid initial state \'{subbuffer}\'!', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid initial state \'{subbuffer}\'!', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        state = State(scopes.extend_name(subbuffer))
                        self.initial = state
                        subbuffer = ''
                        buffer = []
                        
                    case (';', Scopes.HLTS):
                        try:
                            scope, _ = scopes.exit(Scopes.HLTS)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)

                        buffer.append(subbuffer)
                        if not subbuffer:
                            error(f'Invalid halt states {buffer}!')
                            raise ValueError(f'Invalid halt states {buffer}!')
                        for state in buffer:
                            state = State(scopes.extend_name(state))
                            if state not in self.transitions:
                                subbuffer = ''
                                buffer = []
                                error(f'Invalid halt state \'{state}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                                raise ValueError(f'Invalid halt state \'{state}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            self.halt.append(state)
                        
                        subbuffer = ''
                        buffer = []
                    case ('\n', Scopes.CMNT):
                        subbuffer = ''
                        buffer = []
                        try:
                            scope, _ = scopes.exit(Scopes.CMNT)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)
                    case (';', Scopes.ASTS):
                        buffer.append(subbuffer)
                        if not subbuffer:
                            subbuffer = ''
                            buffer = []
                            error(f'Invalid states {buffer}!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid states {buffer}!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        for state in buffer:
                            name_extended = scopes.extend_name(state)
                            if State(name_extended) in self.transitions:
                                subbuffer = ''
                                buffer = []
                                warning(f'State \'{state}\' already defined!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                                # raise ValueError(f'State \'{state}\' already defined!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            self.transitions.append(State(name_extended))
                        subbuffer = ''
                        buffer = []
                        try:
                            scope, _ = scopes.exit(Scopes.ASTS)
                        except ValueError as e:
                            subbuffer = ''
                            buffer = []
                            error(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(e, f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        history.append(scope)
                    # Separators / Buffer builders
                    case (':', Scopes.NSPC):
                        error (f'Invalid character \'{char}\' in namespace!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        raise ValueError(f'Invalid character \'{char}\' in namespace!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                    case (':', Scopes.TSTR):
                        error (f'Separator \'{char}\' in tape string!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        raise ValueError(f'Separator \'{char}\' in tape string!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                    case (':', Scopes.INIT):
                        error (f'Separator \'{char}\' in initial state!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        raise ValueError(f'Separator \'{char}\' in initial state!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                    case (':', _):
                        buffer.append(subbuffer)
                        subbuffer = ''
                    case ('>', Scopes.ATRS):
                        buffer.append(subbuffer)
                        subbuffer = ''
                    case ('-', Scopes.ATRS):
                        continue
                    # Subbuffer builders
                    case ('\n', _):
                        continue
                    case (_, Scopes.CMNT):
                        pass
                    case (_, Scopes.FNSP):
                        if not char.isalnum():
                            error(f'Invalid character \'{char}\' in namespace!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid character \'{char}\' in namespace!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        subbuffer += char
                    case (_, Scopes.TSTR):
                        if not allowed_tape(char):
                            error(f'Invalid character \'{char}\' in tape string!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid character \'{char}\' in tape string!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        subbuffer += char
                    case (_, Scopes.ALPH):
                        if (not char.isalnum()) and (char not in ALLOWED):
                            error(f'Invalid character \'{char}\' in alphabet!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid character \'{char}\' in alphabet!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        subbuffer += char
                    case (_, Scopes.ATRS):
                        if not allowed_transition(char):
                            error(f'Invalid character \'{char}\' in transition!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid character \'{char}\' in transition!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        subbuffer += char
                    case (_, Scopes.INIT):
                        if not allowed_state(char):
                            error(f'Invalid character \'{char}\' in initial state!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid character \'{char}\' in initial state!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        subbuffer += char
                    case (_, Scopes.HLTS):
                        if not allowed_state(char):
                            error(f'Invalid character \'{char}\' in halt state!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid character \'{char}\' in halt state!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        subbuffer += char
                    case (_, Scopes.ASTS):
                        if not allowed_state(char):
                            error(f'Invalid character \'{char}\' in add states!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                            raise ValueError(f'Invalid character \'{char}\' in alphabet!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        subbuffer += char
                    case (_, _):
                        error(f'Invalid character \'{char}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
                        raise ValueError(f'Invalid character \'{char}\'!', f'Line {line_count}', f'Scope: {scopes.top}', highlight_index(lines[line_count - 1], ch_index))
            except ValueError:
                errors += 1
        try:
            if not self.initial or self.initial not in self.transitions:
                error(f'Invalid initial state \'{state}\'!')
                raise ValueError(f'Invalid initial state \'{state}\'!')
            
            # Check if all target states are valid
            for state in self.transitions.states:
                for target in state.transitions.values():
                    if target.new_state not in self.transitions:
                        error(f'Invalid target state \'{target}\'!')
                        raise ValueError(f'Invalid target state \'{target}\'!')
        except ValueError:
            errors += 1
        if errors > 0:
            error(f'{errors} error(s) found!')
            return False
        self.tape = Tape(self.tape)
        return True
        
    def make_turing_machine(self):
        """
        Creates a Turing Machine from the parsed lines.
        """

        for state in self.transitions:
            if state.name == '':
                self.transitions.states.remove(state)

        # Get the tape alphabet
        tape_alphabet = self.alphabet
        # Get the transition table
        transition_table = self.transitions
        # Get the initial state
        initial_state = self.initial
        # Get the halt state
        halt_state = self.halt
        # Get the states
        states = self.transitions.states
        # Create the Turing Machine
        return TuringMachine(transition_table, self.tape, initial_state, halt_state, tape_alphabet)