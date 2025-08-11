from pathlib import Path


def force_delete_path(path:str):
    try:
        Path(path).unlink(missing_ok=True)
    except:
        pass