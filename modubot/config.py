# pyright: reportUnknownVariableType=false
# ^ the type of typeguard.check_type ironically can't be inferred :P

import json
from os import path
from typeguard import check_type
from typing import Any,List,Dict,Generator,Literal,Optional,Tuple,Type,TypeVar,Union,get_origin,get_type_hints

T = TypeVar("T",bound="PropertyDict")

class TypedProperties:
    def __init__(self):
        self.types: Dict[str,type] = get_type_hints(self)
    
    def __iter__(self) -> Generator[Tuple[str,Any],None,None]:
        for attr in self.types:
            value: Any = getattr(self,attr)
            if isinstance(value,TypedProperties):
                value = dict(value)
            yield attr, value

class PropertyDict(TypedProperties):
    def __init__(self,missing_fields: List[str],data: Dict[str,Any],path: str) -> None:
        super().__init__()
        missing_fields += [field for field in self.types if field not in data]

        for attr,tp in self.types.items():
            subpath: str = f"{path}.{attr}"
            value: Any = getattr(self.__class__,attr) if attr not in data else data[attr]
            if isinstance(value,PropertyDict):
                value = dict(value)
            origin: Optional[type] = get_origin(tp)
            if origin == list or origin == dict:
                value = value.copy()
            elif origin == Literal:
                pass
            elif issubclass(tp,PropertyDict):
                value = tp(missing_fields,value,subpath)
            check_type(subpath,value,tp)
            setattr(self,attr,value)

class Config(TypedProperties):
    def __init__(self,config_path: Union[str,'Config']) -> None:
        self.types: Dict[str,type] = {}
        self.path: str = config_path if isinstance(config_path,str) else config_path.path
        self.exists: bool = path.exists(self.path)

    def get(self,config_type: Type[T]) -> T:
        config_name: str = config_type.__name__
        if hasattr(self,config_name):
            return getattr(self,config_name)
        data: Dict[str,Any] = {}
        if self.exists:
            with open(self.path) as f:
                config: Dict[str,Any] = json.load(f)
                if config_name in config:
                    data = config[config_name]
        missing_fields: List[str] = []
        self.types[config_name] = config_type
        properties: T = config_type(missing_fields,data,self.__class__.__name__)
        setattr(self,config_name,properties)
        if missing_fields:
            self._save()
        return properties
    
    def _save(self) -> None:
        output: Dict[str,Any] = {}
        if self.exists:
            with open(self.path) as f:
                content: str = f.read()
                output.update(json.loads(content))
        output.update(dict(self))
        with open(self.path,"w+") as f:
            json.dump(output,f,indent=4)
        self.exists = True