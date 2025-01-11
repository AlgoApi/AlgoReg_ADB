# -*- coding: utf-8 -*-
import sys
from flask import Flask, request, jsonify
import threading
import shutil
import time
import psutil
import pyautogui
import pygetwindow as gw
import os
import pywinctl as pwc
import configparser
import logging
import os.path
import requests
import traceback
import datetime
import io
from dotenv import load_dotenv

os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()

if os.getenv("chat_id") is None or os.getenv("chat_id") == "None":
    env_path = os.path.join(os.path.dirname(__file__), 'mac.env')
    load_dotenv(dotenv_path=env_path)


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
    telegram_bot_token = os.getenv("telegram_bot_token")
    chat_id = os.getenv("chat_id")

    bot_url_document = 'https://api.telegram.org/bot' + telegram_bot_token + '/sendDocument'
    bot_url_text = 'https://api.telegram.org/bot' + telegram_bot_token + '/sendMessage'

    formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

    payload = {
        'chat_id': chat_id,
        'text': f"ОШИБКА НА СЕРВЕРЕ\n-------{formatted_datetime}-------\n{traceback_filename}"
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
        #req = requests.post(url=bot_url_text, data=payload)
        #response = req.json()
        #print(response)

    log_response = send_file_to_telegram(
        telegram_bot_token,
        chat_id,
        "app.log",
        'Критическая Ошибка'
    )
    print(log_response)


def login_telegram_client_part1(phone_number: str, proxy: dict[str, str], reset=False, restart=False,
                                phone_number_debug="+7 (000) 123 12 12", sec_sleep=2, debug=False):
    global accounts_on_client, target_telegram_path, config

    config.read("settings.ini")
    accounts_on_client = int(config["GLOBAL"]["accounts_on_client"])
    target_telegram_path = config["GLOBAL"]["target_telegram_path"]

    if debug:
        phone_number = phone_number_debug

    #accounts_on_client += 1
    logger2.info(f"login_telegram_client accounts on client {accounts_on_client}")
    if restart:
        logger2.info("login_telegram_client ПЕРЕзапуск telegram PC")
        logger2.info("login_telegram_client закрытие существующих PC клиентов telegram")
        for proc in psutil.process_iter():
            if proc.name() == 'Telegram.exe':
                proc.terminate()
        time.sleep(sec_sleep)

    if (accounts_on_client >= 3 or target_telegram_path is None or
            target_telegram_path.replace(" ", "") == "" or len(target_telegram_path) < 1) or reset:
        formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        logger2.info(f"login_telegram_client {formatted_datetime}")
        if accounts_on_client >= 3 or reset:
            accounts_on_client = 0

        num_folder = 0
        while num_folder < 10:
            num_folder += 1
            logger2.info("Попытка создать папку")
            if not os.path.exists(f"telegram{formatted_datetime}_{num_folder}"):
                os.makedirs(f'telegram{formatted_datetime}_{num_folder}')
                # os.makedirs(f'telegram{formatted_datetime}_{num_folder}/TelegramForcePortable')
                break
            time.sleep(sec_sleep)
        if num_folder >= 10:
            logger2.critical("login_telegram_client ПАПКА НЕ СОЗДАНА")
            send_error_via_tg("login_telegram_client ПАПКА НЕ СОЗДАНА")
            return False
        target_telegram_path = os.path.join(f'telegram{formatted_datetime}_{num_folder}', 'Telegram.exe')
        logger2.info(f"login_telegram_client {target_telegram_path}")
        time.sleep(sec_sleep)
        logger2.info(f"login_telegram_client копирование exe")
        try:
            shutil.copy(
                os.path.join('Telegram.exe'),
                target_telegram_path
            )
        except Exception as err:
            logger2.exception(f"login_telegram_client FATAL copy {os.path.join('Telegram.exe')} "
                              f"{target_telegram_path} : %s", err, exc_info=True)

            send_error_via_tg(f"login_telegram_client FATAL copy {os.path.join('Telegram.b')}\n"
                              f"{target_telegram_path}")

            exit(f"login_telegram_client FATAL copy {os.path.join('Telegram.exe')} {target_telegram_path}")
        time.sleep(sec_sleep)
        logger2.info("login_telegram_client закрытие существующих PC клиентов telegram")
        for proc in psutil.process_iter():
            if proc.name() == 'Telegram.exe':
                proc.terminate()
        time.sleep(sec_sleep)
        logger2.info(f"login_telegram_client запуск telegram PC {target_telegram_path}")
        try:
            config.read("settings.ini")
            config["GLOBAL"]["target_telegram_path"] = target_telegram_path
            config["GLOBAL"]["accounts_on_client"] = str(accounts_on_client)
            with open('settings.ini', 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            logger2.error("НЕ УДАЛОСЬ СОХРАНИТЬ target_telegram_path accounts_on_client")
            logger2.critical(e)

        #os.startfile(os.path.dirname(os.path.realpath(__file__)) + "\\" + target_telegram_path)
        logger2.info(os.path.dirname(os.path.realpath(__file__)) + "\\" + target_telegram_path)
        os.startfile(os.path.dirname(os.path.realpath(__file__)) + "\\" + target_telegram_path)
        logger2.info("Ожидание 6 сек")
        time.sleep(6)
    if restart:
        logger2.info("login_telegram_client ПЕРЕЗАПУСК закрытие существующих PC клиентов telegram")
        for proc in psutil.process_iter():
            if proc.name() == 'Telegram.exe':
                proc.terminate()
        time.sleep(sec_sleep)
        logger2.info(f"login_telegram_client ПЕРЕзапуск telegram PC {target_telegram_path}")
        os.startfile(os.path.dirname(os.path.realpath(__file__)) + "\\" + target_telegram_path)
        time.sleep(4)
    logger2.info(f"получение PC окна telegram")
    try:
        win = gw.getWindowsWithTitle('Telegram')
    except Exception as err:
        logger2.warning(err)
        win = pwc.getWindowsWithTitle('Telegram')
    try:
        logger2.info(win)
        logger2.info(win[0])
    except Exception as err:
        logger2.error(err)
        logger2.info("login_telegram_client закрытие существующих PC клиентов telegram")
        for proc in psutil.process_iter():
            if proc.name() == 'Telegram.exe':
                proc.terminate()
        time.sleep(sec_sleep)
        logger2.info(f"login_telegram_client запуск telegram PC {target_telegram_path}")
        os.startfile(os.path.dirname(os.path.realpath(__file__)) + "\\" + target_telegram_path)
        time.sleep(4)
        try:
            win = gw.getWindowsWithTitle('Telegram')
        except Exception as err:
            logger2.warning(err)
            win = pwc.getWindowsWithTitle('Telegram')
    if win is not None and len(win) > 0:
        logger2.info(f"трансформация PC окна telegram")
        win[0].size = (800, 780)
        win[0].moveTo(1, 1)
        win[0].show()
        logger2.info("Ожидание 3 сек")
        time.sleep(3)
        if accounts_on_client == 0:
            logger2.info(f"click PC по русски")
            pyautogui.click(400, 564, interval=1)  # по русски
            time.sleep(sec_sleep)
            logger2.info(f"click PC начать общение")
            pyautogui.click(400, 517, interval=1)  # начать общение
        time.sleep(sec_sleep)
        logger2.info(f"click PC по номеру")
        pyautogui.click(400, 569, interval=1)  # по номеру
        time.sleep(sec_sleep)
        raw_phone_number = phone_number.replace("+7", "").replace(" ", "")
        clear_phone_number = raw_phone_number.replace("(", "").replace(")", "")
        logger2.info(f"PC ввод номер нелефона без +7, после по номеру")
        pyautogui.typewrite(clear_phone_number, 0.3)  # номер нелефона без +7
        time.sleep(sec_sleep)
        if accounts_on_client < 1:
            logger2.info("Ставим прокси")
            logger2.info("Настройки")
            pyautogui.click(739, 51, interval=1)
            time.sleep(sec_sleep // 2)
            logger2.info(f"click PC тип соединения")
            pyautogui.click(305, 178, interval=1)  # тип соед
            time.sleep(sec_sleep // 2)
            logger2.info(f"click PC использовать собственный прокси")
            pyautogui.click(300, 329, interval=1)  # исп собствен прокси
            time.sleep(sec_sleep // 2)
            logger2.info(f"click PC HTTP")
            pyautogui.click(290, 279, interval=1)  # HTTP
            time.sleep(sec_sleep // 2)
            logger2.info(f"Ввод PC ip прокси")
            pyautogui.typewrite(proxy["ip"], 0.3)  # ip прокси
            time.sleep(sec_sleep // 2)
            pyautogui.typewrite(["tab"])
            logger2.info(f"Ввод PC порт прокси через tab")
            pyautogui.typewrite(proxy["port"], 0.3)  # порт прокси
            time.sleep(sec_sleep // 2)
            pyautogui.typewrite(["tab"])
            logger2.info(f"Ввод PC логин прокси через tab")
            pyautogui.typewrite(proxy["login"], 0.3)  # логин прокси
            time.sleep(sec_sleep // 2)
            pyautogui.typewrite(["tab"])
            logger2.info(f"Ввод PC пароль прокси через tab")
            pyautogui.typewrite(proxy["password"], 0.3)  # пароль прокси
            time.sleep(sec_sleep // 2)
            logger2.info(f"click PC сохранить прокси")
            pyautogui.click(495, 598, interval=1)  # сохранить прокси
            time.sleep(sec_sleep)
            logger2.info(f"click PC закрыть прокси")
            pyautogui.click(368, 616, interval=1)  # закрыть прокси
            time.sleep(sec_sleep)
            logger2.info(f"click PC закрыть продвинутые настройки")
            pyautogui.click(570, 85, interval=1)  # закрыть настройки
            time.sleep(sec_sleep)
        logger2.info(f"click PC продолжить")
        pyautogui.click(400, 486, interval=1)  # продолжить
        time.sleep(sec_sleep)
    else:
        logger2.critical(f"login_telegram_client не найдено окно telegram {win}")
        try:
            config.read("settings.ini")
            config["GLOBAL"]["target_telegram_path"] = ""
            config["GLOBAL"]["accounts_on_client"] = "0"
            with open('settings.ini', 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            logger2.error(f"НЕ УДАЛОСЬ СОХРАНИТЬ {target_telegram_path} {accounts_on_client}")
            logger2.critical(e)
        send_error_via_tg(f"login_telegram_client не найдено окно telegram \n{win}")
        return False
        # exit(f"login_telegram_client не найдено окно telegram {win}")
    return True


def login_telegram_client_part2(code_tg: str, sec_sleep: int, password: str, debug=False,
                                code_tg_debug=00000):
    global accounts_on_client, target_telegram_path

    logger2.info(f"PC find_number() получение кода тг, после продолжить")
    if debug:
        code_tg = code_tg_debug

    logger2.info(f"PC find_number() {code_tg} ввод")
    pyautogui.click(280, 323, interval=1)  # продолжить
    time.sleep(sec_sleep)
    pyautogui.typewrite(str(code_tg), 0.3)  # код из тг
    time.sleep(sec_sleep)
    logger2.info(f"click PC продолжить, после {code_tg} ввод")
    pyautogui.click(400, 485, interval=1)  # продолжить
    time.sleep(sec_sleep)
    logger2.info(f"PC Ввод {password}, после продолжить")
    pyautogui.typewrite(password, 0.3)  # пароль
    time.sleep(sec_sleep)
    logger2.info(f"click PC продолжить")
    pyautogui.click(400, 485, interval=1)  # продолжить
    time.sleep(sec_sleep)
    time.sleep(sec_sleep)
    logger2.info(f"click PC три полоски")
    pyautogui.click(30, 55, interval=1)  # три полоски
    time.sleep(sec_sleep // 2)
    logger2.info(f"click PC настройки")
    try:
        start = pyautogui.locateCenterOnScreen('start.png')  # If the file is not a png file it will not work
        logger2.info(start)
        pyautogui.click(start)  # Moves the mouse to the coordinates of the image
        logger2.info("найдена кнопка добавить аккаунт синяя")
    except pyautogui.ImageNotFoundException:
        try:
            start = pyautogui.locateCenterOnScreen('start2.png')  # If the file is not a png file it will not work
            logger2.info(start)
            pyautogui.click(start)  # Moves the mouse to the coordinates of the image
            time.sleep(sec_sleep)
            logger2.info("найдена кнопка настройки картинка")
            logger2.info(f"click PC три точки")
            pyautogui.click(528, 85, interval=1)  # три точки
            time.sleep(sec_sleep // 2)
            logger2.info(f"click PC добавить аккаунт")
            pyautogui.click(419, 116, interval=1)  # добавить аккаунт
        except pyautogui.ImageNotFoundException:
            logger2.info("нажато по кордам 105, 545")
            pyautogui.click(105, 545, interval=1)  # настройки
            time.sleep(sec_sleep)
            logger2.info(f"click PC три точки")
            pyautogui.click(528, 85, interval=1)  # три точки
            time.sleep(sec_sleep // 2)
            logger2.info(f"click PC добавить аккаунт")
            pyautogui.click(419, 116, interval=1)  # добавить аккаунт
    time.sleep(sec_sleep)
    accounts_on_client += 1
    try:
        config.read("settings.ini")
        config["GLOBAL"]["target_telegram_path"] = target_telegram_path
        config["GLOBAL"]["accounts_on_client"] = str(accounts_on_client)
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)
    except Exception as e:
        logger2.error("НЕ УДАЛОСЬ СОХРАНИТЬ target_telegram_path accounts_on_client")
        logger2.critical(e)


def create_app():
    app = Flask(__name__)

    # Хранилище состояния авторизации
    auth_sessions = {}

    @app.route('/auth/telegram', methods=['POST'])
    def start_auth():
        data = request.json
        phone_number = data.get("phone_number")
        password = data.get("password")
        proxy = data.get("proxy")
        sec_sleep = data.get("sec_sleep")
        reset_switch = data.get("reset")
        restart_switch = data.get("restart")
        logger2.info(data)
        logger2.info(data.get("phone_number"))
        logger2.info(data.get("password"))
        logger2.info(data.get("proxy"))
        logger2.info(data.get("sec_sleep"))
        logger2.info(data.get("reset"))
        logger2.info(data.get("restart"))

        if reset_switch is None or reset_switch == "":
            reset_switch = False
        elif reset_switch == "False":
            reset_switch = False
        elif reset_switch == "True":
            reset_switch = True

        if restart_switch is None or restart_switch == "":
            restart_switch = False
        elif restart_switch == "False":
            restart_switch = False
        elif restart_switch == "True":
            restart_switch = True

        logger2.info(f"validatoin: {reset_switch}")
        logger2.info(f"validatoin: {restart_switch}")

        if (phone_number is None or accounts_on_client is None or target_telegram_path is None or
                target_telegram_path is None or password is None or proxy is None or sec_sleep is None):
            return jsonify({"status": "error", "message": "Missing credentials"}), 400

        # Уникальный идентификатор сессии (упрощённо используем имя пользователя)
        session_id = phone_number
        event = threading.Event()

        # Сохраняем состояние сессии
        auth_sessions[session_id] = {
            "status": "pending",
            "auth_code": None,
            "event": event
        }

        def wait_for_code():
            # Задержка перед запросом кода
            logger2.info(auth_sessions[session_id])
            res = login_telegram_client_part1(phone_number, reset=reset_switch, proxy=proxy)
            try_n = 0
            while not res:
                res = login_telegram_client_part1(phone_number, proxy=proxy, reset=reset_switch)
                try_n += 1
                if try_n >= 3:
                    logger2.critical("НЕ удалось запустить телеграм и пройти 1 этап")
                    send_error_via_tg("НЕ удалось запустить телеграм и пройти 1 этап")
                    return False

            time.sleep(1)
            auth_sessions[session_id]["status"] = "waiting_code"
            logger2.info(f"Сервер ожидает код авторизации для session_id: {session_id}")

            # Ожидание получения кода (до 3 минут)
            event.wait(timeout=180)
            if auth_sessions[session_id]["status"] == "waiting_code":
                auth_sessions[session_id]["status"] = "failed"
                del auth_sessions[session_id]
                logger2.info(f"session_id: {session_id} удалён")
                logger2.info(f"Таймаут ожидания кода для session_id: {session_id}")
                return

            time.sleep(1)
            login_telegram_client_part2(code_tg=auth_sessions[session_id]["auth_code"],
                                        password=password, sec_sleep=1)

            # Запуск фонового потока для ожидания кода

        threading.Thread(target=wait_for_code).start()

        return jsonify({"status": "pending", "session_id": session_id}), 200

    @app.route('/auth/telegram/code', methods=['POST'])
    def submit_auth_code():
        data = request.json
        session_id = data.get("session_id")
        try:
            auth_code = int(data.get("auth_code"))
        except Exception:
            return jsonify({"status": "error", "message": "Missing session_id or auth_code"}), 400

        if not session_id or not auth_code:
            return jsonify({"status": "error", "message": "Missing session_id or auth_code"}), 400

        session = auth_sessions.get(session_id)
        if not session:
            return jsonify({"status": "error", "message": "Invalid session_id"}), 404

        if session["status"] != "waiting_code":
            return jsonify({"status": "error", "message": "Code not requested yet"}), 400

        # Проверка кода
        if 9999 < auth_code < 100000:  # Здесь можно добавить генерацию и проверку реального кода
            session["status"] = "authorized"
            session["auth_code"] = auth_code
            session["event"].set()  # Сообщаем, что код был получен
            return jsonify({"status": "success", "message": "Authorization completed"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid code"}), 403

    return app


config = configparser.ConfigParser()
config.read("settings.ini")
accounts_on_client = int(config["GLOBAL"]["accounts_on_client"])
target_telegram_path = config["GLOBAL"]["target_telegram_path"]

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

if __name__ == "__main__":
    print("DEAMON")
    time.sleep(2)
    pyautogui.typewrite("12340", 0.3)  # код из тг
