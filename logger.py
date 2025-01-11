import logging
import os.path
import sys
import requests
import traceback
import uiautomator2 as u2
import datetime
import configparser
from dotenv import load_dotenv

load_dotenv()

DEVICE = "PLS FILL"

logger2 = logging.getLogger(__name__)
logger2.setLevel(logging.DEBUG)


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

try:
    config = configparser.ConfigParser()  # создаём объекта парсера
    config.read("settings.ini")
    DEVICE = config["GLOBAL"]["device"]
except:
    logger2.error("Не удалось загрузить настройки")


def save_trace_to_file(trace_text, filename='traceback.txt'):
    with open(filename, 'w') as file:
        file.write(trace_text)
    return filename


def handle_exception(exc_type, exc_value, exc_traceback):
    logger2.critical("Неперехваченное исключение", exc_info=(exc_type, exc_value, exc_traceback))
    formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    xml_path = None
    try:
        print(DEVICE)
        d = u2.connect(DEVICE)
        imagebin = d.screenshot()
        imagebin.save(f"error_{formatted_datetime}.png")

        xml = d.dump_hierarchy()
        # print(xml)
        xml_path = f"xml_dump_{formatted_datetime}.xml"
        with open(xml_path, "w+") as file:
            file.write(xml)

        d.stop_uiautomator()
    except Exception as err:
        logger2.error(f"Не удалось получит скриншот {err}")
    exception_as_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    traceback_file = save_trace_to_file(exception_as_text)
    if os.path.exists(f"error_{formatted_datetime}.png"):
        send_error_via_tg(f"error_{formatted_datetime}.png", traceback_file, False, xml_path)
    else:
        send_error_via_tg(f"nophoto.jpg", traceback_file)


sys.excepthook = handle_exception


def send_file_to_telegram(bot_token, chat_id, file_path, caption):
    bot_url = f'https://api.telegram.org/bot{bot_token}/sendDocument'
    with open(file_path, 'rb') as file:
        payload = {'chat_id': chat_id, 'caption': caption}
        files = {'document': file}
        response = requests.post(bot_url, data=payload, files=files)
    return response.json()


def send_error_via_tg(screenshot_path, traceback_filename, traceback_as_text=True, xml_path=None):
    telegram_bot_token = os.getenv("telegram_bot_token")
    chat_id = os.getenv("chat_id")

    bot_url_photo = 'https://api.telegram.org/bot' + telegram_bot_token + '/sendPhoto'
    bot_url_document = 'https://api.telegram.org/bot' + telegram_bot_token + '/sendDocument'
    bot_url_text = 'https://api.telegram.org/bot' + telegram_bot_token + '/sendMessage'

    formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

    payload = {
        'chat_id': chat_id,
        'text': f"-------{formatted_datetime}-------\n{traceback_filename}"
    }
    requests.post(bot_url_text, data=payload)

    payload = {
        'chat_id': chat_id,
    }

    with open(screenshot_path, 'rb') as photo:
        if not traceback_as_text:
            with open(traceback_filename, 'rb') as file:
                files = {'photo': photo}
                req = requests.post(url=bot_url_photo, data=payload, files=files)
                response = req.json()
                print(response)

                files = {'document': file}
                req = requests.post(url=bot_url_document, data=payload, files=files)
                response = req.json()
                print(response)
        else:
            files = {'photo': photo}
            req = requests.post(url=bot_url_photo, data=payload, files=files)
            response = req.json()
            print(response)

    if xml_path is not None:
        with open(xml_path, 'rb') as file:
            files = {'document': file}
            req = requests.post(url=bot_url_document, data=payload, files=files)
            response = req.json()
            print(response)

    log_response = send_file_to_telegram(
        telegram_bot_token,
        chat_id,
        "logger.log",
        'Критическая Ошибка'
    )
    print(log_response)


response_git_version = requests.get("https://raw.githubusercontent.com/AlgoApi"
                                    "/AlgoReg_ADB/refs/heads/master/VERSION.txt")

if response_git_version.text.split("\n")[2] != "logger=1.1":
    logger2.warning("ДОСТУПНО ОБНОВЛЕНИЕ logger.py")

if __name__ == "__main__":
    logger2.info("TEST")
    send_error_via_tg("test.jpg", "Test2")
