from pathlib import Path
import json


def store_entry(data, file) -> None:
    """ Saves the data to file """
    if not entry_file_exists(file):
        create_entry_file(file)

    with open(file, 'w') as f:
        json.dump(data, f, indent=4)


def get_entry(file):
    if entry_file_exists(file):
        with open(file, 'r') as f:
            file_str = f.read()
    else:
        file_str = ""

    return json.loads(file_str) if file_str else {}


def entry_file_exists(file_name) -> bool:
    """ Checks if the file at the path file_name exists"""

    file_path = Path(file_name)

    return file_path.exists()


def create_entry_file(file_name) -> None:
    """ Creates a file at file_name. Does not overwrite if file already exists """

    file_path = Path(file_name)
    file_path.touch()

