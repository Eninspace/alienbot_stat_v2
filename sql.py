import sqlite3

class db:
    def __init__(self, db):
        self.con = sqlite3.connect(db)
        self.cur = self.con.cursor()

    def query(self, sql, args):
        self.cur.execute(sql, args)
        self.con.commit()
        return self.cur

    def __del__(self):
        self.con.close()
