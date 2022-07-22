import src
import pygame

pygame.init()  # ensuring that everything we need will be initialised before starting

# Here we create the game window. The first argument is the native resolution the game runs at, and you can then add
# flags after that. The ones I put here allow us to have a bigger window without needing to scale everything up, and
# allow the user to resize the window as they like. Feel free to change the resolution if you feel that it's too small
screen = pygame.display.set_mode((160, 144), pygame.RESIZABLE | pygame.SCALED)

running = True

while running:
    # We generally use a while loop when making a game. Most of the game code should go here.
    screen.fill("skyblue")
    pygame.display.update()  # This function is called when everything render-related is done.
    # If you don't call this or pygame.display.flip, the screen won't show what you've drawn on it!
    # Events are how we manage player inputs (and others).
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # This one is, as you may have guessed, used when the user clicks on the "Close" button.
            # Generally we just close the window when we get an event of that type.
            running = False
            pygame.quit()


try:
    exit(0)
except NameError:
    raise SystemExit(0)
