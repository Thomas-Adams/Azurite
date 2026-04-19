import datetime
from enum import Enum
from pathlib import Path


class ImageQuality(str, Enum):
    ungenuegend = 5
    mangelhaft = 4
    ausreichend = 3
    befriedigend = 2
    gut = 1
    sehr_gut = 0


def get_created(file: Path) -> datetime.datetime:
    try:
        return datetime.datetime.fromtimestamp(file.stat().st_ctime)
    except AttributeError:
        return datetime.datetime.now()
