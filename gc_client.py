"""
Module for interacting with the GetCourse API.
Provides an asynchronous client for retrieving group and user data.
"""

import asyncio
import importlib
from urllib.parse import quote
from typing import List, Optional
import aiohttp  # type: ignore
import config  # type: ignore
from logger import logger  # type: ignore

class GetCourseClient:
    """Client for interacting with the GetCourse API."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._load_config()
        self._validate_config()

    def _load_config(self) -> None:
        """Loads configuration from config.py."""
        self.api_key = config.GC_API_KEY
        self.base_url = config.BASE_GC_API
        self.api_paths = {
            'fields': config.FIELDS_PATH,
            'items': config.ITEMS_PATH,
            'export_id': config.EXPORT_ID_PATH
        }
        self.fields = {
            'email': config.FIELD_EMAIL,
            'group_id': config.FIELD_GROUP_ID
        }
        self.wait_seconds = getattr(config, 'GC_WAIT_SECONDS', {'groups': 60, 'users': 10})
        self.max_retries = getattr(config, 'GC_MAX_RETRIES', 3)
        self.retry_delay = getattr(config, 'GC_RETRY_DELAY', 5)
        logger.debug("Configuration for GetCourse loaded")

    def _validate_config(self) -> None:
        """Validates the presence of required configuration fields."""
        required_fields = [
            'GC_API_KEY', 'BASE_GC_API', 'FIELDS_PATH', 'ITEMS_PATH',
            'EXPORT_ID_PATH', 'FIELD_EMAIL', 'FIELD_GROUP_ID'
        ]
        missing = [field for field in required_fields if not hasattr(config, field)]
        if missing:
            logger.error("Missing required configuration fields: %s", missing)
            raise ValueError(f"Missing configuration fields: {missing}")

    def reload_config(self) -> None:
        """Reloads configuration from config.py."""
        importlib.reload(config)
        self._load_config()
        logger.info("Configuration reloaded")

    async def start(self) -> None:
        """Initializes ClientSession."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            logger.debug("ClientSession created")

    async def close(self) -> None:
        """Closes ClientSession."""
        if self.session is not None:
            await self.session.close()
            self.session = None
            logger.debug("ClientSession closed")

    async def _get(self, endpoint: str, retry: int = 0) -> dict:
        """
        Performs a GET request to the GetCourse API with retries.
        
        Args:
            endpoint: Endpoint API.
            retry: Current attempt (for recursion).

        Returns:
            API response in JSON format.

        Raises:
            aiohttp.ClientResponseError: In case of HTTP-request error after all retries.
        """
        if self.session is None:
            await self.start()

        url = f"{self.base_url}{endpoint}"
        logger.debug("GET request to %s", url)

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug("Successful response from %s", url)
                return data
        except aiohttp.ClientResponseError as e:
            logger.warning("HTTP error %s on request %s: %s", e.status, url, e.message)
            if retry < self.max_retries and e.status in (429, 503):
                await asyncio.sleep(self.retry_delay)
                return await self._get(endpoint, retry + 1)
            raise
        except Exception as e:
            logger.error("Unknown error on request %s: %s", url, e)
            raise

    def _extract(self, path: str, data: dict) -> any:
        """
        Extracts data from a dictionary by a specified path.
        
        Args:
            path: Path in the format of 'key1.key2.key3'.
            data: Dictionary with data.

        Returns:
            Value at specified path.

        Raises:
            KeyError: If path does not exist.
        """
        try:
            for key in path.split("."):
                data = data[key]
            return data
        except KeyError as e:
            logger.error("Key %s not found in data at path %s", e, path)
            raise KeyError(f"Key {e} not found at path {path}") from e

    async def _get_export_data(self, export_id: str, wait_seconds: int) -> tuple[list, list]:
        """
        Retrieves export data after waiting.
        
        Args:
            export_id: Export ID.
            wait_seconds: Wait time in seconds.

        Returns:
            Typle (fields, items) with fields and items of export.
        """
        logger.info("Waiting %s seconds for export %s", wait_seconds, export_id)
        await asyncio.sleep(wait_seconds)
        data = await self._get(f"/exports/{export_id}?key={self.api_key}")
        fields = self._extract(self.api_paths['fields'], data)
        items = self._extract(self.api_paths['items'], data)
        logger.debug("Received fields: %s, items: %s", len(fields), len(items))
        return fields, items

    async def get_group_emails(self, group_id: int) -> List[str]:
        """
        Retrieves a list of user emails in a GetCourse group.
        
        Args:
            group_id: Group ID (should be > 0).

        Returns:
            List of user emails.

        Raises:
            ValueError: If group_id is invalid.
            ValueError: If field email is not found in export.
        """
        if not isinstance(group_id, int) or group_id <= 0:
            logger.error("Invalid group_id: %s", group_id)
            raise ValueError("group_id must be a positive integer")

        logger.info("Requesting emails for group %s", group_id)
        data = await self._get(f"/groups/{group_id}/users?key={self.api_key}")
        export_id = self._extract(self.api_paths['export_id'], data)
        fields, items = await self._get_export_data(export_id, self.wait_seconds['groups'])

        try:
            email_index = fields.index(self.fields['email'])
        except ValueError as exc:
            logger.warning("Field %s not found in fields", self.fields['email'])
            raise ValueError(f"Field '{self.fields['email']}' not found") from exc

        emails = [row[email_index] for row in items if len(row) > email_index and row[email_index]]
        logger.info("Found %s emails in group %s", len(emails), group_id)
        return emails

    async def get_user_group_ids_by_email(self, email: str) -> Optional[List[str]]:
        """
        Retrieves a list of group IDs for a user by their email.
        
        Args:
            email: User email.

        Returns:
            List of group IDs or None, if user is not found.

        Raises:
            ValueError: If field group_id is not found in export.
        """
        if not email or not isinstance(email, str):
            logger.error("Invalid email: %s", email)
            raise ValueError("email should be a valid string")

        logger.info("Requesting groups for email %s", email)
        encoded_email = quote(email)
        data = await self._get(f"/users?key={self.api_key}&email={encoded_email}&idgrouplist=id")
        export_id = self._extract(self.api_paths['export_id'], data)
        fields, items = await self._get_export_data(export_id, self.wait_seconds['users'])

        try:
            group_index = fields.index(self.fields['group_id'])
        except ValueError as exc:
            logger.error("Field %s not found in fields", self.fields['group_id'])
            raise ValueError(f"Field '{self.fields['group_id']}' not found") from exc

        if not items or len(items[0]) <= group_index:
            logger.info("Groups for email %s not found", email)
            return None

        group_ids = items[0][group_index] if items[0][group_index] else []
        logger.info("Found groups for email %s: %s", email, group_ids)
        return group_ids
