# pyright: reportUnknownVariableType=false
# ^ the type of typeguard.check_type ironically can't be inferred :P

import json
from os import path
from typeguard import check_type
from typing import Any,Dict,Generator,Tuple,Union,get_origin,get_type_hints

class Config:
    def __init__(self,config_path: Union[str,'Config']) -> None:
        self.path: str = config_path if isinstance(config_path,str) else config_path.path
        self.exists: bool = path.exists(self.path)
        self.types: Dict[str,Any] = get_type_hints(self)

        if self.exists:
            with open(self.path) as f:
                self._load(json.load(f))
        else:
            self._load({})
            self.save()
            raise Exception(f"config does not exist, new one created at '{config_path}'")
    
    def _load(self,data: Dict[str,Any]) -> None:
        needs_saving: bool = False
        for attr,t in self.types.items():
            value: Any
            if attr not in data:
                print(f"field '{attr}' missing from config, adding")
                value = (get_origin(t) or t)()
                needs_saving = True
            else:
                value = data[attr]
                check_type(f"Config.{attr}",value,t)
            setattr(self,attr,value)
        if needs_saving:
            self.save()
    
    def save(self) -> None:
        output: Dict[str,Any] = dict(self)
        if self.exists:
            with open(self.path) as f:
                content: str = f.read()
                output.update(json.loads(content))
        with open(self.path,"w+") as f:
            json.dump(output,f,indent=4)
    
    def __iter__(self) -> Generator[Tuple[str,Any],None,None]:
        for attr in self.types:
            yield attr, getattr(self,attr)