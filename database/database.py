import sqlite3 as sql
from pathlib import Path
from typing import Optional
import os

class GameDB:
    def __init__(self, id: str):
        self.path = f'{Path(__file__).parent}/db/{id}.db'
        self.exists = os.path.exists(self.path)
        self.db = sql.connect(self.path)
        self.cursor = self.db.cursor()

    def create_table(self, overwrite=True):
        '''
        Attempts to open the db file.
        
        If create is set to True, the file will be created if it does not exist. 
        If False is returned, do not attempt to interact with the database with other methods.

        Parameters:
            create (bool, optional): Determines whether or not a new file should be created. Defaults to True.

        Returns:
            bool: Whether or not the file was successfully opened.
        '''
        if overwrite:
            self.cursor.execute('DROP TABLE IF EXISTS gamedb')
            self.db.commit()
        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS gamedb (
                state INTEGER PRIMARY KEY,
                remoteness INTEGER,
                value INTEGER
            )
            '''
        )
    
    def insert(self, table: dict[int, tuple[int, int]]):
        '''
        Attempts to insert the key, value pairs in the given dictionary into the database.

        Parameters:
            table (dict): The dictionary of values to insert.
            overwrite (bool, optional): Whether the database entries should be overwritten. Defaults to False.
        '''
        self.cursor.executemany(
            '''
            INSERT OR IGNORE INTO gamedb (state, remoteness, value)
            VALUES (?, ?, ?)
            ''',
            [(state, remoteness, value) for state, (remoteness, value) in table.items()]
        )
        self.db.commit()
    
    def get(self, state: int) -> Optional[tuple[int, int]]:
        '''
        Attempts to retrieve the remoteness for the given state from the database.

        Parameters:
            state (int): The (hashed) state of the position.
        
        Returns:
            Optional[tuple[int, int]]: Either the retrieved remoteness, or None if the key does not exist in the database.
        '''
        self.cursor.execute(
            '''
            SELECT remoteness, value FROM gamedb
            WHERE state = ?
            ''',
            (state,)
        )
        return self.cursor.fetchone()
        
    
    def get_all(self) -> list[tuple[int, int, int]]:
        self.cursor.execute('SELECT * FROM gamedb')
        return self.cursor.fetchall()

        
    
    def close(self):
        '''
        Updates the database with any changes made and closes it.
        '''
        self.db.commit()
        self.db.close()