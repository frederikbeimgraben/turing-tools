"""
Turing Machine emulator - model.py

Contains the model of the Turing Machine (classes)
"""

from email import message
from os import stat
import time
from typing import Any, Dict, List, Tuple, Union
from tools import *
from printf import warning, error

LEFT = 'L'
RIGHT = 'R'
BLANK = '_'
ANY = '*'

class Transition:
    """
    Transition class
    """

    def __init__(self, state: 'State', char: str, new_state: 'State', new_char: str, direction: str):
        self.state = state
        self.char = char
        self.new_state = new_state
        self.new_char = new_char
        self.direction = direction

    def __str__(self):
        return f'Transition({self.state} {self.char} -> {self.new_state} {self.new_char} {self.direction})'

    def __repr__(self):
        return str(self)

    def __eq__(self, other: Tuple['State', str]):
        return self.state == other[0] and self.char == other[1]


class State:
    """
    State of the Turing Machine
    """

    _name: str
    _transitions: Dict[str, Transition]

    @property
    def transitions(self) -> dict:
        """
        Get transitions
        """
        return self._transitions

    @property
    def name(self) -> str:
        """
        Get name
        """
        return self._name

    def __getitem__(self, key):
        """
        Get transition
        """
        return self.transitions[key]

    def __setitem__(self, key, value):
        """
        Set transition
        """
        self.transitions[key] = value

    def __init__(self, name: Union[str, 'State']):
        """
        Initialize state
        """

        if isinstance(name, State):
            self._name = name.name
            self._transitions = name.transitions
        else:
            self._name = name
            self._transitions = {}

    def __str__(self):
        """
        String representation
        """

        return f'<State {self.name}>'

    def __repr__(self):
        return str(self)

    def __eq__(self, other: object) -> bool:
        return str(self) == str(other)


class Tape:
    """
    Tape of the Turing Machine
    """
    
    _tape: List[str] = []
    _head: int = 0

    def __init__(self, tape: Union[str, List[str]]):
        """
        Initialize tape
        """

        if isinstance(tape, str):
            self._tape = [c for c in tape]
        elif isinstance(tape, list):
            self._tape = tape
        else:
            raise TypeError(f'Unknown type \'{type(tape)}\' for tape')

        self._head = 0

    @property
    def tape(self) -> List[str]:
        """
        Get tape
        """
        return self._tape

    @property
    def head(self) -> int:
        """
        Get head
        """
        return self._head

    @head.setter
    def head(self, value):
        """
        Set head
        """
    
        while value >= len(self.tape):
            self.tape.append(BLANK)
        while value < 0:
            self.tape.insert(0, BLANK)
            self.head += 1
            value += 1
        else:
            self._head = value

    def move_head(self, direction: str):
        """
        Move head
        """

        if direction == LEFT:
            self.head -= 1
        elif direction == RIGHT:
            self.head += 1
        elif direction == ANY:
            pass
        else:
            raise ValueError(f'Unknown direction \'{direction}\'')

    def __getitem__(self, index):
        """
        Get item at index
        """

        index = self.head + index

        while index >= len(self.tape):
            self.tape.append(BLANK)
        while index < 0:
            self.tape.insert(0, BLANK)
            self.head += 1
            index += 1
        else:
            return self.tape[index]

    def __setitem__(self, index, value):
        """
        Set item at index
        """

        index = self.head + index

        while index >= len(self.tape):
            self.tape.append(BLANK)
        while index < 0:
            self.tape.insert(0, BLANK)
            self.head += 1
            index += 1
        if value != ANY:
            self.tape[index] = value

    def __len__(self):
        """
        Get length of tape
        """

        return len(self.tape)

    def __str__(self):
        """
        String representation
        """

        return ''.join(self.tape)

    def fancy(self):
        """
        Fancy representation
        """

        tape_str = ''

        fancy = lambda string: string.replace('_', f'{strikethrough()}␣{reset()}')

        # get terminal width
        width = get_terminal_width()

        span = width // 4 - 1

        tape_str += '┏' + '━┳' * span * 2 + '━┓\n┃'

        for index in range(-span, span + 1):
            if index == 0:
                tape_str += f'{foreground(0,255,0)}{bold()}{underline()}' + fancy(self[index]) + f'{reset()}'
            else:
                tape_str += fancy(self[index])
            tape_str += '┃'

        tape_str += '\n┗' + '━┻' * span * 2 + '━┛'
        
        return tape_str

    def __repr__(self):
        return str(self)


