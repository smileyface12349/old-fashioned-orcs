import sqlite3


class GameDatabase:
    """This class handles the save/load of the player's progress in our database."""

    def __init__(self):
        con = sqlite3.connect("./players.db")
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS players
            ([unique_id] TEXT, [level] INT)
            """
        )

    async def save(self):
        """This method saves the data using `unique_id`"""
        # TODO => Create the actual save method using unique_id (unique_id needs to be stored client-side as well)
        pass

    async def load(self):
        """This method load the data using `unique_id`"""
        # TODO => Create the actual load method using unique_id (unique_id needs to be stored client-side as well)
        pass

    async def reset(self):
        """This method reseets the data using `unique_id`"""
        # TODO => Create the actual reset method that will update the entry in database
        pass
