import duckdb
import pandas
from pathlib import Path
from typing import Optional
import os
from games import get_game
from .database import GameDB

class DuckDB(GameDB):
    def __init__(self, id: str, variant: str, ro: bool=True):
        game_res = get_game(id, variant)
        if game_res.is_err():
            raise ValueError(game_res.unwrap_err())

        file_name = f'{id}_{variant}'
        self.path = f'{Path(__file__).resolve().parents[2]}/db/{file_name}.db'
        self.exists = os.path.exists(self.path)
        self.db = duckdb.connect(database=self.path, read_only=ro)

    def __del__(self):
        self.close()

    def create_table(self, overwrite=True):
        '''
        Attempts to create a `gamedb` sqlite database within the file.
        
        If overwrite is set to True, the table will be overwritten if it already exists. 

        Parameters:
            overwrite (bool, optional): Determines whether or not the table should be overwritten. Defaults to True.
        '''
        if overwrite:
            self.db.execute('DROP TABLE IF EXISTS gamedb')
        self.db.execute(
            '''
            CREATE TABLE IF NOT EXISTS gamedb (
                state BIGINT PRIMARY KEY,
                remoteness SMALLINT,
                value TINYINT
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
        
        df = pandas.DataFrame(
            [(state, remoteness, value) for state, (remoteness, value) in table.items()],
            columns=['state', 'remoteness', 'value']
        )
        self.db.register('game_solution', df)
        self.db.execute(
            '''
            INSERT INTO gamedb
            SELECT * FROM game_solution
            '''
        )
        self.db.unregister('game_solution')
    
    def get(self, state: int) -> Optional[tuple[int, int]]:
        '''
        Attempts to retrieve the remoteness for the given state from the database.

        Parameters:
            state (int): The (hashed) state of the position.
        
        Returns:
            Optional[tuple[int, int]]: Either the retrieved remoteness, or None if the key does not exist in the database.
        '''
        self.db.execute(
            '''
            SELECT remoteness, value FROM gamedb
            WHERE state = ?
            ''',
            [state]
        )
        return self.db.fetchone()
        
    
    def get_all(self) -> list[tuple[int, int, int]]:
        self.db.execute('SELECT * FROM gamedb')
        return self.db.fetchall()

        
    
    def close(self):
        '''
        Updates the database with any changes made and closes it.
        '''
        self.db.close()