from pathlib import Path
from typing import Optional
import os
from .database import GameDB
from games import get_game
import indexed_gzip as igzip
import gzip

class ArrayDB(GameDB):
    def __init__(self, id: str, variant: str, ro: bool=True):
        '''
        Initialize the database for the given game id, variant id combination.
        Open as read only if ro=True
        '''
        game_res = get_game(id, variant)
        if game_res.is_err():
            raise ValueError(game_res.unwrap_err())

        file_name = f'{id}_{variant}'
        self.path = f'{Path(__file__).resolve().parents[2]}/db/{file_name}.db'
        self.exists = os.path.exists(self.path)

    def __del__(self):
        '''
        Finalize any transactions in the database and perform necessary cleanup 
        before deleting this object.
        '''
        pass

    def create_table(self, overwrite=True):
        '''
        Attempts to create a `gamedb` sqlite database within the file.
        
        If overwrite is set to True, the table will be overwritten if it already exists. 

        Parameters:
            overwrite (bool, optional): Determines whether or not the table should be overwritten. Defaults to True.
        '''
        pass
    
    def insert(self, table: dict[int, tuple[int, int]]):
        '''
        Attempts to insert the key, value pairs in the given dictionary into the database.

        Parameters:
            table (dict): The dictionary of values to insert.
            overwrite (bool, optional): Whether the database entries should be overwritten. Defaults to False.
        '''
        pass
    
    def get(self, state: int) -> Optional[tuple[int, int]]:
        '''
        Attempts to retrieve the remoteness for the given state from the database.

        Parameters:
            state (int): The (hashed) state of the position.
        
        Returns:
            Optional[tuple[int, int]]: Either the retrieved remoteness, or None if the key does not exist in the database.
        '''
        pass
        
    
    def get_all(self) -> list[tuple[int, int, int]]:
        pass

        
    
    def close(self):
        '''
        Updates the database with any changes made and closes it.
        '''
        pass