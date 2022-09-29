import discord
import importlib
import os
from .bot_config import BotConfig
from .config import Config
from types import ModuleType
from typing import Any,Dict,List,Optional,Type

DEFAULT_CONFIG_NAME = "config.json"

def import_recursive(module: ModuleType,out: List[ModuleType]) -> List[ModuleType]:
    if hasattr(module,"__all__"):
        for module_name in getattr(module,"__all__"):
            import_recursive(getattr(module,module_name),out)
    else:
        out.append(module)
    return out

class ModuleBase:
    def __init__(self,bot: 'Bot') -> None:
        pass
    
    async def init(self) -> None:
        pass
    
    async def postinit(self) -> None:
        pass

class Bot(discord.AutoShardedClient):
    def __init__(self,work_dir: str = os.getcwd(),config_name: str=DEFAULT_CONFIG_NAME):
        self._work_dir: str = work_dir
        self._config: Config = Config(config_path=os.path.join(work_dir,config_name))
        self._bot_config: BotConfig = self._config.get(BotConfig)
        self._loaded_modules: Dict[str,ModuleBase] = self._preload_modules()

        intents: discord.Intents = discord.Intents.none()
        for intent,value in self._bot_config.intents.items():
            assert hasattr(intents,intent), f"invalid intent '{intent}' present in config"
            setattr(intents,intent,bool(value))
        super().__init__(intents=intents,**self._bot_config.client_args)
    
    def _preload_modules(self) -> Dict[str,ModuleBase]:
        loaded_modules: Dict[str,ModuleBase] = {}
        for module_path in self._bot_config.enabled_modules:
            module_path_recursive: List[ModuleType] = []
            import_recursive(importlib.import_module(module_path),module_path_recursive)
            for module in module_path_recursive:
                module_name: str = module.__name__
                assert hasattr(module,"Module"), f"'{module_name}' is not a valid module"
                module_class: Type[ModuleBase] = getattr(module,"Module")
                loaded_modules[module_name] = module_class(self)
        return loaded_modules
    
    @property
    def config(self):
        return self._config

    @property
    def work_dir(self):
        return self._work_dir

    def get_module(self,module_name: str) -> Any:
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name]
        else:
            raise Exception(f"cannot find module '{module_name}'")

    async def start(self,token: str,*,reconnect: bool=True) -> None:
        for module_instance in self._loaded_modules.values():
            if hasattr(module_instance,"init") and callable(module_instance.init):
                await module_instance.init()
        for module_instance in self._loaded_modules.values():
            if hasattr(module_instance,"postinit") and callable(module_instance.postinit):
                await module_instance.postinit()
        await super().start(token,reconnect=reconnect)
    
    def run(self,token: Optional[str]=None,**_: Any) -> None:
        assert self._bot_config.token, "token missing from config"
        super().run(token or self._bot_config.token)