from aiosqlite import Cursor
from discord import Guild,Invite,Object,PartialInviteChannel,PartialInviteGuild,Role
from discord.abc import GuildChannel
from modubot import ModuleBase
from typing import List,Optional,TYPE_CHECKING,Union

if TYPE_CHECKING:
    from modubot import Bot
    from .persistence_layer import Module as PersistenceLayer

InviteChannel = Optional[Union[GuildChannel,Object,PartialInviteChannel]]
InviteGuild = Optional[Union[Guild,Object,PartialInviteGuild]]

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: 'Bot' = bot
        self.persistence_layer: PersistenceLayer
    
    async def postinit(self) -> None:
        self.persistence_layer = self.bot.get_module("modules.invite_role_bot.persistence_layer")
    
    async def on_ready(self) -> None:
        for guild in self.bot.guilds:
            if await self.persistence_layer.guild_exists(guild):
                guild_invites: List[Invite] = await guild.invites()