from sqlite3 import Row
from aiosqlite import Cursor
from cachetools import TTLCache
from discord import Guild,Invite,Object,PartialInviteChannel,PartialInviteGuild,Role
from discord.abc import GuildChannel
from discord.errors import NotFound
from modubot import ModuleBase
from typing import Dict,List,Optional,Tuple,TYPE_CHECKING,Union

if TYPE_CHECKING:
    from modubot import Bot
    from ..persistence.db_sqlite import Module as DBSQLite

InviteChannel = Optional[Union[GuildChannel,Object,PartialInviteChannel]]
InviteGuild = Optional[Union[Guild,Object,PartialInviteGuild]]

class Module(ModuleBase):
    def __init__(self,bot: 'Bot') -> None:
        self._bot: Bot = bot
        self._cached_invites: TTLCache[int,List[Invite]] = TTLCache(maxsize=512,ttl=30)
        self._db_sqlite: DBSQLite
    
    async def postinit(self) -> None:
        self._db_sqlite: DBSQLite = self._bot.get_module("modules.persistence.db_sqlite")

        cur: Cursor = await self._db_sqlite.cursor()
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
        cur: Cursor = await self._db_sqlite.cursor()
        return await (await cur.execute("SELECT 1 FROM guilds WHERE id = ?;",[guild_id])).fetchone() is not None

    async def _raw_invite_exists(self,invite_code: str) -> bool:
        cur: Cursor = await self._db_sqlite.cursor()
        return await (await cur.execute("SELECT 1 FROM invites WHERE code = ?;",[invite_code])).fetchone() is not None

    async def _raw_invite_role_exists(self,invite_code: str,role_id: Optional[int]) -> bool:
        cur: Cursor = await self._db_sqlite.cursor()
        if role_id:
            return await (await cur.execute("SELECT 1 FROM roles WHERE id = ? AND invite_code = ?;",[role_id,invite_code])).fetchone() is not None
        else:
            return await self._raw_invite_exists(invite_code)
    
    async def _raw_add_guild(self,guild_id: int) -> None:
        cur: Cursor = await self._db_sqlite.cursor()
        if not await self._raw_guild_exists(guild_id):
            await cur.execute("INSERT INTO guilds (id) VALUES (?);",[guild_id])
    
    async def _raw_remove_guild_if_unused(self,guild_id: int) -> None:
        cur: Cursor = await self._db_sqlite.cursor()
        if not await (await cur.execute("SELECT 1 FROM invites WHERE guild_id = ?;",[guild_id])).fetchone():
            await cur.execute("DELETE FROM guilds WHERE id = ?;",[guild_id])
    
    async def _raw_add_invite(self,guild_id: int,invite_code: str,invite_uses: int) -> None:
        await self._raw_add_guild(guild_id)
        cur: Cursor = await self._db_sqlite.cursor()
        if not await self._raw_invite_exists(invite_code):
            await cur.execute("INSERT INTO invites (code,uses,guild_id) VALUES (?,?,?);",[invite_code,invite_uses,guild_id])
    
    async def _raw_remove_invite_if_unused(self,guild_id: int,invite_code: str) -> None:
        cur: Cursor = await self._db_sqlite.cursor()
        if not await (await cur.execute("SELECT 1 FROM roles WHERE invite_code = ?;",[invite_code])).fetchone():
            await cur.execute("DELETE FROM invites WHERE code = ?;",[invite_code])
            await self._raw_remove_guild_if_unused(guild_id)

    async def _raw_get_invite_codes(self,guild_id: int) -> List[str]:
        cur: Cursor = await self._db_sqlite.cursor()
        return [x[0] for x in await (await cur.execute("SELECT code FROM invites WHERE guild_id = ?;",[guild_id])).fetchall()]
    
    async def _raw_get_invite_role_ids(self,invite_code: str) -> List[int]:
        cur: Cursor = await self._db_sqlite.cursor()
        return [x[0] for x in await (await cur.execute("SELECT id FROM roles WHERE invite_code = ?;",[invite_code])).fetchall()]
    
    async def _raw_add_invite_role(self,guild_id: int,invite_code: str,invite_uses: int,role_id: int) -> None:
        cur: Cursor = await self._db_sqlite.cursor()
        if not await self._raw_invite_role_exists(invite_code,role_id):
            await self._raw_add_invite(guild_id,invite_code,invite_uses)
            await cur.execute("INSERT INTO roles (id,invite_code) VALUES (?,?);",[role_id,invite_code])
    
    async def _raw_remove_invite_role(self,guild_id: int,invite_code: str,role_id: Optional[int]) -> None:
        cur: Cursor = await self._db_sqlite.cursor()
        if role_id:
            await cur.execute("DELETE FROM roles WHERE invite_code = ? AND id = ?;",[invite_code,role_id])
        else:
            await cur.execute("DELETE FROM roles WHERE invite_code = ?;",[invite_code])
        await self._raw_remove_invite_if_unused(guild_id,invite_code)

    async def invite_exists(self,invite_code: str) -> bool:
        return await self._raw_invite_exists(invite_code)

    async def invite_role_exists(self,invite_code: str,role: Optional[Role]) -> bool:
        return await self._raw_invite_role_exists(invite_code,role.id if role else None)

    async def get_guild_ids(self) -> List[int]:
        cur: Cursor = await self._db_sqlite.cursor()
        return [int(x[0]) for x in await (await cur.execute("SELECT id FROM guilds;")).fetchall()]

    async def get_invite_codes(self,guild: Guild) -> List[str]:
        return await self._raw_get_invite_codes(guild.id)

    async def cache_guild_invites(self,guild: Guild) -> None:
        self._cached_invites[guild.id] = []
        if guild.me.guild_permissions.manage_guild:
            if guild.vanity_url:
                try:
                    vanity_invite: Optional[Invite] = await guild.vanity_invite()
                    if vanity_invite:
                        self._cached_invites[guild.id].append(vanity_invite)
                except NotFound:
                    pass
            self._cached_invites[guild.id] += await guild.invites()
            #print(guild)
        else:   #Slower fallback to still serve invites even without manage_guild
            for invite_code in await self._raw_get_invite_codes(guild.id):
                try:
                    self._cached_invites[guild.id].append(await self._bot.fetch_invite(invite_code,with_counts=False,with_expiration=False))
                except NotFound:
                    pass
    
    async def cache_guild_invites_add(self,guild: Guild,invite: Invite) -> None:
        if guild.id in self._cached_invites:
            self._cached_invites[guild.id].append(invite)
        else:
            await self.cache_guild_invites(guild)
    
    async def cache_guild_invites_remove(self,guild: Guild,invite: Invite) -> None:
        if guild.id in self._cached_invites and invite in self._cached_invites[guild.id]:
            self._cached_invites[guild.id].remove(invite)
        else:
            await self.cache_guild_invites(guild)
    
    async def get_cached_guild_invites(self,guild: Guild) -> List[Invite]:
        if guild.id not in self._cached_invites:
            await self.cache_guild_invites(guild)
        return self._cached_invites[guild.id]

    async def get_invites(self,guild: Guild,cached: bool=True) -> List[Invite]:
        invite_codes: List[str] = await self._raw_get_invite_codes(guild.id)
        if invite_codes:
            if guild.id not in self._cached_invites or not cached:
                await self.cache_guild_invites(guild)
            invites: List[Invite] = await self.get_cached_guild_invites(guild)
            matched_invites: List[Invite] = []
            if guild.vanity_url_code in invite_codes:
                vanity_invite: Optional[Invite] = await guild.vanity_invite()
                if vanity_invite:
                    matched_invites.append(vanity_invite)
            matched_invites += [invite for invite in invites if invite.code in invite_codes]
            return matched_invites
        return []

    async def get_invite_roles(self,guild: Guild,invite_code: str) -> Tuple[List[Role],List[Role]]:
        invite_role_ids: List[int] = await self._raw_get_invite_role_ids(invite_code)
        role_id_map: Dict[int,Role] = {role.id: role for role in guild.roles}
        active_roles: List[Role] = []
        inactive_roles: List[Role] = []
        for role_id in invite_role_ids:
            if role_id in role_id_map:
                role: Role = role_id_map[role_id]
                if role < guild.me.top_role:
                    active_roles.append(role)
                else:
                    inactive_roles.append(role)
            else:
                await self._raw_remove_invite_role(guild.id,invite_code,role_id)
        return active_roles,inactive_roles
    
    async def update_invite_uses(self,guild: Guild) -> List[Invite]:
        used_invites: List[Invite] = []
        cur: Cursor = await self._db_sqlite.cursor()
        if guild.me.guild_permissions.manage_guild:
            for invite in await self.get_invites(guild,False):
                saved_uses_row: Optional[Row] = await (await cur.execute("SELECT uses FROM invites WHERE code = ?;",[invite.code])).fetchone()
                if saved_uses_row and invite.uses > saved_uses_row[0]:
                    used_invites.append(invite)
                await cur.execute(
                    """
                    UPDATE invites SET
                        uses = ?
                    WHERE code = ?
                    """,
                    [invite.uses or 0,invite.code]
                )
        return used_invites

    async def add_invite_role(self,invite: Invite,role: Role) -> None:
        assert invite.guild
        await self._raw_add_invite_role(invite.guild.id,invite.code,invite.uses or -1,role.id)
    
    async def remove_invite_role(self,guild: Guild,invite_code: str,role: Optional[Role]) -> None:
        await self._raw_remove_invite_role(guild.id,invite_code,role.id if role else None)