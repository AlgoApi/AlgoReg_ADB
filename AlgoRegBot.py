# -*- coding: utf-8 -*-
import asyncio
import shutil
import uuid
import json
import logging
from pyrogram import filters
from pyromod import Client, listen
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import pyautogui
import os
import PIL
import requests
import datetime
import traceback
import zipfile
import sys
import io

os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Форматер для логера
class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(filename)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def save_trace_to_file(trace_text, filename='traceback.txt'):
    with open(filename, 'w') as file:
        file.write(trace_text)
    return filename


def handle_exception(exc_type, exc_value, exc_traceback):
    logger2.critical("Неперехваченное исключение", exc_info=(exc_type, exc_value, exc_traceback))
    exception_as_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    traceback_file = save_trace_to_file(exception_as_text)
    send_error_via_tg(traceback_file, False)


def send_file_to_telegram(bot_token, chat_id, file_path, caption):
    bot_url = f'https://api.telegram.org/bot{bot_token}/sendDocument'
    with open(file_path, 'rb') as file:
        payload = {'chat_id': chat_id, 'caption': caption}
        files = {'document': file}
        response = requests.post(bot_url, data=payload, files=files)
    return response.json()


def send_error_via_tg(traceback_filename, traceback_as_text=True):

    bot_url_document = 'https://api.telegram.org/bot' + telegram_bot_token + '/sendDocument'
    bot_url_text = 'https://api.telegram.org/bot' + telegram_bot_token + '/sendMessage'

    formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

    payload = {
        'chat_id': chat_id,
        'text': f"ОШИБКА НА СЕРВЕРЕ - БОТ\n-------{formatted_datetime}-------\n{traceback_filename}"
    }
    requests.post(bot_url_text, data=payload)

    payload = {
        'chat_id': chat_id,
    }

    if not traceback_as_text:
        with open(traceback_filename, 'rb') as file:
            files = {'document': file}
            req = requests.post(url=bot_url_document, data=payload, files=files)
            response = req.json()
            print(response)
    else:
        pass
        # req = requests.post(url=bot_url_text, data=payload)
        # response = req.json()
        # print(response)

    log_response = send_file_to_telegram(
        telegram_bot_token,
        chat_id,
        "AlgoRegBot.log",
        'Критическая Ошибка'
    )
    print(log_response)


logger2 = logging.getLogger(__name__)
logger2.setLevel(logging.DEBUG)

# настройка обработчика и форматировщика для logger2
handler2 = logging.FileHandler(f"{__name__}.log", mode='a')
formatter2 = logging.Formatter("%(asctime)s - %(filename)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)")

# добавление форматировщика к обработчику
handler2.setFormatter(formatter2)
# добавление обработчика к логгеру в файл
logger2.addHandler(handler2)
# добавление обработчика к логгеру в консоль c цветами
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger2.addHandler(ch)

sys.excepthook = handle_exception

response_git_version = requests.get("https://raw.githubusercontent.com/AlgoApi"
                                    "/AlgoReg_ADB/refs/heads/master/VERSION.txt")

if response_git_version.text.split("\n")[4] != "AlgoRegBot=1.2":
    logger2.warning("ДОСТУПНО ОБНОВЛЕНИЕ AlgoRegBot.py")

# Конфигурация
API_ID = 20427673
API_HASH = "046f9b91f1158d77b8d9765c00849b82"
BOT_TOKEN = os.getenv("telegram_bot_token")
telegram_bot_token = BOT_TOKEN
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
chat_id = os.getenv("chat_id")

# Файл для хранения авторизованных пользователей
AUTHORIZED_USERS_FILE = "authorized_users.json"
CONFIG_FILE = "groups_config.json"


# Чтение конфигурации групп
def load_groups_config():
    logger2.info("Загрузка групп")
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            groups = json.load(f)
    else:
        logger2.error(f"Не удалось загрузить группы, файла: {CONFIG_FILE} нет")
        groups = ["Default Group"]  # Заглушка, если файл отсутствует
    return groups


