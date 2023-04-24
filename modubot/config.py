# pyright: reportUnknownVariableType=false
# ^ the type of typeguard.check_type ironically can't be inferred :P

import json
from os import path
from typeguard import check_type
from typing import Any,List,Dict,Generator,Literal,Tuple,Type,TypeVar,Union,cast,get_args,get_origin,get_type_hints

T = TypeVar("T",bound="PropertyDict")

def _get_raw_origin(tp: Type[Any]) -> type:
    return get_origin(tp) or tp

def _parse_value(value: Any,missing_fields: List[str],tp: type,subpath: str) -> Any:
    origin: type = _get_raw_origin(tp)
    if isinstance(value,PropertyDict):
        value = dict(value)
    if origin == dict:
        value = value.copy()
    elif origin == list:
        value = [_parse_value(x,missing_fields,get_args(tp)[0],f"{subpath}[{i}]") for i,x in enumerate(value)]
    elif origin == Any or origin == Literal or origin == Union:
        pass
    elif issubclass(tp,PropertyDict):
        value = tp(missing_fields,value,subpath)
    return value

class TypedProperties:
    def __init__(self):
        self._types: Dict[str,type] = get_type_hints(self.__class__)
    
    def __iter__(self) -> Generator[Tuple[str,Any],None,None]:
        for attr,tp in self._types.items():
            value: Any = getattr(self,attr)
            if isinstance(value,TypedProperties):
                value = dict(value)
            elif isinstance(value,list) and issubclass(_get_raw_origin(get_args(tp)[0]),TypedProperties):
                value = list(map(dict,cast(List[TypedProperties],value)))
            yield attr, value

class PropertyDict(TypedProperties):
    def __init__(self,missing_fields: List[str],data: Dict[str,Any],path: str) -> None:
        super().__init__()
        missing_fields += [field for field in self._types if field not in data]

        for attr,tp in self._types.items():
            subpath: str = f"{path}.{attr}"
            value: Any = data[attr] if attr in data else None if type(None) in get_args(tp) else getattr(self.__class__,attr)
            value = _parse_value(value,missing_fields,tp,subpath)
            check_type(subpath,value,tp)
            setattr(self,attr,value)

class Config(TypedProperties):
    def __init__(self,config_path: Union[str,'Config']) -> None:
        self._types: Dict[str,type] = {}
        self._path: str = config_path if isinstance(config_path,str) else config_path.path

    @property
    def exists(self):
        return path.exists(self._path)

    @property
    def path(self):
        return self._path

    def get(self,config_type: Type[T]) -> T:
        config_name: str = config_type.__name__
        if hasattr(self,config_name):
            return getattr(self,config_name)
        data: Dict[str,Any] = {}
        if self.exists:
            with open(self._path) as f:
                config: Dict[str,Any] = json.load(f)
                if config_name in config:
                    data = config[config_name]
        missing_fields: List[str] = []
        self._types[config_name] = config_type
        properties: T = config_type(missing_fields,data,self.__class__.__name__)
        setattr(self,config_name,properties)
        if missing_fields:
            self._save()
        return properties
    
    def _save(self) -> None:
        output: Dict[str,Any] = {}
        if self.exists:
            with open(self._path) as f:
                content: str = f.read()
                output.update(json.loads(content))
        output.update(dict(self))
        with open(self._path,"w+") as f:
            json.dump(output,f,indent=4)