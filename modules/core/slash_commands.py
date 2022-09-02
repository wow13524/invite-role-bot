from discord.app_commands import CommandTree
from modubot import ModuleBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot
    from func_inject import Module as FuncInject

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: Bot = bot
        self._cmds_synced: bool = False
        self.cmd_tree: CommandTree[Bot]
    
    async def init(self) -> None:
        self.cmd_tree = CommandTree(self.bot)
    
    async def postinit(self) -> None:
        func_inject: FuncInject = self.bot.get_module("modules.core.func_inject")
        func_inject.inject(self.on_ready)
    
    async def on_ready(self):
        await self.bot.wait_until_ready()
        if not self._cmds_synced:
            await self.cmd_tree.sync()
            self._cmds_synced = True