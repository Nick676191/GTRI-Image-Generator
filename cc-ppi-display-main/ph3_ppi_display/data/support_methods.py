import json


def import_json(file: str) -> dict:
    """
    Helper method to import data from a file as a json object
    """
    output = {}
    try:
        with open(file, 'r', encoding='utf-8') as filereader:
            output = json.load(filereader)
    except ValueError as err:
        print("JSON parsing error: %s", err)
    return output