# Загрузка списка авторизованных пользователей
def load_authorized_users():
    logger2.info("Загрузка пользователей")
    try:
        with open(AUTHORIZED_USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger2.error(f"Не удалось загрузить пользователей, файла: {AUTHORIZED_USERS_FILE} нет")
        return {}


# Сохранение списка авторизованных пользователей
def save_authorized_users(data):
    logger2.info("Сохранение пользователей")
    with open(AUTHORIZED_USERS_FILE, "w") as f:
        json.dump(data, f)


# Инициализация данных
authorized_users = load_authorized_users()

groups = load_groups_config()

# Инициализация клиента
app = Client("auth_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

admin_filter = filters.create(lambda _, __, message: message.from_user and message.from_user.username == "AlgoApi")


def is_authorized(_, __, message: Message):
    users = load_authorized_users()

    user_id = str(message.from_user.id)

    if user_id in users and users[user_id].get("status") == "authorized":
        logger2.info("Проверка на авторизованность: True")
        return True
    logger2.info("Проверка на авторизованность: False")
    return False


def is_registered(_, __, message: Message):
    users = load_authorized_users()

    user_id = str(message.from_user.id)

    if user_id in users and users[user_id].get("status") == "registered":
        logger2.info("Проверка на зарегистрированность: True")
        return True
    logger2.info("Проверка на зарегистрированность: False")
    return False


# Создаём фильтр для команды auth с аргументами
def auth_with_args_filter(_, __, message: Message) -> bool:
    logger2.info(f"Проверяем, есть ли аргументы: текст: {message.text.split()}, len: {len(message.text.split())}")
    return len(message.text.split()) > 1  # Проверяем, есть ли аргументы


# Создаём фильтр для команды auth без аргументов
def auth_without_args_filter(_, __, message: Message) -> bool:
    logger2.info(f"Проверяем, нет ли аргументов: текст: {message.text.split()}, len: {len(message.text.split())}")
    return len(message.text.split()) == 1  # Проверяем, нет ли аргументов


PAGE_SIZE = 10  # Количество папок на одной странице
folder_pages = []  # Хранилище страниц
selected_folders = []
available_folders = []


# Функция построения клавиатуры с учётом страниц
def build_folder_keyboard_with_pagination(available_folders: list, selected_folders, page):
    start_index = page * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    current_page_folders = available_folders[start_index:end_index]
    logger2.info("build_folder_keyboard_with_pagination")
    logger2.info(start_index)
    logger2.info(end_index)
    logger2.info(current_page_folders)

    keyboard = []
    for folder in current_page_folders:
        status = "✅" if folder in selected_folders else "❌"
        keyboard.append([InlineKeyboardButton(f"{status} {folder}", callback_data=folder)])

    # Добавляем кнопки управления страницами
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⏮ Назад", callback_data=f"page:{page - 1}"))
    if end_index < len(available_folders):
        navigation_buttons.append(InlineKeyboardButton("Вперед ⏭", callback_data=f"page:{page + 1}"))

    keyboard.append(navigation_buttons)
    keyboard.append([InlineKeyboardButton("Готово", callback_data="done")])
    logger2.info(keyboard)
    return InlineKeyboardMarkup(keyboard)


# Обработчик команды Snapshot_TelegramService
@app.on_message(filters.command("Snapshot_TelegramService") & filters.create(is_authorized))
async def snapshot_telegram_service(client: Client, message: Message):
    global available_folders
    base_dir = os.getcwd()
    args = message.text.split()
    if len(args) >= 1:
        args = args[1] + "_"
    else:
        args = ""
    available_folders = [
        folder_name for folder_name in os.listdir(base_dir)
        if folder_name.startswith(f"telegram") and args in folder_name and os.path.isdir(folder_name)
    ]
    logger2.info("snapshot_telegram_service")
    logger2.info(base_dir)
    logger2.info(available_folders)

    if not available_folders:
        await message.reply(f"Не найдены папки, начинающиеся на 'telegram' и имеющие '{args}' в названии.")
        return

    global selected_folders
    logger2.info(f"selected_folders до очистки{selected_folders}")
    selected_folders.clear()  # Очищаем список выбранных папок
    logger2.info(f"selected_folders после очистки{selected_folders}")

    # Отправляем первую страницу выбора папок
    await message.reply(
        "Выберите папки для архивации. Нажимайте на папки, чтобы выбрать/убрать. После выбора нажмите 'Готово'.",
        reply_markup=build_folder_keyboard_with_pagination(available_folders, selected_folders, page=0)
    )


# Хэндлер для команды auth
@app.on_message(filters.command("auth") & filters.create(auth_without_args_filter))
async def auth_handler(client: Client, message: Message):
    logger2.info("auth_handler auth_without_args_filter")
    users = load_authorized_users()

    user_id = str(message.from_user.id)
    username = message.from_user.username

    logger2.info(users)
    logger2.info(user_id)
    logger2.info(username)

    # Проверяем, находится ли пользователь в чёрном списке
    if user_id in users and users[user_id].get("status") == "blacklisted":
        await message.reply("Вы были заблокированы и не можете авторизоваться.")
        return

    # Если пользователь уже авторизован
    if user_id in users and users[user_id].get("status") == "authorized":
        await message.reply("Вы уже авторизованы!")
        return

    # Если пользователь уже зарегистрирован
    if user_id in users and users[user_id].get("status") == "registered":
        await message.reply("Вы уже зарегистрированы!")
        return

    # Отправляем запрос администратору на подтверждение
    await client.send_message(
        ADMIN_USERNAME,
        f"Запрос авторизации от пользователя @{username} (ID: {user_id}).",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Принять", callback_data=f"accept_{user_id}_@{username}"),
                InlineKeyboardButton("Отклонить", callback_data=f"reject_{user_id}_@{username}")
            ]
        ])
    )
    await message.reply("Ваш запрос на авторизацию отправлен админу. Пожалуйста, подождите.")


