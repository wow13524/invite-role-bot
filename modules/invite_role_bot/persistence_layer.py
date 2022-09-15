from sqlite3 import Row
from aiosqlite import Connection,Cursor
from discord import Guild,Invite,Object,PartialInviteChannel,PartialInviteGuild,Role
from discord.abc import GuildChannel
from discord.errors import NotFound
from modubot import ModuleBase
from typing import List,Optional,Tuple,TYPE_CHECKING,Union

if TYPE_CHECKING:
    from modubot import Bot
    from ..persistence.db_sqlite import Module as DBSQLite

InviteChannel = Optional[Union[GuildChannel,Object,PartialInviteChannel]]
InviteGuild = Optional[Union[Guild,Object,PartialInviteGuild]]

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self.bot: Bot = bot
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
    
    async def _raw_guild_exists(self,guild_id: int) -> bool:
        cur: Cursor = await self.connection.cursor()
        return await (await cur.execute("SELECT 1 FROM guilds WHERE id = ?;",[guild_id])).fetchone() is not None

    async def _raw_invite_exists(self,invite_code: str) -> bool:
        cur: Cursor = await self.connection.cursor()
        return await (await cur.execute("SELECT 1 FROM invites WHERE code = ?;",[invite_code])).fetchone() is not None

    async def _raw_invite_role_exists(self,invite_code: str,role_id: Optional[int]) -> bool:
        cur: Cursor = await self.connection.cursor()
        if role_id:
            return await (await cur.execute("SELECT 1 FROM roles WHERE id = ? AND invite_code = ?;",[role_id,invite_code])).fetchone() is not None
        else:
            return await self._raw_invite_exists(invite_code)
    
    async def _raw_add_guild(self,guild_id: int) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await self._raw_guild_exists(guild_id):
            await cur.execute("INSERT INTO guilds (id) VALUES (?);",[guild_id])
    
    async def _raw_remove_guild_if_unused(self,guild_id: int) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM invites WHERE guild_id = ?;",[guild_id])).fetchone():
            await cur.execute("DELETE FROM guilds WHERE id = ?;",[guild_id])
    
    async def _raw_add_invite(self,guild_id: int,invite_code: str,invite_uses: int) -> None:
        await self._raw_add_guild(guild_id)
        cur: Cursor = await self.connection.cursor()
        if not await self._raw_invite_exists(invite_code):
            await cur.execute("INSERT INTO invites (code,uses,guild_id) VALUES (?,?,?);",[invite_code,invite_uses,guild_id])
    
    async def _raw_remove_invite_if_unused(self,guild_id: int,invite_code: str) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM roles WHERE invite_code = ?;",[invite_code])).fetchone():
            await cur.execute("DELETE FROM invites WHERE code = ?;",[invite_code])
            await self._raw_remove_guild_if_unused(guild_id)

    async def _raw_get_invite_codes(self,guild_id: int) -> List[str]:
        cur: Cursor = await self.connection.cursor()
        return [x[0] for x in await (await cur.execute("SELECT code FROM invites WHERE guild_id = ?;",[guild_id])).fetchall()]
    
    async def _raw_get_invite_role_ids(self,invite_code: str) -> List[int]:
        cur: Cursor = await self.connection.cursor()
        return [x[0] for x in await (await cur.execute("SELECT id FROM roles WHERE invite_code = ?;",[invite_code])).fetchall()]
    
    async def _raw_add_invite_role(self,guild_id: int,invite_code: str,invite_uses: int,role_id: int) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await self._raw_invite_role_exists(invite_code,role_id):
            await self._raw_add_invite(guild_id,invite_code,invite_uses)
            await cur.execute("INSERT INTO roles (id,invite_code) VALUES (?,?);",[role_id,invite_code])
    
    async def _raw_remove_invite_role(self,guild_id: int,invite_code: str,role_id: Optional[int]) -> None:
        cur: Cursor = await self.connection.cursor()
        if role_id:
            await cur.execute("DELETE FROM roles WHERE invite_code = ? AND id = ?;",[invite_code,role_id])
        else:
            await cur.execute("DELETE FROM roles WHERE invite_code = ?;",[invite_code])
        await self._raw_remove_invite_if_unused(guild_id,invite_code)

    async def invite_role_exists(self,invite: Invite,role: Optional[Role]) -> bool:
        return await self._raw_invite_role_exists(invite.code,role.id if role else None)

    async def get_guild_ids(self) -> List[int]:
        cur: Cursor = await self.connection.cursor()
        return [int(x[0]) for x in await (await cur.execute("SELECT id FROM guilds;")).fetchall()]

    async def get_invite_codes(self,guild: Guild) -> List[str]:
        return await self._raw_get_invite_codes(guild.id)

    async def get_invites(self,guild: Guild) -> List[Invite]:
        invite_codes: List[str] = await self._raw_get_invite_codes(guild.id)
        invites: List[Invite] = []
        if guild.me.guild_permissions.manage_guild:
            if guild.vanity_url_code in invite_codes:
                vanity_invite: Optional[Invite] = await guild.vanity_invite()
                if vanity_invite:
                    invites.append(vanity_invite)
            invites += [invite for invite in await guild.invites() if invite.code in invite_codes]
        else:   #Slower fallback to still serve invites even without manage_guild
            for invite_code in invite_codes:
                try:
                    invites.append(await self.bot.fetch_invite(invite_code))
                except NotFound:
                    pass
        return invites

    async def get_invite_roles(self,guild: Guild,invite_code: str) -> Tuple[List[Role],List[Role]]:
        invite_role_ids: List[int] = await self._raw_get_invite_role_ids(invite_code)
        active_roles: List[Role] = []
        inactive_roles: List[Role] = []
        for role in guild.roles:
            if role.id in invite_role_ids:
                if role < guild.me.top_role:
                    active_roles.append(role)
                else:
                    inactive_roles.append(role)
            else:
                await self._raw_remove_invite_role(guild.id,invite_code,role.id)
        return active_roles,inactive_roles
    
    async def update_invite_uses(self,guild: Guild) -> List[Invite]:
        used_invites: List[Invite] = []
        cur: Cursor = await self.connection.cursor()
        if guild.me.guild_permissions.manage_guild:
            for invite in await self.get_invites(guild):
                saved_uses_row: Optional[Row] = await (await cur.execute("SELECT uses FROM invites WHERE code = ?;",[invite.code])).fetchone()
                if saved_uses_row and saved_uses_row[0] >= 0 and invite.uses != saved_uses_row[0]:
                    used_invites.append(invite)
                await cur.execute(
                    """
                    UPDATE invites SET
                        uses = ?
                    WHERE code = ?
                    """,
                    [invite.uses or -1,invite.code]
                )
        return used_invites

    async def add_invite_role(self,invite: Invite,role: Role) -> None:
        assert invite.guild
        await self._raw_add_invite_role(invite.guild.id,invite.code,invite.uses or -1,role.id)
    
    async def remove_invite_role(self,invite: Invite,role: Optional[Role]) -> None:
        assert invite.guild
        await self._raw_remove_invite_role(invite.guild.id,invite.code,role.id if role else None)