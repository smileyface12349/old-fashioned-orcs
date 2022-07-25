import asyncio
import threading

import pygame

if pygame.vernum[0] < 2:
    raise RuntimeError("Your version of Pygame is too old. Please install pygame 2.0.0 or higher to run the game")

pygame.init()  # ensuring that everything we need will be initialised before starting

# Here we create the game window. The first argument is the native resolution the game runs at, and you can then add
# flags after that. The ones I put here allow us to have a bigger window without needing to scale everything up, and
# allow the user to resize the window as they like. Feel free to change the resolution if you feel that it's too small
screen = pygame.display.set_mode((160, 144), pygame.RESIZABLE | pygame.SCALED)

import src.game  # Screw PEP 8 for this one. We need this import to be here, as convert_alpha needs an open window


game = src.game.Game()
clock = pygame.time.Clock()  # a framerate helper object.


class StoppableThread(threading.Thread):
    """
    Thread class with a stop() method.

    The thread itself has to check regularly for the stopped() condition.
    """

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        """Stop the running thread."""
        self._stop_event.set()

    def stopped(self):
        """Return is_set() response of thread."""
        return self._stop_event.is_set()


def echo_runner():
    """
    This function solely exists for the purpose of the threading.

    We ensure that the engine runs in parallel to the websocket.
    """
    asyncio.run(game.client.run())


comm_thread = StoppableThread(target=echo_runner, daemon=True)  # The connection thread.
# We make it "daemon" so that the full process stops when the window is closed.
# (If the thread is not daemon, we get a RuntimeError upon closing the window.)

running = True

comm_thread.start()  # Once we start the thread, it'll run as long as the game exists.

while running:
    # We generally use a while loop when making a game. Most of the game code should go here.
    screen.fill("skyblue")
    dt = clock.tick(60)  # this ensures that the game cannot run higher that 60FPS. We also get a delta time in ms.
    if not game.crashing:
        game.objects.update(dt)  # Auto update for every sprite, if the game has not "crashed"
    game.objects.draw(screen)  # We draw everything here
    pygame.display.update()  # This function is called when everything render-related is done.
    # If you don't call this or pygame.display.flip, the screen won't show what you've drawn on it!
    # Events are how we manage player inputs (and others).
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # This one is, as you may have guessed, used when the user clicks on the "Close" button.
            # Generally we just close the window when we get an event of that type.
            running = False
            pygame.quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                game.player.moving_left = True
            elif event.key == pygame.K_RIGHT:
                game.player.moving_right = True
            elif event.key == pygame.K_SPACE:
                game.player.jump()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                game.player.moving_left = False
            elif event.key == pygame.K_RIGHT:
                game.player.moving_right = False


# we stop it before we return an exit code, outside of the try block, to ensure the thread terminates in every case
# (Some implementations of Python might not define the "exit" builtin, hence this try-except clause.)
comm_thread.stop()
try:
    exit(0)
except NameError:
    raise SystemExit(0)
