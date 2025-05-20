"""
Module for managing the Telegram chat user database.
Provides the Database class for managing user data in SQLite.
"""

from datetime import datetime
from typing import Dict
import aiosqlite  # type: ignore

class Database:
    """Class for managing the user database in SQLite."""

    def __init__(self, path: str = "db.sqlite"):
        """
        Initializes the SQLite database.

        Args:
            path (str): Path to database file. Default is 'db.sqlite'.
        """
        self.path = path

    async def initialize(self) -> None:
        """Initializes the database and creates the users and scheduled_messages tables."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER,
                    user_id INTEGER,
                    email TEXT,
                    PRIMARY KEY (chat_id, user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT,
                    send_time REAL
                )
            """)
            await db.commit()

    async def is_duplicate(self, email: str) -> bool:
        """
        Checks if an email exists in the database.

        Args:
            email (str): Email for checking.

        Returns:
            bool: True, if email exists, otherwise False.
        """
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT 1 FROM users WHERE email = ?", (email,))
            return await cursor.fetchone() is not None

    async def add(self, user_id: int, email: str, chat_id: int) -> None:
        """
        Adds a user to the database.

        Args:
            user_id (int): User ID.
            email (str): User email.
            chat_id (int): Chat ID.
        """
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO users (chat_id, user_id, email) VALUES (?, ?, ?)",
                (chat_id, user_id, email)
            )
            await db.commit()

    async def remove(self, chat_id: int, user_id: int) -> None:
        """
        Removes a user from the database.

        Args:
            chat_id (int): Chat ID.
            user_id (int): User ID.
        """
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM users WHERE chat_id = ? AND user_id = ?", (chat_id, user_id,))
            await db.commit()

    async def get_users_by_chat_id(self, chat_id: int) -> Dict[str, str]:
        """
        Returns a dictionary of users for a specified chat.

        Args:
            chat_id (int): Char ID.

        Returns:
            dict: Dictionary in the format {user_id: email} for the specified chat or empty dictionary.
        """
        users = {}
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT user_id, email FROM users WHERE chat_id = ?",
                (chat_id,)
            )
            rows = await cursor.fetchall()
            for user_id, email in rows:
                users[str(user_id)] = email
        return users

    async def add_scheduled_message(self, user_id: int, message: str, send_time: datetime) -> None:
        """
        Adds a scheduled message to the database.

        Args:
            user_id (int): User ID.
            message (str): Message text.
            send_time (datetime): Time of message sending.
        """
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO scheduled_messages (user_id, message, send_time) VALUES (?, ?, ?)",
                (user_id, message, send_time.timestamp())
            )
            await db.commit()

    async def get_scheduled_messages(self) -> list:
        """
        Returns a list of all scheduled messages.

        Returns:
            list: List of dictionaries with fields user_id, message, send_time.
        """
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT user_id, message, send_time FROM scheduled_messages")
            rows = await cursor.fetchall()
            return [{"user_id": row[0], "message": row[1], "send_time": row[2]} for row in rows]

    async def remove_scheduled_message(self, user_id: int, send_time: float) -> None:
        """
        Removes a scheduled message from the database.

        Args:
            user_id (int): User ID.
            send_time (float): Time of message sending (timestamp).
        """
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "DELETE FROM scheduled_messages WHERE user_id = ? AND send_time = ?",
                (user_id, send_time)
            )
            await db.commit()
