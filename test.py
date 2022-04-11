"""
A simple script that generate random number around a given number.
"""

import random
import sys


def main():
    """
    Main function.
    """
    if len(sys.argv) != 2:
        print("Usage: {} <number>".format(sys.argv[0]))
        sys.exit(1)

    try:
        number = int(sys.argv[1])
    except ValueError:
        print("Error: {} is not a number.".format(sys.argv[1]))
        sys.exit(1)

    print("{} +- {}".format(number, random.randint(0, 100)))


if __name__ == "__main__":
    main()
