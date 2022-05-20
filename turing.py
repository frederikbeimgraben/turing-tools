"""
Tests
"""

from parser import Parser
from printf import redraw


def main():
    """
    Main function
    """
    parser = Parser('assembler.tur')
    if parser.parse():
        machine = parser.make_turing_machine()
        machine.run()

if __name__ == "__main__":
    main()