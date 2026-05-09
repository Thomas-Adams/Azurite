import datetime
from pathlib import Path


def get_created(file: Path) -> datetime.datetime:
    try:
        return datetime.datetime.fromtimestamp(file.stat().st_ctime)
    except AttributeError:
        return datetime.datetime.now()
