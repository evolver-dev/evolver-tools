#!/usr/bin/env python3
"""cowsay — ASCII cow saying text.

Usage: cowsay "Hello World"
       echo "Hello" | cowsay
       cowsay -l                    # list all animals
       cowsay -f tux "Hello"       # use tux (penguin)

Supports multiple animals: cow, tux, dragon, bunny, cheese, daemon
Zero-dependency (stdlib only).
"""

import sys

ANIMALS = {}

# Cow
ANIMALS['cow'] = r"""
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
"""

ANIMALS['tux'] = r"""
        \   
         \   
            .--.
           |o_o |
           |:_/ |
          //   \ \
         (|     | )
        /'\_   _/`\
        \___)=(___/
"""

ANIMALS['dragon'] = r"""
        \                    / \  //\
         \    |\___/|      /   \//  \
              /0  0  \__  /    //  | \ \    
             /     /  \/_/    //   |  \  \  
             @_^_@'/   \/_   //    |   \   \ 
             //_^_/     \/_ //     |    \    \
          ( //) |        \///      |     \     \
        ( / /) _|_ /   )  //       |      \     _\
      ( // /) '/,_ _ _/  ( ; -.    |    _ _\.-~        .-~~~^-.
    (( / / )) ,-{        _      `-.|.-~-.           .~         `.
   (( // / ))  '/\      /                 ~-. _ .-~      .-~^-.  \
   (( /// ))      `.   {            }                   /      \  \
      (( / ))     .----~-.\        \-'                 .~         \  `. \^-.
                 ///.----..>        \             _ -~             `.  ^-`  ^-_
                   ///-._ _ _ _ _ _ _}^ - - - -~                     `-~ _-~^
"""

ANIMALS['bunny'] = r"""
        \   (
         \   )
            __(
           /  |
          /  /|
         /  / |
        (  (  |
         \  \ |
          \  \|
           \  \
            \  \
             \  \_
              \__,_)
"""

ANIMALS['cheese'] = r"""
        \
         \  ╔═══════════════╗
           ║  (•_•)        ║
           ║  <) )╯        ║
           ║   / \          ║
           ╚═══════════════╝
"""

ANIMALS['daemon'] = r"""
        \   
         \   
            \/\/
            |\/
            /\
           / _\
          / /  \
         /_/    \__
         \_\    /_/
          \_\  /_/
           \/_\/_/
            \/_/
"""


def make_speech(text, animal='cow'):
    lines = text.split('\n')
    max_len = max(len(l) for l in lines) if lines else 0
    width = min(max_len + 2, 60)

    if len(lines) == 1:
        speech = f"< {text} >"
    else:
        speech = []
        speech.append(f" {'_' * width}")
        for i, line in enumerate(lines):
            if i == 0:
                speech.append(f"/ {' ' * (width - 2)} \\" if max_len < width else f"/ {line:<{width-2}} \\")
            elif i == len(lines) - 1:
                speech.append(f"\\ {line:<{width-2}} /")
            else:
                speech.append(f"| {line:<{width-2}} |")
        speech.append(f" -{'-' * width}")
        speech = '\n'.join(speech)

    art = ANIMALS.get(animal, ANIMALS['cow'])
    return f"{speech}\n{art}"


def main():
    args = sys.argv[1:]
    animal = 'cow'

    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '-f' and i + 1 < len(args):
            animal = args[i + 1].lower()
            i += 2
        elif args[i] == '-l':
            print("Available animals:", ', '.join(sorted(ANIMALS.keys())))
            return
        elif args[i] in ('-h', '--help'):
            print(__doc__)
            return
        else:
            filtered.append(args[i])
            i += 1

    if filtered:
        text = ' '.join(filtered)
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("Usage: cowsay <text> or echo <text> | cowsay [-f animal]")
        print("       cowsay -l    (list animals)")
        return

    if animal not in ANIMALS:
        print(f"Unknown animal: {animal}. Use -l to list.", file=sys.stderr)
        sys.exit(1)

    print(make_speech(text, animal))


# === Auto-registration metadata ===
TOOL_META = {
    "name": "cowsay",
    "func": "main",
    "desc": 'ASCII cow saying text (cow/tux/dragon/bunny)',
}

if __name__ == '__main__':
    main()
