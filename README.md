## "A Totally Generic Platformer"

Hello there! This is our project for the summer code jam of Python Discord!
"A Totally Generic Platformer" by Old-Fashioned Orcs, is an online multiplayer game written in Python with [`pygame`](https://github.com/pygame/pygame).
The framework we chose to use for the client/server stuff is [`websockets`](https://github.com/aaugustin/websockets).
Also, we must warn you, don't expect much more than what the title says. It's your generic, average platformer, duh.


## Installation

If you want to play our game, simply download the package you need from [the latest release](https://github.com/smileyface12349/old-fashioned-orcs/releases/latest), then run the executable. (Internet connection required to start the game.)


For a manual installation :

1. [Clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) this repository.
2. Make sure you have [Python](https://www.python.org/downloads/) installed (version 3.10+).
3. While in the repo directory, run the following console command:

```bash
python3 -m pip install -r dev-requirements.txt
```

4. Then simply run the [__init__.py](__init__.py) file.


## Controls

- `←` and `→` to move right/left (WASD and ZQSD control schemes are supported as well).
- `↑` or `Space Bar` to jump.
- `R` if you experience a "pseudo-crash".
- `Return` or `Space Bar` for interactions.
- `ESC` key while playing will take you back to the menu, a second hit will exit the game.
