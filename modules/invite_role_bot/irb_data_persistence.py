from aiosqlite import Connection,Cursor
from discord import Invite,Role
from modubot import ModuleBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot
    from ..core.db_sqlite import Module as DBSQLite

class Module(ModuleBase):
    name = "irb_data_persistence"

    def __init__(self,bot: 'Bot') -> None:
        self.bot: 'Bot' = bot
        self.connection: Connection
    
    async def postinit(self) -> None:
        db_sqlite: DBSQLite = self.bot.get_module("db_sqlite")
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
    
    async def _add_guild(self,id: int) -> None:
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM guilds WHERE id = ?",[id])).fetchone():
            await cur.execute("INSERT INTO guilds (id) VALUES (?);",[id])
    
    async def _add_invite(self,invite: Invite) -> None:
        channel,guild = invite.channel,invite.guild
        if not channel or not guild:
            return
        await self._add_guild(guild.id)
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM invites WHERE id = ?",[invite.code])).fetchone():
            await cur.execute("INSERT INTO invites (id,uses,channel_id,guild_id) VALUES (?,?,?,?);",[invite.code,invite.uses or 0,channel.id,guild.id])
    
    async def add_invite_role(self,invite: Invite,role: Role) -> None:
        await self._add_invite(invite)
        cur: Cursor = await self.connection.cursor()
        if not await (await cur.execute("SELECT 1 FROM roles WHERE id = ? AND invite_id = ?",[role.id,invite.code])).fetchone():
            await cur.execute("INSERT INTO roles (id,invite_id) VALUES (?,?);",[role.id,invite.code])
        await self.connection.commit()