import src.game
import pygame

pygame.init()  # ensuring that everything we need will be initialised before starting

# Here we create the game window. The first argument is the native resolution the game runs at, and you can then add
# flags after that. The ones I put here allow us to have a bigger window without needing to scale everything up, and
# allow the user to resize the window as they like. Feel free to change the resolution if you feel that it's too small
screen = pygame.display.set_mode((160, 144), pygame.RESIZABLE | pygame.SCALED)

game = src.game.Game()
clock = pygame.time.Clock()  # a framerate helper object.

running = True

while running:
    # We generally use a while loop when making a game. Most of the game code should go here.
    screen.fill("skyblue")
    dt = clock.tick(60)  # this ensures that the game cannot run higher that 60FPS. We also get a delta time in ms.
    game.objects.update(dt)  # Auto update for every sprite
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
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                game.player.moving_left = False
            elif event.key == pygame.K_RIGHT:
                game.player.moving_right = False


try:
    exit(0)
except NameError:
    raise SystemExit(0)