# Хэндлер для обработки нажатий кнопок
@app.on_callback_query()
async def callback_query_handler(client: Client, callback_query):
    global available_folders
    logger2.info("callback_query_handler")
    data = callback_query.data
    logger2.info(data)

    # Загрузка данных пользователей
    users = load_authorized_users()
    logger2.info(users)

    if "accept" in data:
        logger2.info('"accept" in data')
        user_id = str(data.split("_")[1])
        username = data.split("_")[2]
        logger2.info(user_id)
        logger2.info(username)
        logger2.info(groups)
        # Отправляем выбор группы
        await callback_query.message.edit(
            f"Выберите группу для пользователя {username} (ID: {user_id}):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(group, callback_data=f"group_{group}_{user_id}_{username}")]
                for group in groups
            ])
        )
    elif "reject" in data:
        logger2.info('"reject" in data')
        user_id = str(data.split("_")[1])
        # Отклоняем запрос и заносим пользователя в чёрный список
        users[user_id] = {"status": "blacklisted"}
        logger2.info(user_id)
        logger2.info(users[user_id])
        save_authorized_users(users)
        await callback_query.message.edit("Запрос на авторизацию отклонён, пользователь заблокирован.")

    elif "group" in data:
        logger2.info('"group" in data')
        # Привязываем группу и генерируем UUID
        _, group, user_id, username = data.split("_")
        user_id = int(user_id)
        user_uuid = str(uuid.uuid4())

        users[user_id] = {
            "status": "registered",
            "uuid": user_uuid,
            "group": group
        }
        logger2.info(group)
        logger2.info(user_id)
        logger2.info(username)
        logger2.info(user_uuid)
        save_authorized_users(users)

        await callback_query.message.edit(
            f"Пользователь {username} (ID: {user_id}) зарегистрирован в группе '{group}'.\n UUID: {user_uuid}"
        )

        await client.send_message(user_id, f"Вы были зарегистрированы!")

    elif "page" in data:
        # Обработка переключения страниц для выбора папок
        logger2.info('"page" in data')
        _, page = data.split(":")
        page = int(page)

        base_dir = os.getcwd()
        logger2.info(page)
        logger2.info(base_dir)
        logger2.info(available_folders)
        logger2.info(selected_folders)
        await callback_query.message.edit_reply_markup(
            build_folder_keyboard_with_pagination(available_folders, selected_folders, page)
        )
    # ВСЕГДА ДОЛЖНО БЫТЬ В КОНЦЕ
    elif data == "done":
        logger2.info('data == "done"')
        # Обработка завершения выбора папок
        if not selected_folders:
            logger2.info(f"Вы не выбрали ни одной папки. {selected_folders}")
            await callback_query.message.reply("Вы не выбрали ни одной папки.")
            return

        archive_name = "server_state.zip"
        skipped_folders = []
        base_dir = os.getcwd()

        logger2.info(skipped_folders)
        logger2.info(base_dir)

        logger2.info("Создаём архив")

        # Создаём архив
        with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as archive:
            for folder_name in selected_folders:
                try:
                    folder_path = os.path.join(base_dir, folder_name)
                    logger2.info(folder_path)
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            logger2.info(file)
                            if is_not_exe(file):  # Пропускаем .exe файлы
                                logger2.info(f"True {file}")
                                file_path = os.path.join(root, file)
                                logger2.info(file_path)
                                # Добавляем файл в архив с сохранением структуры
                                archive.write(
                                    file_path,
                                    os.path.relpath(file_path, base_dir)
                                )
                    shutil.move(folder_path, os.path.join(base_dir, "archive"))
                except Exception as e:
                    logger2.info(f"Скип {file}")
                    logger2.exception(e, exc_info=True)
                    skipped_folders.append(folder_name)

        # Отправляем уведомления
        if skipped_folders:
            logger2.info(skipped_folders)
            skipped_message = (
                    "Следующие папки не были архивированы, так как они заняты другим процессом:\n"
                    + "\n".join(skipped_folders)
            )
            await callback_query.message.reply(skipped_message)

        # Отправляем архив пользователю
        logger2.info("отправка архива")
        await callback_query.message.reply_document(archive_name)

        logger2.info("даляем архив после отправки")
        # Удаляем архив после отправки
        if os.path.exists(archive_name):
            os.remove(archive_name)

        logger2.info("screenshot")
        screenshot_path = "screenshot.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        log_path = "app.log"

        settings_path = "settings.ini"
        # Отправка файлов
        logger2.info("Отправка")
        logger2.info(screenshot_path)
        logger2.info(log_path)
        logger2.info(settings_path)
        await callback_query.message.reply_document(screenshot_path)
        await callback_query.message.reply_document(log_path)
        await callback_query.message.reply_document(f"{__name__}.log")
        await callback_query.message.reply_document(settings_path)

        await callback_query.message.edit("Архивация завершена.")

    else:
        logger2.info("Обработка выбора/удаления папок")
        # Обработка выбора/удаления папок
        base_dir = os.getcwd()


        logger2.info(available_folders)

        if data in selected_folders:
            logger2.info(f"Убираем {data}")
            selected_folders.remove(data)
        else:
            logger2.info(f"Добавляем {data}")
            selected_folders.append(data)

        logger2.info("Определение текущей страницы")
        # Определение текущей страницы
        for i in range(0, len(available_folders), PAGE_SIZE):
            logger2.info(i)
            if data in available_folders[i:i + PAGE_SIZE]:
                logger2.info(available_folders[i:i + PAGE_SIZE])
                current_page = i // PAGE_SIZE
                logger2.info(current_page)
                break
        else:
            current_page = 0
            logger2.info(f"current_page: {current_page}")

        logger2.info("Обновляем клавиатуру")
        # Обновляем клавиатуру
        await callback_query.message.edit_reply_markup(
            build_folder_keyboard_with_pagination(available_folders, selected_folders, current_page)
        )


