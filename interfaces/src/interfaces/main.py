from .tui import TUI
import argparse

interface_types = {
    'tui' : TUI,
}

parser = argparse.ArgumentParser(description="GamesmanPy Interfaces cli")

parser.add_argument("interface_type", help="Interface Type", choices=['tui'])
args = parser.parse_args()

interface_type = args.interface_type

def main():
    if interface_type in interface_types.keys():
        Interface = interface_types[interface_type]
        interface_inst = Interface()
