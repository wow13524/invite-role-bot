import aiosqlite
from os.path import join
from modubot import ModuleBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot
    from func_inject import Module as FuncInject

DEFAULT_DB_NAME = "data.db"

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: Bot = bot
        self.connection: aiosqlite.Connection
    
    async def init(self) -> None:
        self.connection = await aiosqlite.connect(join(self.bot.work_dir,DEFAULT_DB_NAME))
    
    async def postinit(self) -> None:
        func_inject: FuncInject = self.bot.get_module("modules.core.func_inject")
        func_inject.inject(self.close)
    
    async def close(self):
        await self.connection.close()