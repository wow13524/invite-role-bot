from discord import Forbidden,Game,Guild,Invite,Member,Role,Status
from modubot import ModuleBase
from tqdm import tqdm
from typing import List,Dict,Optional,TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot
    from .persistence_layer import Module as PersistenceLayer
    from ..core.func_inject import Module as FuncInject

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: Bot = bot
        self.persistence_layer: PersistenceLayer
        self.ready_guilds: Dict[int,bool] = {}
    
    async def postinit(self) -> None:
        func_inject: FuncInject = self.bot.get_module("modules.core.func_inject")
        self.persistence_layer = self.bot.get_module("modules.invite_role_bot.persistence_layer")

        func_inject.inject(self.on_guild_available)
        func_inject.inject(self.on_guild_join)
        func_inject.inject(self.on_guild_update)
        func_inject.inject(self.on_guild_role_update)
        func_inject.inject(self.on_guild_unavailable)
        func_inject.inject(self.on_member_join)
        func_inject.inject(self.on_ready)

    async def on_guild_available(self,guild: Guild) -> None:
        if guild.id in self.ready_guilds:
            await self.persistence_layer.update_invite_uses(guild)
            self.ready_guilds[guild.id] = True

    async def on_guild_join(self,guild: Guild) -> None:
        await self.persistence_layer.update_invite_uses(guild)
        self.ready_guilds[guild.id] = True

    async def on_guild_update(self,before: Guild,after: Guild) -> None:
        try:
            before_vanity: Optional[Invite] = await before.vanity_invite()
            after_vanity: Optional[Invite] = await after.vanity_invite()
            print(before_vanity,after_vanity)
            if after_vanity and after_vanity != before_vanity:
                await self.persistence_layer.update_invite_uses(after)
        except Forbidden:
            pass
    
    async def on_guild_role_update(self,before: Role,after: Role) -> None:
            await self.persistence_layer.update_invite_uses(after.guild)

    async def on_guild_unavailable(self,guild: Guild) -> None:
        if guild.id in self.ready_guilds:
            self.ready_guilds[guild.id] = False

    async def on_member_join(self,member: Member) -> None:
        if member.guild.id not in self.ready_guilds or not self.ready_guilds[member.guild.id] or not member.guild.me.guild_permissions.manage_guild or not member.guild.me.guild_permissions.manage_roles:
            return
        used_invites: List[Invite] = await self.persistence_layer.update_invite_uses(member.guild)
        if used_invites:
            assert len(used_invites) == 1, "Other invites used before join"
            used_invite: Invite = used_invites[0]
            await member.add_roles(*await self.persistence_layer.get_invite_roles(member.guild,used_invite.code),reason=f"Invite-roles for {used_invite.code}")

    async def on_ready(self) -> None:
        self.ready_guilds = {}
        await self.bot.change_presence(status=Status.idle,activity=Game(name="Starting up..."))
        guilds_map: Dict[int,Guild] = {guild.id:guild for guild in self.bot.guilds}
        for guild_id in tqdm(await self.persistence_layer.get_guild_ids(),desc="Updating Cached Guild Invites",unit="guilds"):
            guild: Optional[Guild] = guilds_map[guild_id]
            if guild and not guild.unavailable:
                await self.persistence_layer.update_invite_uses(guild)
                self.ready_guilds[guild.id] = True
        await self.bot.change_presence(status=Status.online,activity=Game(name="'/help' for help!"))