class TransitionTable:
    """
    Transition table of the Turing Machine
    """

    @property
    def states(self) -> List[State]:
        """
        Get states
        """
        return self._states

    def __getitem__(self, key):
        """
        Get state
        """
        return self.states[key]

    def __setitem__(self, key, value):
        """
        Set state
        """
        self.states[key] = value

    def __init__(self, states: List[State], tape: Tape):
        """
        Initialize transition table
        """

        self._states = states
        self._tape = tape

    def __call__(self, state: 'State', char: str) -> Any:
        """
        Find matching `Transition` or return `None`
        """

        for state_self in self.states:
            if state_self == state:
                state = state_self
            for transition in state.transitions:
                transition: Transition = state.transitions[transition]
                if transition.char == char or transition.char == ANY:
                    return transition

        return None

    def __str__(self):
        """
        String representation
        """

        return f'<TransitionTable {self.states}>'

    def __repr__(self):
        return str(self)

    def append(self, other: Union['Transition', 'TransitionTable', 'State', List]):
        """
        Append transition or state
        """

        if isinstance(other, Transition):
            if other.state not in self.states:
                warning(f'State {other.state} not found in transition table! Adding it now...')
                self.states.append(other.state)
            if other.new_state not in self.states:
                warning(f'State {other.new_state} not found in transition table! Adding it now...')
                self.states.append(other.new_state)
            for index, state in enumerate(self.states):
                if state == other.state:
                    other.state = state
                    self.states[index].transitions[other.char] = other
                if state == other.new_state:
                    other.new_state = state
        elif isinstance(other, State):
            if other not in self.states:
                self.states.append(other)
        elif isinstance(other, TransitionTable):
            self.states.extend(other.states)
        elif isinstance(other, list):
            if State(other[0]) not in self.states:
                self.append(State(other[0]))
            if State(other[2]) not in self.states:
                self.append(State(other[2]))
            self.append(Transition(
                state=State(other[0]),
                char=other[1],
                new_state=State(other[2]),
                new_char=other[3],
                direction=other[4]
            ))
        else:
            raise TypeError(f'Cannot append \'{type(other)}\' to TransitionTable')
        
    def __contains__(self, item: 'State'):
        """
        Check if state or transition is in table
        """

        if isinstance(item, State):
            return item in self.states
        elif isinstance(item, Transition):
            return item.state in self.states and item in item.state.transitions
        else:
            raise TypeError(f'Cannot check if \'{type(item)}\' is in TransitionTable')


class TuringMachine:
    """
    Turing Machine
    """

    _transition_table: TransitionTable
    _tape: Tape
    _state: State
    _halt: List[State] = ['HALT']
    _alphabet: List[str] = [BLANK, '0', '1']

    @property
    def transition_table(self) -> TransitionTable:
        """
        Get transition table
        """
        return self._transition_table

    @property
    def tape(self) -> Tape:
        """
        Get tape
        """
        return self._tape

    @property
    def state(self) -> State:
        """
        Get state
        """
        return self._state

    @state.setter
    def state(self, value: State):
        """
        Set state
        """
        self._state = value

    @property
    def halt(self) -> List[State]:
        """
        Get halt states
        """
        return self._halt

    @property
    def alphabet(self) -> List[str]:
        """
        Get alphabet
        """
        return self._alphabet

    def __init__(self, transition_table: TransitionTable=None, tape: Tape=None, state: State=None, halt: List[State]=None, alphabet: List[str]=None):
        """
        Initialize Turing Machine
        """

        # Set initial state
        if state is not None:
            if transition_table is None or state not in transition_table:
                raise ValueError(f'Starting state \'{state}\' not in transition table.')
            self._state = state

        # Initialize transition table
        if transition_table is not None:
            self._transition_table = transition_table

        # Initialize tape
        if isinstance(tape, Tape):
            self._tape = tape
        elif tape is not None:
            self._tape = Tape(tape)

        # Append halt state
        if halt is not None:
            self._halt += halt

        # Append alphabet
        if alphabet is not None:
            self._alphabet += alphabet

    def step(self, step: int) -> bool:
        """
        Step Turing Machine
        """

        # Get transition
        transition = self.transition_table(self.state, self.tape[0])
        if transition is None:
            # raise ValueError(f'No transition for {self.state} {self.tape[0]}')
            return False
        self.tape[0] = transition.new_char
        self.state = transition.new_state
        self.tape.move_head(transition.direction)

        print_step(self, transition, step)

        return True

    def run(self):
        """
        Run Turing Machine
        """

        step = 1
        inpt = ''
        msg = ''

        while inpt != 'q':
            if not self.step(step):
                print_step(self, Transition(self.state, self.tape[0], State('*'), '*', '*'), step)
            msg = 'Stepped one step.'
            if self.state in self.halt:
                msg = f'HALTED at step {step}'
            else:
                step += 1

            info(msg)

            inpt = input(f'(skip: <int> | move: <r/l> | func: $<state> | halt)\n > ')

            while inpt != '':
                if inpt.isdigit():
                    for x in range(int(inpt)):
                        if self.step(step):
                            step += 1
                            time.sleep(0.01)
                    msg = f'Skipping forward {int(inpt)} steps'
                    break
                elif inpt == 'r':
                    self.tape.move_head(RIGHT)
                    msg = 'Moving head right'
                elif inpt == 'l':
                    self.tape.move_head(LEFT)
                    msg = 'Moving head left'
                elif inpt[0] == '$':
                    self.state = State(inpt[1:])
                    msg = f'Changing state to {self.state}'
                elif inpt[0] == '+' and len(inpt) > 1 and inpt[1] in self.alphabet:
                    msg = f'Writing {inpt[1:]} to tape'
                    self.tape[0] = inpt[1]
                else:
                    msg = f'Invalid input \'{inpt}\''

                print_step(self, Transition(self.state, self.tape[0], State('*'), '*', '*'), step)

                info(msg)

                inpt = input(f'(skip: <int> | move: <r/l> | func: $<state>)\n > ')


                

    def __str__(self):
        """
        String representation
        """

        return f'<TuringMachine {self.transition_table} {self.tape} {self.state}>'

    def __repr__(self):
        return str(self)