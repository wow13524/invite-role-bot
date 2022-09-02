from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .bot import Bot

class ModuleBase:
    name: str

    def __init__(self,bot: 'Bot') -> None:
        pass
    
    async def init(self) -> None:
        pass
    
    async def postinit(self) -> None:
        pass