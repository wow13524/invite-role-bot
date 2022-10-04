from discord.app_commands import CommandTree
from modubot import ModuleBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot
    from func_inject import Module as FuncInject

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self._bot: Bot = bot
        self._cmds_synced: bool = False
        self._cmd_tree: CommandTree[Bot]
    
    @property
    def cmd_tree(self) -> CommandTree['Bot']:
        return self._cmd_tree
    
    async def init(self) -> None:
        self._cmd_tree = CommandTree(self._bot)
    
    async def postinit(self) -> None:
        func_inject: FuncInject = self._bot.get_module("modules.core.func_inject")
        func_inject.inject(self.on_ready)
    
    async def on_ready(self):
        await self._bot.wait_until_ready()
        if not self._cmds_synced:
            await self._cmd_tree.sync()
            self._cmds_synced = True