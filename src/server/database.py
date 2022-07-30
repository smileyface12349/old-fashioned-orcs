import sqlite3


class GameDatabase:
    """This class handles the save/load of the player's progress in our database."""

    def __init__(self):
        self.con = sqlite3.connect("./players.db")
        self.cur = self.con.cursor()
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS players
            ([unique_id] TEXT, [level] INT)
            """
        )
        self.con.commit()

    async def save(self, player):
        """This method saves player's progress using `unique_id`"""
        self.cur.execute(f"SELECT * FROM players WHERE unique_id = '{player.unique_id}'")
        list = [list for list in self.cur.fetchall()]
        if not list and player.level is not None:
            self.cur.execute("INSERT INTO players (unique_id,level) VALUES (?, ?)", (player.unique_id, player.level))
            self.con.commit()
        elif list:
            # Entry already in database.
            for i in list:
                old_level = int(i[1])
            if old_level < player.level:
                self.cur.execute(f"DELETE FROM players WHERE unique_id IN ('{player.unique_id}')")
                self.cur.execute(
                    "INSERT INTO players (unique_id,level) VALUES (?, ?)", (player.unique_id, player.level)
                )
                self.con.commit()

    async def load(self, unique_id):
        """This method load player's level using `unique_id`"""
        self.cur.execute(f"SELECT level FROM players WHERE unique_id = '{unique_id}'")
        list = [list for list in self.cur.fetchall()]
        for i in list:
            return i[0]

    async def delete(self, player):
        """This method resets player's level using `unique_id`"""
        self.cur.execute(f"DELETE FROM players WHERE unique_id IN ('{player.unique_id}')")
        self.con.commit()

    async def show_all(self):
        """Prints everything, for testing only"""
        self.cur.execute("SELECT * FROM players")
        list = [list for list in self.cur.fetchall()]
        return list