# Хэндлер для проверки авторизации
@app.on_message(filters.command("auth") & filters.create(auth_with_args_filter) & filters.create(is_registered))
async def verify_auth_handler(client: Client, message: Message):
    logger2.info("verify_auth_handler auth_with_args_filter & is_registered")
    users = load_authorized_users()

    user_id = message.from_user.id
    args = message.text.split()

    logger2.info(users)
    logger2.info(user_id)
    logger2.info(args)

    logger2.info("Проверяем UUID")
    # Проверяем UUID
    if len(args) != 2:
        logger2.info("len(args) != 2")
        logger2.info(len(args))
        await message.reply("Использование: /auth <ваш UUID>")
        return

    user_uuid = args[1]
    logger2.info(user_uuid)

    if str(user_id) in users and users[str(user_id)].get("uuid") == user_uuid:
        logger2.info("Верный UUID.")
        users[str(user_id)]["status"] = "authorized"
        save_authorized_users(users)
        logger2.info(users[str(user_id)]["status"])
        await message.reply("Вы успешно авторизованы!")
    else:
        logger2.info("Неверный UUID. Попробуйте ещё раз.")
        await message.reply("Неверный UUID. Попробуйте ещё раз.")


# Хэндлер для проверки авторизации
@app.on_message(filters.command("reload") & admin_filter)
async def reload_bot(client: Client, message: Message):
    logger2.info("RELOAD admin_filter")
    global authorized_users, groups
    authorized_users = load_authorized_users()
    groups = load_groups_config()
    await message.reply("RELOAD")


