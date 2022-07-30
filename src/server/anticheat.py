import logging


class GameAntiCheat:
    """Basic anticheat so that the server actually asserts what client sends him."""

    def __init__(self):
        self.spawned = set()

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

        if event["direction"] not in ["r", "l"]:
            logging.info("Invalid direction.")
            return True

        if event["position"][0] < 0 or event["position"][1] < 0:
            logging.info("Invalid position [negative]")
            return True

        if player.banned is not None and player.level is not None:
            if int(player.level) - int(event["level"]) > 1:
                logging.info("Failed the level check.")
                return True
            if not int(player.level) != int(event["level"]):
                # Skip position check when spawning and on level change.
                if event["position"][0] - player.position[0] > 50:
                    logging.info("Invalid position [X-Axis]")
                    return True
                if event["position"][1] - player.position[1] > 50:
                    logging.info("Invalid position [Y-Axis]")
                    return True

        # Player/Game checks
        if player not in game.players:
            logging.info("Player not in game.")
            return True

        if player.nickname not in game.nicknames:
            logging.info("Nickname not in game.")
            return True

        self.spawned.add(player)
        return False
