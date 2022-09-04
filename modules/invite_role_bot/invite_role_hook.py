from discord import Forbidden,Guild,Invite,Member
from modubot import ModuleBase
from typing import List,Optional,TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot
    from .persistence_layer import Module as PersistenceLayer
    from ..core.func_inject import Module as FuncInject

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: 'Bot' = bot
        self.persistence_layer: PersistenceLayer
    
    async def postinit(self) -> None:
        func_inject: FuncInject = self.bot.get_module("modules.core.func_inject")
        self.persistence_layer = self.bot.get_module("modules.invite_role_bot.persistence_layer")

        func_inject.inject(self.on_guild_update)
        func_inject.inject(self.on_member_join)
        func_inject.inject(self.on_ready)
    
    async def on_guild_update(self,before: Guild,after: Guild) -> None:
        try:
            before_vanity: Optional[Invite] = await before.vanity_invite()
            after_vanity: Optional[Invite] = await after.vanity_invite()
            print(before_vanity,after_vanity)
            if after_vanity and after_vanity != before_vanity:
                await self.persistence_layer.update_invite_uses(after)
        except Forbidden:
            pass

    async def on_member_join(self,member: Member) -> None:
        used_invites: List[Invite] = await self.persistence_layer.update_invite_uses(member.guild)
        assert len(used_invites) == 1, "Other invites used before join"
        used_invite: Invite = used_invites[0]
        await member.add_roles(*await self.persistence_layer.get_invite_roles(used_invite),reason=f"Invite-roles for {used_invite.code}")

    async def on_ready(self) -> None:
        for guild in self.bot.guilds:
            await self.persistence_layer.update_invite_uses(guild)