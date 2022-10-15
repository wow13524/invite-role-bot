import discord
import importlib
import os
from .bot_config import BotConfig
from .config import Config
from types import ModuleType
from typing import Any,Dict,List,Optional,Type

DEFAULT_CONFIG_NAME = "config.json"

def _import_recursive(*,module: ModuleType,out: List[ModuleType]) -> List[ModuleType]:
    if hasattr(module,"__all__"):
        for module_name in getattr(module,"__all__"):
            _import_recursive(module=getattr(module,module_name),out=out)
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
    def __init__(self,config_name: str=DEFAULT_CONFIG_NAME,*,work_dir: str = os.getcwd()):
        self._work_dir: str = work_dir
        self._config: Config = Config(config_path=os.path.join(work_dir,config_name))
        self._bot_config: BotConfig = self._config.get(BotConfig)
        self._loaded_modules: Dict[str,ModuleBase] = self._preload_modules()
        
        assert "intents" not in self._bot_config.client_args, "intents must be defined in BotConfig.intents, not BotConfig.client_args"
        parsed_client_args: Dict[str,Any] = {}
        for option,raw_value in self._bot_config.client_args.items():
            if type(raw_value) == dict and "_class" in raw_value:
                raw_value: Dict[str,Any] = raw_value
                assert hasattr(discord,raw_value["_class"]), f"invalid class '{raw_value['_class']}' present in config"
                value_class: type = getattr(discord,raw_value["_class"])
                option_value: Any
                if "_attr" in raw_value:
                    assert hasattr(value_class,raw_value["_attr"]), f"invalid attribute '{raw_value['_class']}.{raw_value['_attr']}' present in config"
                    option_value = getattr(value_class,raw_value["_attr"])
                    assert raw_value["_class"] in str(type(option_value)), f"attribute '{raw_value['_class']}.{raw_value['_attr']}' present in config is not of type {raw_value['class']}"
                else:
                    option_value = value_class() if not hasattr(value_class,"none") else getattr(value_class,"none")()
                    for k,v in raw_value.items():
                        if not k.startswith("_"):
                            setattr(option_value,k,v)
                parsed_client_args[option] = option_value
                continue
            parsed_client_args[option] = raw_value
        
        intents: discord.Intents = discord.Intents.none()
        for intent,value in self._bot_config.intents.items():
            assert hasattr(intents,intent), f"invalid intent '{intent}' present in config"
            setattr(intents,intent,bool(value))
        super().__init__(intents=intents,**parsed_client_args)
    
    def _preload_modules(self) -> Dict[str,ModuleBase]:
        loaded_modules: Dict[str,ModuleBase] = {}
        for module_path in self._bot_config.enabled_modules:
            module_path_recursive: List[ModuleType] = []
            _import_recursive(module=importlib.import_module(module_path),out=module_path_recursive)
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

    async def setup_hook(self) -> None:
        for module_instance in self._loaded_modules.values():
            if hasattr(module_instance,"init") and callable(module_instance.init):
                await module_instance.init()
        for module_instance in self._loaded_modules.values():
            if hasattr(module_instance,"postinit") and callable(module_instance.postinit):
                await module_instance.postinit()
    
    async def start(self,token: Optional[str]=None,*,reconnect: bool=True) -> None:
        token = token or self._bot_config.token
        assert token, "token missing"
        await super().start(token,reconnect=reconnect)
    
    def run(self,token: Optional[str]=None,**_: Any) -> None:
        token = token or self._bot_config.token
        assert token, "token missing"
        super().run(token,**_)