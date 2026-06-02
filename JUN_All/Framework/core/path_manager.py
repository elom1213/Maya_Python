import os
from pathlib import Path


class PathManager:

    def __init__(   self, 
                    root_file,
                    read_dir="0010_Src",
                    write_dir="0020_out",
                 ):

        self.root = Path(root_file).resolve().parent

        self._dirs = {
                        "read": read_dir,
                        "write": write_dir,
                    }

    def path(self, key, filename=""):
        return self.root / self._dirs[key] / filename
    
    @property
    def path_read(self):
        return self._dirs["read"]

    @property
    def path_write(self):
        return self._dirs["write"]
    
    @path_read.setter
    def path_read(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self._dirs["read"] = value

    @path_write.setter
    def path_write(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self._dirs["write"] = value

    @staticmethod
    def ensure_dir(file_path):

        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )