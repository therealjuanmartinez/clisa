from colorama import Fore
import sys

def printGreen(mystr, end=''):
    print(Fore.GREEN + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printSunsetOrange(mystr, end=''):
    print(Fore.LIGHTRED_EX + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printYellow(mystr, end=''):
    print(Fore.YELLOW + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printOrange(mystr, end=''):
    print(Fore.LIGHTYELLOW_EX + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printRed(mystr, end=''):
    print(Fore.RED + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printGrey(mystr, end=''):
    print(Fore.LIGHTBLACK_EX + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printDarkGrey(mystr, end=''):
    print(Fore.BLACK + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printPeach(mystr, end=''):
    print(Fore.LIGHTMAGENTA_EX + mystr, end=end) 
    sys.stdout.flush()
    print(Fore.WHITE)

def printYellowStderr(mystr, end=''):
    print(Fore.YELLOW + mystr, end=end, file=sys.stderr)
    sys.stderr.flush()
    print(Fore.WHITE, file=sys.stderr)
