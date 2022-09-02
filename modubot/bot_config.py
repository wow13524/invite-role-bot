from .config import Config
from typing import Dict,List

class BotConfig(Config):
    intents: Dict[str,bool]
    enabled_modules: List[str]
    token: str