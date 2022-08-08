import logging


class GameAntiCheat:
    """Basic anticheat so that the server actually asserts what clients send him."""

    def __init__(self):
        pass
    
    @staticmethod
    def __check_if_list(lst):
        """Checks for weird/bad position/velocity lists"""
        if not isinstance(lst, list):
            logging.info("Wrong type.")
            return False
        if len(lst) != 2:
            logging.info("Wrong list size.")
            return False
        return True

    async def ensure(self, event, player, game):
        """Checks an event for strange activity."""
        # Player/Event checks
        if event["unique_id"] != player.unique_id:
            logging.info("Failed unique_id check.")
            return True

        if event["nickname"] != player.nickname:
            logging.info("Failed nickname check.")
            return True

        if not self.__check_if_list(event["position"]):
            return True

        if not self.__check_if_list(event["velocity"]):
            return True

        if event["direction"] not in ["r", "l"]:
            logging.info("Invalid direction.")
            return True

        if event["position"][0] < 0 or event["position"][1] < 0:
            logging.info("Invalid position [negative].")
            return True

        if event["velocity"][0] < 0 or event["velocity"][0] > 1:
            logging.info("Invalid velocity [x].")
            return True

        if event["velocity"][1] < 0 or event["velocity"][1] > 6:
            logging.info("Invalid velocity [y].")
            return True

        if player.banned is not None and player.level is not None:
            if int(player.level) - int(event["level"]) > 1:
                logging.info("Failed the level check.")
                return True

        # Player/Game checks
        if player not in game.players:
            logging.info("Player not in game.")
            return True

        if player.nickname not in game.nicknames:
            logging.info("Nickname not in game.")
            return True

        return False
