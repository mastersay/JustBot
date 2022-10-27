import json
from typing import Union
from os import path


class IDs(dict):
    def __init__(self, file_location: Union[str, bytes] = ".json"):
        if not path.isfile(file_location):
            file_location = "IDs.json"
            if not path.isfile(file_location):
                raise FileNotFoundError
        with open(file_location) as file:
            data = json.load(file)
        super(IDs, self).__init__(data)
