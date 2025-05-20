"""
Telegram bot module for managing chat access.

Handles join requests, verifies emails via the GetCourse API, 
manages the user database, and performs daily access checks.
"""

import asyncio
import importlib
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types  # type: ignore
from aiogram.filters import Command  # type: ignore
from aiogram.exceptions import TelegramAPIError  # type: ignore
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from gc_client import GetCourseClient  # type: ignore
from database import Database  # type: ignore
from logger import logger  # type: ignore
import config  # type: ignore

# Initialization of the bot and dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
gc_client = GetCourseClient()
email_futures = {}
db = Database()
scheduler = AsyncIOScheduler(timezone="Asia/Almaty")  # Global scheduler
CHECK_ALL_CHATS_JOB_ID = "1"

@dp.message(Command("update_config"))
async def update_config(message: types.Message) -> None:
    """
    Updates the bot configuration and scheduled task upon admin command.

    Args:
        message: Input message with a command.
    """
    logger.debug("Received /update_config command from %s in chat %s", message.from_user.id, message.chat.id)
    if message.from_user.id not in config.ADMIN_IDS:
        logger.warning("Unauthorized config update attempt by %s", message.from_user.id)
        await message.answer("Forbidden.")
        return
    try:
        logger.debug("Starting configuration update")
        importlib.reload(config)
        logger.debug("Configuration reloaded")
        gc_client.reload_config()
        logger.debug("gc_client configuration updated")
        
        # Remove old task check_all_chats
        scheduler.remove_job(CHECK_ALL_CHATS_JOB_ID)
        logger.debug("Old check_all_chats task removed")
        
        # Add new task with new configs
        scheduler.add_job(
            check_all_chats,
            CronTrigger(hour=config.CHECK_TIME_HOUR, minute=config.CHECK_TIME_MIN, timezone="Asia/Almaty"),
            id=CHECK_ALL_CHATS_JOB_ID,
            replace_existing=True
        )
        logger.debug("New check_all_chats task added")
        
        logger.info("Configuration and scheduled task successfully updated")
        await message.answer("Configuration and scheduled task updated")
    except Exception as e:
        logger.error("Error updating configuration or scheduled task: %s", e)
        await message.answer("Error updating configuration or scheduled task")

@dp.chat_join_request()
async def handle_join_request(request: types.ChatJoinRequest) -> None:
    """
    Processes a chat join request.

    Requests email, checks for duplicates and access via GetCourse, 
    and approves or declines the request.

    Args:
        request: Chat join request object.
    """
    user = request.from_user
    chat_id = request.chat.id
    logger.info("Join request from %s (%s) to chat %s", user.full_name, user.id, chat_id)

    try:
        await bot.send_message(user.id, config.MESSAGES["hello"], parse_mode="Markdown")
        logger.info("Sent welcome message to user %s", user.id)
    except TelegramAPIError as e:
        logger.warning("Failed to send welcome message to user %s: %s", user.id, e)
        return

    for attempt in range(2):
        email = await wait_for_email(user.id)
        logger.info("Received email %s from user %s (attempt %s)", email, user.id, attempt + 1)

        if await db.is_duplicate(email):
            await bot.decline_chat_join_request(chat_id, user.id)
            await bot.send_message(user.id, config.MESSAGES["is_duplicate"], parse_mode="Markdown")
            logger.info("Email %s already registered, request declined", email)
            return

        if await check_and_add_user(chat_id, user.id, email):
            return

        if attempt == 0:
            await bot.send_message(user.id, config.MESSAGES["try2"], parse_mode="Markdown")
            logger.info("Requested another email attempt for %s", user.id)

    await bot.decline_chat_join_request(chat_id, user.id)
    await bot.send_message(user.id, config.MESSAGES["is_not_access"], parse_mode="Markdown")
    logger.info("Request %s declined after two failed attempts", user.id)

@dp.message()
async def catch_email(message: types.Message) -> None:
    """
    Handles incoming messages with emails from users.

    Args:
        message: Incoming message.
    """
    user_id = message.from_user.id
    if user_id in email_futures and not email_futures[user_id].done():
        email = message.text.strip()
        email_futures[user_id].set_result(email)
        logger.info("Received email %s from user %s", email, user_id)

async def wait_for_email(user_id: int, timeout: int = 120) -> str:
    """
    Waits for email input from a user with a specified timeout.

    Args:
        user_id: User ID.
        timeout: Timeout in seconds.

    Returns:
        str: Entered email or empty string.
    """
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    email_futures[user_id] = future

    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for email from user %s", user_id)
        return ""
    finally:
        email_futures.pop(user_id, None)

