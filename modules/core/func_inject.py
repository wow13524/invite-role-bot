import asyncio
from modubot import ModuleBase
from typing import Any,Awaitable,Callable,Dict,List,TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot

Callback = Callable[...,Awaitable[None]]

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: Bot = bot
        self.groups: Dict[str,List[Callback]] = {}

    def inject(self,callback: Callback) -> None:
        callback_name: str = callback.__name__
        if callback_name not in self.groups:
            self.groups[callback_name] = []
            predefined: bool = False
            try:
                predefined = getattr(self.bot,callback_name)
            except:
                pass
            if predefined:
                self.inject(getattr(self.bot,callback_name))
        self.groups[callback_name].append(callback)
        group: List[Callback] = self.groups[callback_name]
        async def grouper(*args: Any) -> None:
            await asyncio.wait([x(*args) for x in group])
        setattr(self.bot,callback_name,grouper)