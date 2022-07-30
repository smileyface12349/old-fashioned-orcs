import logging


class GameAntiCheat:
    """Basic anticheat so that the server actually asserts what clients send him."""

    def __init__(self):
        pass

    async def ensure(self, event, player, game):
        """Checks an event for strange activity."""
        # Player/Event checks
        if event["unique_id"] != player.unique_id:
            logging.info("Failed unique_id check.")
            return True

        if event["nickname"] != player.nickname:
            logging.info("Failed nickname check.")
            return True

        if not isinstance(event["position"], list):
            logging.info("Wrong position type.")
            return True

        if len(event["position"]) != 2:
            logging.info("Positions list length is not 2.")
            return True

        if event["direction"] not in ["r", "l"]:
            logging.info("Invalid direction.")
            return True

        if event["position"][0] < 0 or event["position"][1] < 0:
            logging.info("Invalid position [negative].")
            return True

        if player.banned is not None and player.level is not None:
            if int(player.level) - int(event["level"]) > 1:
                logging.info("Failed the level check.")
                return True

            # This can also be triggered when the game teleports the player
            # In order to not ban the player we will keep track of how
            # many position violations occurred
            if not int(player.level) != int(event["level"]):
                # Skip position check when spawning and on level change.
                if abs(event["position"][0] - player.position[0]) > 20:
                    player.violations += 1
                    if player.violations > 15:
                        logging.info("Too many 'Invalid position X'")
                        return True
                if abs(event["position"][1] - player.position[1]) > 20:
                    player.violations += 1
                    if player.violations > 15:
                        logging.info("Too many 'Invalid position Y'")
                        return True

        # Player/Game checks
        if player not in game.players:
            logging.info("Player not in game.")
            return True

        if player.nickname not in game.nicknames:
            logging.info("Nickname not in game.")
            return True

        return False
