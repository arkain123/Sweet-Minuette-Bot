import time
from termcolor import colored


def connected():
    important("Module Console_out connected")
    return 1


def log(out_message):
    base = f"{time.strftime('%H:%M:%S')} LOG:\t"
    print(colored(base + out_message, 'white'))


def important(out_message):
    base = f"{time.strftime('%H:%M:%S')} IMPORTANT:\t"
    print(colored(base + out_message, 'blue'))


def warning(out_message):
    base = f"{time.strftime('%H:%M:%S')} WARNING:\t"
    print(colored(base + out_message, 'yellow'))


def error(out_message):
    base = f"{time.strftime('%H:%M:%S')} ERROR:\t\t"
    print(colored(base + out_message, 'red'))