# Функция фильтрации файлов .exe
def is_not_exe(file_name):
    logger2.info(f"is_not_exe {not file_name.lower().endswith(".exe")}")
    return not file_name.lower().endswith(".exe")


# Функция отправки сообщения с кнопками выбора папок
async def send_folder_selection(client, message, folders):
    keyboard = []
    for folder in folders:
        keyboard.append([InlineKeyboardButton(folder, callback_data=folder)])
    keyboard.append([InlineKeyboardButton("Отменить", callback_data="cancel")])

    logger2.info(f"send_folder_selection {keyboard}")

    await message.reply(
        "Выберите одну или несколько папок для архивации:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# Команда /get_ServerState для получения данных и скриншота
@app.on_message(filters.command("Snapshot_TelegramService_old_simple") & filters.create(is_authorized))
async def snapshot_telegram_service_old_simple(client: Client, message: Message):
    logger2.info(f"Snapshot_TelegramService_old_simple")
    user_id = message.from_user.id

    screenshot_path = "screenshot.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)

    log_path = "app.log"

    settings_path = "settings.ini"

    base_dir = os.getcwd()  # Текущая директория со скриптом
    archive_name = "server_state.zip"  # Имя архива
    skipped_folders = []  # Список пропущенных папок
    available_folders = []  # Список доступных папок для выбора пользователем

    await message.reply("Ожидайте, собираем информацию...")

    # Поиск папок для архивации
    for folder_name in os.listdir(base_dir):
        if folder_name.startswith("telegram") and os.path.isdir(folder_name):
            available_folders.append(folder_name)

    # Отправляем выбор папок пользователю
    if available_folders:
        await send_folder_selection(client, message, available_folders)
    else:
        await message.reply("Не найдены подходящие папки для архивации.")

    # Создаём архив
    with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder_name in os.listdir(base_dir):
            if folder_name.startswith("telegram") and os.path.isdir(folder_name):
                try:
                    folder_path = os.path.join(base_dir, folder_name)
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            archive.write(file_path, os.path.relpath(file_path, base_dir))
                except Exception as e:
                    print(e)
                    skipped_folders.append(folder_name)

    # Отправляем уведомление и файл пользователю
    if skipped_folders:
        skipped_message = (
                "Следующие папки не были архивированы, так как они заняты другим процессом:\n"
                + "\n".join(skipped_folders)
        )
        await message.reply(skipped_message)

    # Отправляем архив пользователю
    await message.reply_document(archive_name)

    # Удаляем архив после отправки
    if os.path.exists(archive_name):
        os.remove(archive_name)

    # Отправка файлов
    await app.send_document(user_id, screenshot_path)
    await app.send_document(user_id, log_path)
    await app.send_document(user_id, f"{__name__}.log")
    await app.send_document(user_id, settings_path)


# Запуск бота
if __name__ == "__main__":
    logger2.info(f"STArt")
    app.run()
