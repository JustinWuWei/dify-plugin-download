from pathlib import Path


def delete_file(path:str):
    try:
        Path(path).unlink(missing_ok=True)
    except:
        pass