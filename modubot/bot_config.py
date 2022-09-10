from .config import PropertyDict
from typing import Any,Dict,List

class BotConfig(PropertyDict):
    client_args: Dict[str,Any] = {}
    intents: Dict[str,bool] = {}
    enabled_modules: List[str] = ["modules.core"]
    token: str = ""