async def check_and_add_user(chat_id: int, user_id: int, email: str) -> bool:
    """
    Verifies user access by email and adds them to the chat and database if access is granted.

    Args:
        chat_id: Chat ID.
        user_id: User ID.
        email: User email.

    Returns:
        bool: True, if join request is approved, otherwise False.
    """
    try:
        group_ids = await gc_client.get_user_group_ids_by_email(email)
        logger.info("User groups for %s: %s", email, group_ids)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Error verifying email %s via GetCourse: %s", email, e)
        return False

    if not group_ids:
        logger.info("User %s has no groups in GetCourse", email)
        return False

    # Searching for a group with current chat_id
    allowed_groups = []
    for group_name, group_data in config.CHAT_IDS_GROUPS.items():
        if chat_id in group_data["chat_ids"]:
            allowed_groups = group_data["gc_group_ids"]
            logger.debug(
                "Found group %s for chat %s with GetCourse groups: %s"
                group_name, chat_id, allowed_groups
            )
            break
    else:
        logger.debug("Chat %s not found in CHAT_IDS_GROUPS", chat_id)
        return False

    if any(str(group_id) in group_ids for group_id in allowed_groups):
        try:
            await bot.approve_chat_join_request(chat_id, user_id)
            await bot.send_message(user_id, config.MESSAGES["is_access"], parse_mode="Markdown")
            await db.add(user_id, email, chat_id)
            logger.info("User %s (%s) approved in chat %s", user_id, email, chat_id)
            return True
        except TelegramAPIError as e:
            logger.error("Error approving request %s in chat %s: %s", user_id, chat_id, e)
    return False

async def send_delayed_message(user_id: int, message: str, send_time: float) -> None:
    """
    Sends a scheduled message to a user and removes it from the database.

    Args:
        user_id: User ID.
        message: Message Text.
        send_time: Time of message sending (timestamp).
    """
    try:
        await bot.send_message(user_id, message, parse_mode="Markdown")
        logger.info(
            "Sent scheduled message to user %s about access expiration", 
            user_id
            )
        await db.remove_scheduled_message(user_id, send_time)
        logger.debug("Removed task for user %s from database", user_id)
    except TelegramAPIError as e:
        logger.warning("Failed to send scheduled message to user %s: %s", user_id, e)

async def check_all_chats() -> None:
    """
    Performs daily access checks for users in chats.

    Verifies emails via GetCourse and removes users without access.
    
    Saves scheduled notifications in SQLite for sending with a 1-second interval 
    starting at config.SEND_TIME the same day.
    """
    logger.info("Starting daily access check")
    for group_name, group_data in config.CHAT_IDS_GROUPS.items():
        chat_ids = group_data["chat_ids"]
        group_ids = group_data["gc_group_ids"]
        logger.info("Checking group %s with chats %s", group_name, chat_ids)

        try:
            emails = []
            for group_id in group_ids:
                try:
                    group_emails = await gc_client.get_group_emails(int(group_id))
                    emails.extend(group_emails)
                    logger.debug("Received emails for group %s: %s", group_id, len(group_emails))
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.warning("Error retrieving emails for group %s: %s", group_id, e)
            emails = list(set(emails))
            logger.info("Group %s: collected %s unique emails", group_name, len(emails))
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error processing group %s: %s", group_name, e)
            continue

        # Initial send time
        today = datetime.now().date()
        base_send_time = datetime.combine(today, datetime.strptime(config.SEND_TIME, "%H:%M").time())
        offset_seconds = 0

        for chat_id in chat_ids:
            chat_users = await db.get_users_by_chat_id(int(chat_id))
            logger.info("Chat %s: found %s users in database", chat_id, len(chat_users))

            for user_id_str, email in list(chat_users.items()):
                user_id = int(user_id_str)
                if email not in emails:
                    try:
                        await bot.ban_chat_member(chat_id, user_id)
                        await bot.unban_chat_member(chat_id, user_id)
                        await db.remove(chat_id, user_id)
                        logger.info(
                            "User %s (%s) removed from chat %s due to lack of access"
                            user_id, email, chat_id
                        )
                        # Increment send time by 1 second for each user
                        send_time = base_send_time + timedelta(seconds=offset_seconds)
                        await db.add_scheduled_message(user_id,
                                                       config.MESSAGES["is_end_access"],
                                                       send_time)
                        logger.debug(
                            "Saved scheduled message for user %s at %s"
                            user_id, send_time
                        )
                        offset_seconds += 1
                    except TelegramAPIError as e:
                        logger.warning(
                            "Failed to remove user %s from chat %s: %s"
                            user_id, chat_id, e
                        )

async def process_scheduled_messages() -> None:
    """
    Background task for sending scheduled messages.

    Checks the database every 10 seconds for precise message sending at the specified time.
    """
    while True:
        messages = await db.get_scheduled_messages()
        current_time = datetime.now().timestamp()
        for msg in messages:
            if abs(current_time - msg["send_time"]) <= 5:  # Margin of 5 seconds
                await send_delayed_message(msg["user_id"], msg["message"], msg["send_time"])
        await asyncio.sleep(10)  # Check every 10 seconds

async def main() -> None:
    """Starts the bot, scheduler, and initializes the database."""
    await db.initialize()  # Initialization of SQLite database
    scheduler.add_job(
        check_all_chats,
        CronTrigger(hour=config.CHECK_TIME_HOUR, minute=config.CHECK_TIME_MIN, timezone="Asia/Almaty"),
        id=CHECK_ALL_CHATS_JOB_ID,
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started, daily check scheduled for {config.CHECK_TIME_HOUR}:{config.CHECK_TIME_MIN}")
    asyncio.create_task(process_scheduled_messages())
    logger.info("Background task for sending messages started")
    await dp.start_polling(bot)
    logger.info("Bot started and running in polling mode")

if __name__ == "__main__":
    asyncio.run(main())
