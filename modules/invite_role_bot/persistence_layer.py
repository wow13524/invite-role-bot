from sqlite3 import Row
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
                code varchar(32) PRIMARY KEY,
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
                invite_code varchar(32) NOT NULL,
                FOREIGN KEY (invite_code) REFERENCES invites (id)
            );
            """
        )
    
    async def guild_exists(self,guild: Guild) -> bool:
        cur: Cursor = await self.connection.cursor()
        return await (await cur.execute("SELECT 1 FROM guilds WHERE id = ?;",[guild.id])).fetchone() is not None

    async def invite_exists(self,invite: Invite) -> bool:
        cur: Cursor = await self.connection.cursor()
        return await (await cur.execute("SELECT 1 FROM invites WHERE code = ?;",[invite.code])).fetchone() is not None

    async def invite_role_exists(self,invite: Invite,role: Optional[Role]) -> bool:
        cur: Cursor = await self.connection.cursor()
        if role:
            return await (await cur.execute("SELECT 1 FROM roles WHERE id = ? AND invite_code = ?;",[role.id,invite.code])).fetchone() is not None
        else:
            return await self.invite_exists(invite)

    async def _add_guild(self,guild: Guild) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await self.guild_exists(guild):
            await cur.execute("INSERT INTO guilds (id) VALUES (?);",[guild.id])
    
    async def _remove_guild_if_unused(self,guild: Guild) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM invites WHERE guild_id = ?;",[guild.id])).fetchone():
            await cur.execute("DELETE FROM guilds WHERE id = ?;",[guild.id])
    
    async def _add_invite(self,invite: Invite) -> None:
        channel: InviteChannel = invite.channel
        guild: InviteGuild = invite.guild
        assert isinstance(channel,GuildChannel)
        assert isinstance(guild,Guild)
        await self._add_guild(guild)
        cur: Cursor = await self.connection.cursor()
        if not await self.invite_exists(invite):
            await cur.execute("INSERT INTO invites (code,uses,channel_id,guild_id) VALUES (?,?,?,?);",[invite.code,invite.uses or 0,channel.id,guild.id])
    
    async def _remove_invite_if_unused(self,invite: Invite) -> None:
        guild: InviteGuild = invite.guild
        assert isinstance(guild,Guild)
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM roles WHERE invite_code = ?;",[invite.code])).fetchone():
            await cur.execute("DELETE FROM invites WHERE code = ?;",[invite.code])
            await self._remove_guild_if_unused(guild)

    async def get_invite_codes(self,guild: Guild) -> List[str]:
        cur: Cursor = await self.connection.cursor()
        return [str(x[0]) for x in await (await cur.execute("SELECT code FROM invites WHERE guild_id = ?;",[guild.id])).fetchall()]
    
    async def get_invites(self,guild: Guild) -> List[Invite]:
        invite_codes: List[str] = await self.get_invite_codes(guild)
        return [invite for invite in await guild.invites() if invite.code in invite_codes]
    
    async def get_invite_role_ids(self,invite: Invite) -> List[int]:
        cur: Cursor = await self.connection.cursor()
        return [x[0] for x in await (await cur.execute("SELECT id FROM roles WHERE invite_code = ?;",[invite.code])).fetchall()]
    
    async def get_invite_roles(self,invite: Invite) -> List[Role]:
        guild: InviteGuild = invite.guild
        assert isinstance(guild,Guild)
        invite_role_ids: List[int] = await self.get_invite_role_ids(invite)
        return [role for role in guild.roles if role.id in invite_role_ids]
    
    async def update_invite_uses(self,guild: Guild) -> List[Invite]:
        used_invites: List[Invite] = []
        cur: Cursor = await self.connection.cursor()
        for invite in await guild.invites():
            saved_uses_row: Optional[Row] = await (await cur.execute("SELECT uses FROM invites WHERE code = ?;",[invite.code])).fetchone()
            if saved_uses_row and invite.uses != saved_uses_row[0]:
                used_invites.append(invite)
            await cur.execute(
                """
                UPDATE invites SET
                    uses = ?
                WHERE code = ?
                """,
                [invite.uses,invite.code]
            )
        return used_invites

    async def add_invite_role(self,invite: Invite,role: Role) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await self.invite_role_exists(invite,role):
            await self._add_invite(invite)
            await cur.execute("INSERT INTO roles (id,invite_code) VALUES (?,?);",[role.id,invite.code])
        await self.connection.commit()
    
    async def remove_invite_role(self,invite: Invite,role: Optional[Role]) -> None:
        cur: Cursor = await self.connection.cursor()
        if role:
            await cur.execute("DELETE FROM roles WHERE invite_code = ? AND id = ?;",[invite.code,role.id])
        else:
            await cur.execute("DELETE FROM roles WHERE invite_code = ?;",[invite.code])
        await self._remove_invite_if_unused(invite)