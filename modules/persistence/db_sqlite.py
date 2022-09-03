import aiosqlite
from os.path import join
from modubot import ModuleBase
from typing import TYPE_CHECKING
from .persistence_config import PersistenceConfig

if TYPE_CHECKING:
    from modubot import Bot
    from ..core.func_inject import Module as FuncInject

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: Bot = bot
        self.config: PersistenceConfig = self.bot.config.get(PersistenceConfig)
        self.connection: aiosqlite.Connection
    
    async def init(self) -> None:
        self.connection = await aiosqlite.connect(join(self.bot.work_dir,self.config.db_name),isolation_level=None)
        await self.connection.execute(f"PRAGMA auto_vacuum = {self.config.auto_vacuum};")
        await self.connection.execute("VACUUM;")
        if self.config.write_ahead_logging:
            await self.connection.execute("PRAGMA journal_mode = WAL;")
    
    async def postinit(self) -> None:
        func_inject: FuncInject = self.bot.get_module("modules.core.func_inject")
        func_inject.inject(self.close)
    
    async def close(self):
        await self.connection.close()