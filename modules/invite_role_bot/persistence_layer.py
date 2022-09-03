from aiosqlite import Connection,Cursor
from discord import Guild,Invite,Object,PartialInviteChannel,PartialInviteGuild,Role
from discord.abc import GuildChannel
from modubot import ModuleBase
from typing import List,Optional,TYPE_CHECKING,Union

if TYPE_CHECKING:
    from modubot import Bot
    from ..persistence.db_sqlite import Module as DBSQLite

InviteChannel = Optional[Union[GuildChannel,Object,PartialInviteChannel]]
InviteGuild = Optional[Union[Guild,Object,PartialInviteGuild]]

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: 'Bot' = bot
        self.connection: Connection
    
    async def postinit(self) -> None:
        db_sqlite: DBSQLite = self.bot.get_module("modules.persistence.db_sqlite")
        self.connection = db_sqlite.connection

        cur: Cursor = await self.connection.cursor()
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds (
                id integer PRIMARY KEY
            );
            """
        )
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS invites (
                id varchar(32) PRIMARY KEY,
                uses integer NOT NULL,
                channel_id integer NOT NULL,
                guild_id integer NOT NULL,
                FOREIGN KEY (guild_id) REFERENCES guilds (id)
            );
            """
        )
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id integer NOT NULL,
                invite_id varchar(32) NOT NULL,
                FOREIGN KEY (invite_id) REFERENCES invites (id)
            );
            """
        )
    
    async def _add_guild(self,guild: Guild) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM guilds WHERE id = ?;",[guild.id])).fetchone():
            await cur.execute("INSERT INTO guilds (id) VALUES (?);",[guild.id])
    
    async def _remove_guild_if_unused(self,guild: Guild) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM invites WHERE guild_id = ?;",[guild.id])).fetchone():
            await cur.execute("DELETE FROM guilds WHERE id = ?;",[guild.id])
    
    async def _add_invite(self,invite: Invite) -> None:
        channel: InviteChannel = invite.channel
        guild: InviteGuild = invite.guild
        if not isinstance(channel,GuildChannel) or not isinstance(guild,Guild):
            return
        await self._add_guild(guild)
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM invites WHERE id = ?;",[invite.code])).fetchone():
            await cur.execute("INSERT INTO invites (id,uses,channel_id,guild_id) VALUES (?,?,?,?);",[invite.code,invite.uses or 0,channel.id,guild.id])
    
    async def _remove_invite_if_unused(self,invite: Invite) -> None:
        guild: InviteGuild = invite.guild
        if not isinstance(guild,Guild):
            return
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM roles WHERE invite_id = ?;",[invite.code])).fetchone():
            await cur.execute("DELETE FROM invites WHERE id = ?;",[invite.code])
            await self._remove_guild_if_unused(guild)

    async def get_invite_ids(self,guild: Guild) -> List[str]:
        cur: Cursor = await self.connection.cursor()
        return [str(x[0]) for x in await (await cur.execute("SELECT id FROM invites WHERE guild_id = ?;",[guild.id])).fetchall()]

    async def invite_exists(self,invite: Invite) -> bool:
        cur: Cursor = await self.connection.cursor()
        return await (await cur.execute("SELECT 1 FROM invites WHERE id = ?;",[invite.code])).fetchone() is not None

    async def invite_role_exists(self,invite: Invite,role: Optional[Role]) -> bool:
        cur: Cursor = await self.connection.cursor()
        if role:
            return await (await cur.execute("SELECT 1 FROM roles WHERE id = ? AND invite_id = ?;",[role.id,invite.code])).fetchone() is not None
        else:
            return await self.invite_exists(invite)

    async def add_invite_role(self,invite: Invite,role: Role) -> None:
        await self._add_invite(invite)
        cur: Cursor = await self.connection.cursor()
        if not self.invite_role_exists(invite,role):
            await cur.execute("INSERT INTO roles (id,invite_id) VALUES (?,?);",[role.id,invite.code])
        await self.connection.commit()
    
    async def remove_invite_role(self,invite: Invite,role: Optional[Role]) -> None:
        cur: Cursor = await self.connection.cursor()
        if role:
            await cur.execute("DELETE FROM roles WHERE invite_id = ? AND id = ?;",[invite.code,role.id])
        else:
            await cur.execute("DELETE FROM roles WHERE invite_id = ?;",[invite.code])
        await self._remove_invite_if_unused(invite)