from .config import PropertyDict
from typing import Dict,List

class BotConfig(PropertyDict):
    intents: Dict[str,bool] = {}
    enabled_modules: List[str] = ["modules.core"]
    token: str = ""