import pygame

if pygame.vernum[0] < 2:
    raise RuntimeError("Your version of Pygame is too old. Please install pygame 2.0.0 or higher to run the game")

pygame.init()  # ensuring that everything we need will be initialised before starting

# Here we create the game window. The first argument is the native resolution the game runs at, and you can then add
# flags after that. The ones I put here allow us to have a bigger window without needing to scale everything up, and
# allow the user to resize the window as they like. Feel free to change the resolution if you feel that it's too small
screen = pygame.display.set_mode((160, 144), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("A Totally Generic Platformer by the Old-Fashioned Orcs")

import src.game  # noqa: E402

# Screw PEP 8 for this one. We need this import to be here, as convert_alpha needs an open window

game = src.game.Game()
clock = pygame.time.Clock()  # a framerate helper object.


while game.running:
    # We generally use a while loop when making a game. Most of the game code should go here.
    screen.fill("skyblue" if game.level in (0, 5, 6, 7) or game.showing_gui else "darkgray")
    dt = clock.tick(60)  # this ensures that the game cannot run higher that 60FPS. We also get a delta time in ms.

    if game.showing_gui:
        if game.inputting_nickname:
            game.render_ean_prompt(screen)
        elif game.showing_title:
            game.render_title(screen)
        game.gui.update(dt)
        game.gui.draw(screen)
    else:
        if not game.gui and not game.crashing:
            if game.tiles:
                game.tile_timer.update(dt)
                game.update_objects(dt)  # Auto update for every sprite, if the game has not "crashed"
                game.draw_objects(screen)  # We draw everything here
            else:
                screen.blit(src.game.loading, (0, 0))
            if not game.client.running:
                screen.blit(src.game.disconnected, (0, 0))
            game.trigger_man.check_triggers(dt)
        elif game.crashing:
            screen.blit(src.game.crash, (0, 0))
        else:
            game.gui.update()
            game.gui.draw(screen)

    pygame.display.update()  # This function is called when everything render-related is done.
    # If you don't call this or pygame.display.flip, the screen won't show what you've drawn on it!
    # Events are how we manage player inputs (and others).

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # This one is, as you may have guessed, used when the user clicks on the "Close" button.
            # Generally we just close the window when we get an event of that type.
            game.running = False
            src.game.mixer.unload()
            pygame.quit()

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for btn in game.gui:
                if isinstance(btn, src.game.gui.Button) and btn.rect.collidepoint(event.pos):
                    btn.click()

        elif event.type == src.game.solid.SWITCH_PRESSED:
            game.switchs_man.spawn(event.id)
            game.switchd_man.destroy(event.id)
            game.switcht_man.toggle(event.id, True)

        elif event.type == src.game.solid.SWITCH_RELEASED:
            game.switcht_man.toggle(event.id, False)

        elif event.type == pygame.KEYDOWN:
            if not game.showing_gui:
                if not game.gui:
                    # Allow for ZQSD and WASD control schemes.
                    if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_q]:
                        game.player.moving_left = True
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        game.player.moving_right = True
                    elif event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_z, pygame.K_w]:
                        game.player.jump()
                    elif event.key == pygame.K_ESCAPE:
                        game.showing_gui = True
                        game.showing_title = True
                        if game.crashing:
                            src.game.game_crash.stop()
                        game.gui.add(src.game.gui.Button((48, 90), "Play", game.start))
                        game.gui.add(src.game.gui.Button((110, 90), "Reset", game.del_cache))
                        game.gui.add(src.game.gui.Button((80, 110), "Exit Game", game.quit))
                        game.gui.add(src.game.gui.EmojiButton((148, 10), "♬", game.sound_on_off))
                        game.client.stop()
                        break
                    elif event.key == pygame.K_f:
                        game.showing_gui = True
                        if game.level not in (5, 6, 7):
                            game.gui.add(src.game.gui.Button((80, 40), "Skip this level", game.load_next))
                        if game.level != 0:
                            game.gui.add(src.game.gui.Button((80, 65), "Previous level", game.load_previous))
                        game.gui.add(src.game.gui.Button((80, 90), "Keep playing", game.go_back))
                        game.gui.add(src.game.gui.EmojiButton((148, 10), "♬", game.sound_on_off))
                        break
                    elif event.key == pygame.K_r and game.crashing:
                        if game.sound:
                            src.game.mixer.unpause()
                        game.gui.empty()
                        game.read_map(f"maps/level{game.level}.tmx")
                        src.game.game_crash.stop()
                        game.crashing = False
                else:
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        for tbox in game.gui:
                            if len(tbox.parts_list) > 1 and tbox.part_index < len(tbox.parts_list):
                                tbox.part_index += 1
                            else:
                                tbox.kill()
                                if game.trigger_man.current_trigger is not None:
                                    game.trigger_man.current_trigger.update_evt()
            else:
                if event.key == pygame.K_ESCAPE:
                    game.running = False
                    src.game.mixer.unload()
                    pygame.quit()
                if game.inputting_nickname:
                    if event.key == pygame.K_BACKSPACE:
                        inpt = list(spr for spr in game.gui if isinstance(spr, src.game.gui.TextInput))[0]
                        if inpt.text:
                            inpt.text = inpt.text[:-1]
                    elif event.key == pygame.K_RETURN:
                        for i in game.gui:
                            if i.text:
                                i.kill()
                            else:
                                break
                        game.inputting_nickname = False
                        game.showing_gui = False
                        game.client.start()
                        break

        elif event.type in [pygame.TEXTEDITING, pygame.TEXTINPUT] and game.inputting_nickname:
            print(event.text)
            for i in game.gui:
                i.fetch(event.text)

        elif event.type == pygame.KEYUP and not game.showing_gui:
            if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_q]:
                game.player.moving_left = False
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                game.player.moving_right = False


if game.client.running:
    try:
        game.client.stop()
    except AttributeError:
        pass

try:
    exit(0)
except NameError:
    raise SystemExit(0)
