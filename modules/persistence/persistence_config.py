from modubot import PropertyDict
from typing import Literal

class PersistenceConfig(PropertyDict):
    db_name: str = "data.db"
    auto_vacuum: Literal["NONE","FULL"] = "FULL"
    write_ahead_logging: bool = True