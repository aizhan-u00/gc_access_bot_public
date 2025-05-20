# Telegram Access Bot

## Overview
This project is a Telegram bot designed to manage access to Telegram chats based on user membership in specific GetCourse groups. The bot processes chat join requests, verifies user emails via the GetCourse API, maintains a user database in SQLite, and performs daily access checks to remove users who no longer have access. It also supports scheduled message notifications and configuration updates via admin commands.

## Features
- **Chat Join Request Handling**: Requests users to provide their GetCourse-registered email and verifies access.
- **Access Verification**: Checks user group membership via the GetCourse API.
- **Daily Access Checks**: Removes users from chats if their access has expired and schedules notifications.
- **Scheduled Messages**: Sends delayed notifications to users about access expiration.
- **Admin Configuration**: Allows admins to update the bot’s configuration dynamically.
- **Logging**: Logs all operations to a file (`access-bot.log`) and console for debugging and monitoring.

## Project Structure
- **`access_bot.py`**: Main bot logic, handles join requests, daily checks, and scheduled messages.
- **`database.py`**: Manages the SQLite database for storing user data and scheduled messages.
- **`gc_client.py`**: Interacts with the GetCourse API to fetch group and user data.
- **`logger.py`**: Configures logging for the bot.
- **`config.py`**: Contains bot configuration, including API keys, chat IDs, and message templates.
- **`requirements.txt`**: Lists required Python packages.

## Requirements
- Python 3.8+
- Libraries listed in `requirements.txt`:
  - `aiogram`
  - `apscheduler`
  - `aiosqlite`
  - `aiohttp`

## Setup
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Bot**:
   - Edit `config.py` to include:
     - `BOT_TOKEN`: Your Telegram bot token from BotFather.
     - `GC_API_KEY`: Your GetCourse API key.
     - `BASE_GC_API`: Base URL for the GetCourse API.
     - `CHAT_IDS_GROUPS`: Mapping of group names to Telegram chat IDs and GetCourse group IDs.
     - `ADMIN_IDS`: List of Telegram user IDs for admins.
     - Other settings like `CHECK_TIME_HOUR`, `CHECK_TIME_MIN`, and `SEND_TIME` for scheduling.
   - Ensure all required fields in `config.py` are filled.

4. **Run the Bot**:
   ```bash
   python access_bot.py
   ```
   or
   ```bash
   nohup python access_bot.py > /dev/null 2>&1 &
   ```

## Usage
- **User Interaction**:
  - Users send a chat join request, and the bot with admin rights prompts them to provide their GetCourse email.
  - The bot verifies the email against GetCourse groups and approves or declines the request.
  - Users get two attempts to provide a valid email.
  - If access is granted, the user is added to the chat and database.
  - If access is denied or the email is already used, the user is notified.

- **Admin Commands**:
  - `/update_config`: Reloads the configuration from `config.py` and updates the daily check schedule. Only available to users listed in `ADMIN_IDS`.

- **Daily Checks**:
  - Runs at specified in `config.py` time and timezone to verify user access.
  - Removes users without valid group membership and schedules notifications for specified in `config.py` hour the same day.

- **Scheduled Messages**:
  - Notifications about access expiration are sent at the specified time with a 1-second delay between messages.

## Configuration Notes
- **Messages**: Edit the `MESSAGES` dictionary in `config.py` to customize user-facing messages. Use Markdown for formatting.
- **Group Mapping**: Update `CHAT_IDS_GROUPS` in `config.py` to map Telegram chats to GetCourse groups.
- **Scheduling**: Adjust `CHECK_TIME_HOUR`, `CHECK_TIME_MIN`, and `SEND_TIME` in `config.py` for check and notification times.
- **Logging**: Logs are saved to `access-bot.log` (DEBUG level) and printed to the console (INFO level).

## Development
- **Adding New Features**:
  - Modify `access_bot.py` for bot logic.
  - Update `database.py` for new database tables or queries.
  - Extend `gc_client.py` for additional GetCourse API endpoints.
- **Testing**:
  - Test join requests with valid and invalid emails.
  - Verify daily checks by simulating group membership changes.
  - Check scheduled message delivery.

## Troubleshooting
- **Bot Not Responding**: Ensure `BOT_TOKEN` is correct and the bot is running.
- **API Errors**: Verify `GC_API_KEY` and `BASE_GC_API` in `config.py`.
- **Database Issues**: Check if `db.sqlite` is writable and initialized correctly.
- **Logs**: Review `access-bot.log` for detailed error messages.
