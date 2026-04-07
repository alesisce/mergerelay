import json, os
from os import PathLike
from typing import Any

class Config(object): 
    def __init__(self, program_path: str | PathLike, name: str) -> None:
        self.data = {}
        self.folder_path = os.path.join(program_path, "config")
        
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
        
        self.file_path = os.path.join(self.folder_path, name)
        if not os.path.exists(self.file_path):
            self.__save__() # Creamos el archivo
        self.__load__() # Cargamos el archivo
    
    def __save__(self) -> None:
        with open(self.file_path, "w") as file:
            json.dump(
                obj=self.data, 
                fp=file,
                indent=4 # Hacerlo muy bonito :)
            )
    
    def __load__(self) -> None:
        try:
            with open(self.file_path, "r") as file:
                self.data = json.load(
                    fp=file
                )
        except:
            self.data = {}
            self.__save__() # Si no existe se crea con __save__


    def set_key(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.__save__() # Guardamos

    def get_key(self, key: str, default: Any = None) -> Any:
        if not key in self.data: return default
        return self.data[key]

    def remove_key(self, key: str) -> None:
        if not key in self.data: raise KeyError(key)
        del self.data[key]
        self.__save__()