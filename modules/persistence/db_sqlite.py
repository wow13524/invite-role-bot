from aiosqlite import Connection,Cursor,connect
from os.path import join
from modubot import ModuleBase
from typing import TYPE_CHECKING
from .persistence_config import PersistenceConfig

if TYPE_CHECKING:
    from modubot import Bot
    from ..core.func_inject import Module as FuncInject

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self._bot: Bot = bot
        self._config: PersistenceConfig = self._bot.config.get(PersistenceConfig)
        self._connection: Connection
    
    @property
    def connection(self) -> Connection:
        return self._connection
    
    async def cursor(self) -> Cursor:
        return await self.connection.cursor()
    
    async def init(self) -> None:
        self._connection = await connect(join(self._bot.work_dir,self._config.db_name),isolation_level=None)
        cur: Cursor = await self.cursor()
        await cur.execute(f"PRAGMA auto_vacuum = {self._config.auto_vacuum};")
        await cur.execute("VACUUM;")
        if self._config.write_ahead_logging:
            await cur.execute("PRAGMA journal_mode = WAL;")
    
    async def postinit(self) -> None:
        func_inject: FuncInject = self._bot.get_module("modules.core.func_inject")
        func_inject.inject(self.close)
    
    async def close(self):
        await self._connection.close()