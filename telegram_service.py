import datetime
import random
import shutil
import re
import uiautomator2 as u2
import time
import psutil
import pyautogui
import pygetwindow as gw
import os
import logger
import pywinctl as pwc
import subprocess
import configparser
import requests
from dotenv import load_dotenv
from uiautomator2 import enable_pretty_logging

load_dotenv()

if os.getenv("server_url") is None or os.getenv("server_url") == "None":
    env_path = os.path.join(os.path.dirname(__file__), 'mac.env')
    load_dotenv(dotenv_path=env_path)

logger2 = logger.logger2


class TelegramService:
    def __init__(self, password: str, sec_sleep: int, timeout_n: int,
                 accounts_on_client: int, target_telegram_path: str,
                 proxy: dict[str, str], names: list[str],
                 device: str, off_device: bool = False, phone_number=""):
        if not off_device:
            self.d = u2.connect(device)
        self.NAMES = names
        self.SEC_SLEEP = sec_sleep
        self.TIMEOUT_N = timeout_n
        self.PASSWORD = password
        self.PROXY = proxy
        self.delay_sleep = 0.3
        self.phone_number = phone_number
        self.accounts_on_client = accounts_on_client
        self.target_telegram_path = target_telegram_path
        self.manual_input = False
        response_git_version = requests.get("https://raw.githubusercontent.com/AlgoApi"
                                            "/AlgoReg_ADB/refs/heads/master/VERSION.txt")

        if response_git_version.text.split("\n")[1] != "telegram_service=1.2":
            logger2.warning("ДОСТУПНО ОБНОВЛЕНИЕ telegram_service.py")

    def check_click(self, ui_elem: str, logger_text_click, logger_text_check, critical=True):
        try_n = 0
        if ("permission" in logger_text_click.lower() or "Продолжить" in logger_text_click.lower() or
                "почт" in logger_text_click.lower() or "выбер" in logger_text_click.lower()
                or "google" in logger_text_click.lower()):
            SEC_SLEEP_local = 0.5
        else:
            SEC_SLEEP_local = self.SEC_SLEEP
        while try_n <= self.TIMEOUT_N:
            time.sleep(SEC_SLEEP_local)
            device_elem = self.d.xpath(ui_elem)
            if device_elem.exists:
                logger2.info(logger_text_click)
                device_elem.click()
                return True
            else:
                try_n += 1
                logger2.info(f"{logger_text_check} {try_n}")
        if critical:
            logger2.critical(f"НЕ УДАЛОСЬ {logger_text_check}")
            imagebin = self.d.screenshot()
            formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
            imagebin.save(f"error_{formatted_datetime}.png")

            xml = self.d.dump_hierarchy()
            # print(xml)
            xml_path = f"xml_dump_{formatted_datetime}.xml"
            with open(xml_path, "w+") as file:
                file.write(xml)

            logger.send_error_via_tg(f"error_{formatted_datetime}.png",
                                     f"НЕ УДАЛОСЬ {logger_text_check}", xml_path=xml_path)
            exit()
        else:
            logger2.error(f"НЕ УДАЛОСЬ {logger_text_check}")
            return False

    def login_form(self):
        time.sleep(2)

        response_click = self.check_click('//android.widget.TextView[@text="Начать общение"]',
                                          "click Начать общение login_form",
                                          "Поиск Начать общение login_form", critical=False)
        time.sleep(self.delay_sleep)
        if not response_click:
            self.check_click('//android.widget.TextView[@text="Продолжить на русском"]',
                             "click Продолжить на русском login_form",
                             "Поиск Продолжить на русском login_form")
            time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Продолжить"]',
                         "click Продолжить после Продолжить на русском",
                         "Поиск Продолжить после Продолжить на русском", False)
        time.sleep(self.delay_sleep)
        self.check_click('//*[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]',
                         "click permission_allow_button после Продолжить",
                         "Поиск permission_allow_button после Продолжить", False)
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Продолжить"]',
                         "click Продолжить после Продолжить на русском",
                         "Поиск Продолжить после Продолжить на русском", False)
        time.sleep(self.delay_sleep)
        self.check_click('//*[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]',
                         "click permission_allow_button после Продолжить",
                         "Поиск permission_allow_button после Продолжить", False)
        time.sleep(self.delay_sleep)
        self.check_click('//*[@content-desc="Готово"]',
                         "click Готово после permission_allow_button",
                         "Поиск Готово после permission_allow_button")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Продолжить"]',
                         "click Продолжить после permission_allow_button",
                         "Поиск Продолжить после permission_allow_button", False)
        time.sleep(self.delay_sleep)
        self.check_click('//*[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]',
                         "click permission_allow_button после Продолжить",
                         "Поиск permission_allow_button после Продолжить", False)
        time.sleep(self.delay_sleep)
        try_n = 0
        time.sleep(3)
        while self.d.exists(text="Проверьте код страны и введите свой номер телефона."):
            logger2.info("Ожидание авто ввода номера")
            if try_n >= 3:
                logger2.critical(f"НЕ УДАЛОСЬ дождаться номера телефона")
                self.collect_error_data(f"НЕ УДАЛОСЬ дождаться номера телефона")
                logger2.info("Попробуйте исправить самостоятельно")
                break
            time.sleep(3)
            target_textbox = self.d.xpath('//*[@content-desc="Код страны"]')
            try:
                if target_textbox.exists:
                    logger2.info(target_textbox.exists)
                    logger2.info(target_textbox.get_text() is None)
                    if target_textbox.get_text() is not None:
                        logger2.info(len(target_textbox.get_text()) < 1)
                if target_textbox.exists and (target_textbox.get_text() is None or len(target_textbox.get_text()) < 1):
                    logger2.warning("Номер не был вставлен автоматически, ручной ввод")
                    self.manual_input = True
                    self.check_click('//*[@content-desc="Страна"]',
                                     "click Страна",
                                     "Поиск Страна")
                    time.sleep(1)
                    self.check_click('//*[@content-desc="Поиск"]',
                                     "click Поиск",
                                     "Поиск Поиск")
                    time.sleep(1)
                    self.d.send_keys('Росс')
                    time.sleep(1)
                    self.check_click('//android.widget.TextView[@text="+7"]',
                                     "click +7",
                                     "Поиск +7")

                    time.sleep(1)
                    logger2.warning("ВВЕДИТЕ НОМЕР ТЕЛЕФОНА ВРУЧНУЮ")
                    phone_number = input("Обязательно без кода страны или регионального кода "
                                         "без '+7' '8' в начале номера, без пробелов и иных символов"
                                         " ВВЕДИТЕ НОМЕР ТЕЛЕФОНА ВРУЧНУЮ: ")
                    self.phone_number = phone_number
                    time.sleep(1)

                    self.check_click('//*[@content-desc="Номер телефона"]',
                                     "click Номер телефона",
                                     "ПОИСК Номер телефона")
                    time.sleep(self.delay_sleep * 5)
                    logger2.info(phone_number)
                    self.d.send_keys(phone_number)
                    time.sleep(self.delay_sleep)

                    self.check_click('//*[@content-desc="Готово"]',
                                     "click Готово",
                                     "Поиск Готово")
                    time.sleep(self.delay_sleep * 5)
                    self.check_click('//android.widget.TextView[@text="Да"]',
                                     "click Да",
                                     "Поиск Да")
            except Exception:
                continue
            time.sleep(8 - try_n * 3)
            logger2.info("ожидаем авто ввода номера")
            try_n += 1

        if not self.manual_input:
            self.check_click('//*[@content-desc="Готово"]',
                             "click Готово",
                             "Поиск Готово", critical=False)
            time.sleep(self.delay_sleep * 5)
            self.check_click('//android.widget.TextView[@text="Да"]',
                             "click Да",
                             "Поиск Да", critical=False)

        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="d Войти через аккаунт Google"]',
                         "click Войти через аккаунт Google, просят почту",
                         "login_form почту не просят, проверка", False)
        time.sleep(self.delay_sleep)
        try_n = 0
        while try_n < self.TIMEOUT_N:
            if self.SEC_SLEEP < 2:
                time.sleep(self.SEC_SLEEP * 2)
            else:
                time.sleep(self.SEC_SLEEP)
            if self.d.exists(text="Выберите аккаунт"):
                time.sleep(0.5)
                for elem in self.d.xpath('//*[@resource-id="com.google.android.gms:id/container"]').all():
                    elem.click()
                    logger2.info("click первый аккаунт Google, просят почту, аккаунт")
                    break
                break
            else:
                try_n += 1
                logger2.info(f"login_form аккаунт google не просят, проверка {try_n}")
        time.sleep(self.delay_sleep)
        timeout_maxsec = 60
        timeout_sec = 0
        while self.d(textContains="Мы отправили SMS").exists:
            if self.SEC_SLEEP < 2:
                time.sleep(self.SEC_SLEEP * 2)
            else:
                time.sleep(self.SEC_SLEEP)
            timeout_maxsec = 40
            if timeout_sec > timeout_maxsec:
                logger2.warning("Слишком долгое ожидание автоввода кода из sms, ручной ввод")
                self.d.app_start("com.samsung.android.messaging", wait=True)
                time.sleep(self.delay_sleep)
                try_n = 0
                while not self.d.xpath('//android.widget.TextView[@text="Разговоры"]').exists:
                    time.sleep(self.SEC_SLEEP)
                    try_n += self.SEC_SLEEP
                    if try_n >= timeout_maxsec // 2:
                        logger2.error("Не найден текст Разговоры в смс приложении samsung")
                        logger2.info("Попробуйте исправить самостоятельно")
                        break
                time.sleep(0.5)
                smski_body = self.d.xpath('//*[@resource-id="com.samsung.android.messaging:id/text_content"]').all()
                smski_head = self.d.xpath(
                    '//*[@resource-id="com.samsung.android.messaging:id/list_avatar_name"]').all()
                target_index = 0
                manual_code = ""
                if smski_head is not None and len(smski_head) > 0 and smski_body is not None and len(
                        smski_body) > 0:
                    for sms in smski_head:
                        logger2.info(sms.text)
                        if "telegram" in str(sms.text).lower():
                            logger2.info("найдена sms telegram")
                            manual_code = smski_body[smski_head.index(sms)].text
                            target_index = manual_code.find("code")
                            try:
                                if target_index is not None and target_index > 0:
                                    manual_code = manual_code[target_index:target_index + 14]
                                else:
                                    manual_code = manual_code[:31]
                            except IndexError:
                                logger2.info(f"IndexError {len(manual_code)} {target_index} {manual_code}")
                                target_index = manual_code.find("https")
                                if target_index is not None and target_index > 0:
                                    manual_code = manual_code[:target_index]
                                else:
                                    logger2.warning(f"Не удалось укоротить sms {len(manual_code)} {target_index} "
                                                    f"{manual_code}")
                            manual_code = [int(s) for s in re.findall(r'\b\d+\b', manual_code)]
                    logger2.info(f"Код :{manual_code}")
                    logger2.info(f"Код: {manual_code[0]}")
                    if manual_code is None or manual_code == "" or manual_code == [] or len(manual_code) < 1:
                        logger2.error("НЕ ПОЛУЧЕН КОД")
                        self.d.app_start("org.telegram.messenger", wait=True)
                        time.sleep(self.delay_sleep)
                        timeout_sec = 0
                        continue
                    self.d.app_start("org.telegram.messenger", wait=True)
                    time.sleep(self.delay_sleep)
                    time.sleep(self.delay_sleep)
                    all_number_enter = self.d.xpath('//android.widget.EditText').all()
                    for elem in all_number_enter:
                        print(elem.text)
                        elem.click()
                        break
                    time.sleep(self.delay_sleep)
                    self.d.send_keys(str(manual_code[0]))
                    time.sleep(self.SEC_SLEEP)
                    all_number_enter = self.d.xpath('//android.widget.EditText').all()
                    total_entered_code = ""
                    for elem in all_number_enter:
                        total_entered_code += elem.text
                    if len(total_entered_code) < 5 or str(manual_code[0]) != total_entered_code:
                        logger2.error("неверно введён код, 2 попытка")
                        all_number_button = self.d.xpath('//android.view.ViewGroup/android.view.View').all()
                        for number in str(manual_code[0]):
                            time.sleep(self.delay_sleep)
                            for button in all_number_button:
                                button_index = str(int(button.info.get("index")) + 1)
                                if button_index == "10":
                                    button_index = "0"
                                if button_index == number:
                                    button.click()
                                    time.sleep(self.delay_sleep)
                                    break
                    break
                else:
                    logger2.error("НЕ ПОЛУЧЕНЫ sms-ки")
                    self.d.app_start("org.telegram.messenger", wait=True)
                    time.sleep(self.delay_sleep)
                    timeout_sec = 0
                    continue
            else:
                if self.SEC_SLEEP < 2:
                    timeout_sec += self.SEC_SLEEP * 2
                else:
                    timeout_sec += self.SEC_SLEEP
        time.sleep(self.delay_sleep)

        self.check_click('//android.widget.TextView[@text="d Войти через аккаунт Google"]',
                         "click Войти через аккаунт Google, просят почту 2",
                         "login_form Проверьте почту не просят, проверка", False)
        time.sleep(self.delay_sleep)
        try_n = 0
        while try_n < self.TIMEOUT_N:
            time.sleep(self.SEC_SLEEP)
            if self.d.exists(text="Выберите аккаунт"):
                for elem in self.d.xpath('//*[@resource-id="com.google.android.gms:id/container"]').all():
                    elem.click()
                    logger2.warning("click первый аккаунт Google, просят почту, аккаунт 2")
                    break
                break
            else:
                try_n += 1
                logger2.info(f"login_form выбрать аккаунт не просят, проверка {try_n}")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Продолжить"]',
                         "click Продолжить login_form, после почт или номера",
                         "Поиск Продолжить login_form, после почт или номера", False)
        time.sleep(self.delay_sleep)
        self.check_click('//*[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]',
                         "click permission_allow_button, после Продолжить",
                         "Поиск permission_allow_button, после Продолжить", False)
        time.sleep(self.delay_sleep)
        time.sleep(self.SEC_SLEEP)
        timeout_sec_sleep = 0
        timeout_max_sec_sleep = 160
        while (self.d.exists(textContains="Проверка телефона") or
               self.d.exists(textContains="Отвечать на звонок не требуется")):
            if timeout_sec_sleep > timeout_max_sec_sleep:
                logger2.error("не дождались проверки")
                self.check_click('//*[@text="Получить SMS с кодом"]', "нажимаем получить код из смс",
                                 "Поиск получить код из смс")
                break
            else:
                timeout_sec_sleep += self.SEC_SLEEP + 10
            time.sleep(self.SEC_SLEEP + 10)
            logger2.info("ждём проверку 160 сек")

        time.sleep(self.SEC_SLEEP)
        time.sleep(self.SEC_SLEEP)

        logger2.info("Проверяем на Введите код")
        while self.d.exists(text="Введите код"):
            logger2.info("Проверка телефона не удалась ждём код из смс 40 сек")
            if self.SEC_SLEEP < 2:
                time.sleep(self.SEC_SLEEP * 2)
            else:
                time.sleep(self.SEC_SLEEP)
            timeout_maxsec = 40
            if timeout_sec > timeout_maxsec:
                logger2.warning("Слишком долгое ожидание автоввода кода из sms, ручной ввод")
                self.d.app_start("com.samsung.android.messaging", wait=True)
                time.sleep(self.delay_sleep)
                try_n = 0
                while not self.d.xpath('//android.widget.TextView[@text="Разговоры"]').exists:
                    time.sleep(self.SEC_SLEEP)
                    try_n += self.SEC_SLEEP
                    if try_n >= timeout_maxsec // 2:
                        logger2.error("Не найден текст Разговоры в смс приложении samsung")
                        logger2.info("Попробуйте исправить самостоятельно")
                        break
                time.sleep(0.5)
                smski_body = self.d.xpath('//*[@resource-id="com.samsung.android.messaging:id/text_content"]').all()
                smski_head = self.d.xpath(
                    '//*[@resource-id="com.samsung.android.messaging:id/list_avatar_name"]').all()
                target_index = 0
                manual_code = ""
                if smski_head is not None and len(smski_head) > 0 and smski_body is not None and len(
                        smski_body) > 0:
                    for sms in smski_head:
                        logger2.info(sms.text)
                        if "telegram" in str(sms.text).lower():
                            logger2.info("найдена sms telegram")
                            manual_code = smski_body[smski_head.index(sms)].text
                            target_index = manual_code.find("code")
                            try:
                                if target_index is not None and target_index > 0:
                                    manual_code = manual_code[target_index:target_index + 14]
                                else:
                                    manual_code = manual_code[:31]
                            except IndexError:
                                logger2.info(f"IndexError {len(manual_code)} {target_index} {manual_code}")
                                target_index = manual_code.find("https")
                                if target_index is not None and target_index > 0:
                                    manual_code = manual_code[:target_index]
                                else:
                                    logger2.warning(f"Не удалось укоротить sms {len(manual_code)} {target_index} "
                                                    f"{manual_code}")
                            manual_code = [int(s) for s in re.findall(r'\b\d+\b', manual_code)]
                    logger2.info(f"Код :{manual_code}")
                    logger2.info(f"Код: {manual_code[0]}")
                    if manual_code is None or manual_code == "" or manual_code == [] or len(manual_code) < 1:
                        logger2.error("НЕ ПОЛУЧЕН КОД")
                        self.d.app_start("org.telegram.messenger", wait=True)
                        time.sleep(self.delay_sleep)
                        timeout_sec = 0
                        continue
                    self.d.app_start("org.telegram.messenger", wait=True)
                    time.sleep(self.delay_sleep)
                    time.sleep(self.delay_sleep)
                    all_number_enter = self.d.xpath('//android.widget.EditText').all()
                    for elem in all_number_enter:
                        print(elem.text)
                        elem.click()
                        break
                    time.sleep(self.delay_sleep)
                    self.d.send_keys(str(manual_code[0]))
                    time.sleep(self.SEC_SLEEP)
                    all_number_enter = self.d.xpath('//android.widget.EditText').all()
                    total_entered_code = ""
                    for elem in all_number_enter:
                        total_entered_code += elem.text
                    if len(total_entered_code) < 5 or str(manual_code[0]) != total_entered_code:
                        logger2.error("неверно введён код, 2 попытка")
                        all_number_button = self.d.xpath('//android.view.ViewGroup/android.view.View').all()
                        for number in str(manual_code[0]):
                            time.sleep(self.delay_sleep)
                            for button in all_number_button:
                                button_index = str(int(button.info.get("index")) + 1)
                                if button_index == "10":
                                    button_index = "0"
                                if button_index == number:
                                    button.click()
                                    time.sleep(self.delay_sleep)
                                    break
                    break
                else:
                    logger2.error("НЕ ПОЛУЧЕНЫ sms-ки")
                    self.d.app_start("org.telegram.messenger", wait=True)
                    time.sleep(self.delay_sleep)
                    timeout_sec = 0
                    continue
            else:
                if self.SEC_SLEEP < 2:
                    timeout_sec += self.SEC_SLEEP * 2
                else:
                    timeout_sec += self.SEC_SLEEP

    def set_name(self):
        time.sleep(self.SEC_SLEEP)
        try_n = 0
        while try_n <= self.TIMEOUT_N + 2:
            if self.SEC_SLEEP < 2:
                time.sleep(self.SEC_SLEEP * 2)
            else:
                time.sleep(self.SEC_SLEEP)
            logger2.info("set_name получаем поля текста")
            all_elem = self.d.xpath("//android.widget.EditText").all()
            if all_elem is not None and len(all_elem) > 0:
                for elem in all_elem:
                    elem.click()
                    random_index = random.randint(0, len(self.NAMES) - 1)
                    logger2.info(f"выбрано имя {random_index} - {self.NAMES[random_index]}")
                    self.d.send_keys(self.NAMES[random_index])
                    logger2.info("пишем имя")
                    break
                time.sleep(self.delay_sleep)
                self.check_click('//*[@content-desc="Готово"]',
                                 "сlick Готово после имени",
                                 "Поиск Готово после имени")
                time.sleep(self.delay_sleep)
                break
            else:
                all_elem = self.d.xpath("//android.widget.EditText").all()
                try_n += 1
                if try_n <= self.TIMEOUT_N + 2:
                    logger2.critical(f"set_name НЕ НАЙДЕНЫ поля текста {all_elem}")
                    self.collect_error_data(f"set_name НЕ НАЙДЕНЫ поля текста {all_elem}")
                    logger2.warning("Выполните установку имени вручную и продолжите в телеграм")
                    # exit(f"set_name НЕ НАЙДЕНЫ поля текста {all_elem}")
                else:
                    logger2.warning(f"set_name ПОПЫТКА {try_n} НЕ НАЙДЕНЫ поля текста")
        time.sleep(self.SEC_SLEEP)

    def skip_contacts(self):
        try_n = 0
        while try_n <= self.TIMEOUT_N:
            time.sleep(self.SEC_SLEEP)
            if self.d.exists(text="Не сейчас"):
                logger2.info("skip_contacts найден Не сейчас")
                self.check_click('//android.widget.TextView[@text="Не сейчас"]',
                                 "click Не сейчас",
                                 "Поиск Не сейчас")
                time.sleep(self.SEC_SLEEP)
                break
            else:
                try_n += 1
                logger2.warning(f"skip_contacts ПОПЫТКА {try_n} Не сейчас")
            if try_n > self.TIMEOUT_N:
                logger2.error("skip_contacts НЕ НАЙДЕНА кнопка Не сейчас")
                # imagebin = self.d.screenshot()
                # formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
                # imagebin.save(f"error_{formatted_datetime}.png")

                # xml = self.d.dump_hierarchy()
                ## print(xml)
                # xml_path = f"xml_dump_{formatted_datetime}.xml"
                # with open(xml_path, "w+") as file:
                #    file.write(xml)

                # logger.send_error_via_tg(f"error_{formatted_datetime}.png",
                #                         "skip_contacts НЕ НАЙДЕНА кнопка Не сейчас",
                #                         xml_path=xml_path)
                # input("Введите что либо, чтобы продолжить")
        time.sleep(self.SEC_SLEEP)

    def set_2fa(self):
        time.sleep(self.delay_sleep)
        self.check_click('//*[@content-desc="Открыть меню навигации"]',
                         "set_2fa click меню навигации",
                         "set_2fa Поиск меню навигации", critical=False)
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Настройки"]',
                         "set_2fa click Настройки",
                         "set_2fa Поиск Настройки", critical=False)
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.FrameLayout[@text="Конфиденциальность"]',
                         "click Конфиденциальность после Настройки",
                         "Поиск Конфиденциальность после Настройки")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Облачный пароль"]',
                         "click Облачный пароль после Конфиденциальность",
                         "Поиск Облачный пароль после Конфиденциальность")
        time.sleep(self.delay_sleep)
        try_n = 0
        while try_n <= self.TIMEOUT_N:
            time.sleep(self.SEC_SLEEP)
            self.check_click('//android.widget.TextView[@text="Задать пароль"]',
                             "click Задать пароль после Облачный пароль",
                             "Поиск Задать пароль после Облачный пароль", False)
            time.sleep(self.SEC_SLEEP)
            time.sleep(self.SEC_SLEEP)
            logger2.info("поиск Введите пароль после Задать пароль")
            time.sleep(0.3)
            if self.d.xpath('//*[@content-desc="Введите пароль"]').exists:
                self.d.xpath('//*[@content-desc="Введите пароль"]').click()
                self.d.send_keys(self.PASSWORD)
                logger2.info("ввод пароля 2fa")
                break
            else:
                try_n += 1
                if try_n > self.TIMEOUT_N:
                    logger2.critical("set_2fa НЕ НАЙДЕНО Введите пароль после Задать пароль")
                    self.collect_error_data("set_2fa НЕ НАЙДЕНО Введите пароль после Задать пароль")
                    exit("set_2fa НЕ НАЙДЕНО Введите пароль после Задать пароль")
                else:
                    logger2.warning(f"set_2fa ПОПЫТКА {try_n} Введите пароль после Задать пароль")
        time.sleep(self.SEC_SLEEP)
        try_n = 0
        while try_n <= self.TIMEOUT_N:
            if self.SEC_SLEEP < 2:
                time.sleep(self.SEC_SLEEP * 2)
            else:
                time.sleep(self.SEC_SLEEP)
            self.check_click('//*[@content-desc="Далее"]',
                             "click Далее после Ввода пароля 2fa",
                             "Поиск Далее после Ввода пароля 2fa", False)
            time.sleep(self.delay_sleep)
            self.check_click('//*[@content-desc="Далее"]',
                             "click Далее после Ввода пароля 2fa",
                             "Поиск Далее после Ввода пароля 2fa", False)
            time.sleep(self.delay_sleep)
            logger2.info("поиск Повторите пароль после Далее")
            time.sleep(self.delay_sleep)
            if self.d.xpath('//*[@content-desc="Повторите пароль"]').exists:
                self.d.xpath('//*[@content-desc="Повторите пароль"]').click()
                self.d.send_keys(self.PASSWORD)
                logger2.info("ввод пароля 2fa повторно")
                break
            else:
                try_n += 1
                if try_n > self.TIMEOUT_N:
                    logger2.critical("set_2fa НЕ НАЙДЕНО Повторите пароль после Далее")
                    self.collect_error_data("set_2fa НЕ НАЙДЕНО Повторите пароль после Далее")
                    exit("set_2fa НЕ НАЙДЕНО Повторите пароль после Далее")
                else:
                    logger2.warning(f"set_2fa ПОПЫТКА {try_n} Повторите пароль после Далее")
        time.sleep(self.delay_sleep)
        self.check_click('//*[@content-desc="Далее"]',
                         "click Далее после Ввод пароля 2fa повторно",
                         "Поиск Далее после Ввод пароля 2fa повторно")
        time.sleep(self.delay_sleep)
        try_n = 0
        while try_n <= self.TIMEOUT_N:
            if self.SEC_SLEEP < 2:
                time.sleep(self.SEC_SLEEP * 2)
            else:
                time.sleep(self.SEC_SLEEP)
            self.check_click('//android.widget.TextView[@text="Пропустить"]',
                             "click Пропустить после Далее",
                             "Поиск Пропустить после Далее")
            time.sleep(self.SEC_SLEEP)
            logger2.info("поиск Электронная почта после Пропустить")
            time.sleep(self.delay_sleep)
            if self.d.xpath('//*[@content-desc="Электронная почта"]').exists:
                self.check_click('//*[@content-desc="Далее"]',
                                 "click Далее после поиск Электронная почта",
                                 "Поиск Далее после поиск Электронная почта")
                break
            else:
                try_n += 1
                if try_n > self.TIMEOUT_N:
                    logger2.critical("set_2fa НЕ НАЙДЕНО Электронная почта после Пропустить")
                    self.collect_error_data("set_2fa НЕ НАЙДЕНО Электронная почта после Пропустить")
                    exit("set_2fa НЕ НАЙДЕНО Электронная почта после Пропустить")
                else:
                    logger2.warning(f"set_2fa ПОПЫТКА {try_n} Электронная почта после Пропустить")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Пропустить"]',
                         "click Пропустить после Далее",
                         "Поиск Пропустить после Далее", critical=False)
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Пропустить"]',
                         "click Пропустить2 после Пропустить",
                         "Поиск Пропустить2 после Пропустить", critical=False)
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Вернуться к настройкам"]',
                         "click Вернуться к настройкам после Пропустить2",
                         "Поиск Вернуться к настройкам после Пропустить2", critical=False)
        time.sleep(self.delay_sleep)
        logger2.info(self.d.xpath('//*[@content-desc="Назад"]').exists)
        time.sleep(self.delay_sleep)
        with self.d.watch_context() as ctx:
            #  назад
            ctx.when('//*[@content-desc="Назад"]').click()
            logger2.info("click Назад после Вернуться к настройкам")
            time.sleep(self.delay_sleep)
        logger2.info(self.d.xpath('//*[@content-desc="Назад"]').exists)
        time.sleep(self.delay_sleep)
        with self.d.watch_context() as ctx:
            #  назад
            ctx.when('//*[@content-desc="Назад"]').click()
            logger2.info("click Назад2 после Назад")
            time.sleep(self.delay_sleep)
        logger2.info(self.d.xpath('//*[@content-desc="Назад"]').exists)
        time.sleep(self.delay_sleep)
        with self.d.watch_context() as ctx:
            #  назад
            ctx.when('//*[@content-desc="Назад"]').click()
            logger2.info("click Назад3 после Назад2")
            time.sleep(self.delay_sleep)
        logger2.info(f"НОМЕР ТЕЛЕФОНА: {self.phone_number}")

    def get_tg_code(self):
        code_tg = 0
        try_n = 0
        while try_n <= self.TIMEOUT_N:
            if self.SEC_SLEEP < 2:
                time.sleep(self.SEC_SLEEP * 2)
            else:
                time.sleep(self.SEC_SLEEP)
            #  первая плитка сообщений(там уже должен быть телеграм)
            if not self.d.xpath('//android.widget.TextView[@text="Служебные уведомления"]').exists:
                self.check_click('//android.view.ViewGroup',
                                 "get_tg_code click на первую плитку с сообщениями",
                                 "get_tg_code Поиск первую плитку с сообщениями")
            time.sleep(self.delay_sleep)
            time.sleep(self.delay_sleep)
            if self.d.xpath('//android.widget.TextView[@text="Служебные уведомления"]').exists:
                timeout = 0
                while timeout < 200:
                    message_code_tg_obj = self.d(textContains="Код для входа в Telegram:")
                    if message_code_tg_obj.exists:
                        raw_message_code_tg = message_code_tg_obj.get_text()
                        cleaned_message_code_tg = raw_message_code_tg[:raw_message_code_tg.find(".")]
                        raw_code_tg = re.findall(r'\d+', cleaned_message_code_tg)
                        if len(raw_code_tg) > 0:
                            code_tg = raw_code_tg[0]
                            logger2.info(f"find_number {code_tg}")
                        break
                    else:
                        time.sleep(4)
                        logger2.warning("Не найден код")
                        timeout += 4
                if code_tg is None or int(code_tg) < 10000 or int(code_tg) > 999999:
                    logger2.critical(f"find_number НЕ НАЙДЕН Код для входа в Telegram {code_tg}")
                    self.collect_error_data(f"find_number НЕ НАЙДЕН Код для входа в Telegram {code_tg}")
                    exit(f"find_number НЕ НАЙДЕН Код для входа в Telegram {code_tg}")
                time.sleep(self.delay_sleep)
                return code_tg
            else:
                try_n += 1
                if try_n > self.TIMEOUT_N:
                    self.collect_error_data("find_number НЕ НАЙДЕНО Служебные уведомления")
                    exit("find_number НЕ НАЙДЕНО Служебные уведомления")
                else:
                    logger2.warning(f"find_number ПОПЫТКА {try_n} Служебные уведомления")
        time.sleep(self.SEC_SLEEP)

    def login_telegram_client_on_server(self):
        if self.phone_number is None or self.PASSWORD is None or self.PROXY is None:
            logger2.error("self.phone_number is None or self.PASSWORD is None or self.PROXY is None")
            return False
        try_n = 0
        while try_n < self.TIMEOUT_N:
            try_n += 1

            if try_n >= self.TIMEOUT_N:
                logger2.info("Не удалось авторизовать аккаунт на сервере")
                break

            server_url = os.getenv("server_url")
            auth_data = {
                "phone_number": self.phone_number,
                "password": self.PASSWORD,
                "proxy": self.PROXY,
                "sec_sleep": 2,
                "reset": False,
                "restart": False
            }

            if try_n == 2:
                auth_data["restart"] = True
            if try_n > 2:
                auth_data["reset"] = True

            response = requests.post(f"{server_url}/auth/telegram", json=auth_data)
            if response.status_code != 200:
                logger2.critical("Ошибка авторизации:", response.json().get("message"))
                self.collect_error_data(f"Ошибка авторизации: {response.json().get('message')}")
                continue

            session_id = response.json().get("session_id")
            logger2.info(f"Авторизация началась, session_id: {session_id}")

            # 2. Ожидание запроса кода от сервера
            start_time = time.time()
            while time.time() - start_time < 180:  # Ожидание до 3 минут
                try:
                    response = requests.post(f"{server_url}/auth/telegram/code",
                                             json={"session_id": session_id, "auth_code": 9})
                except Exception as e:
                    logger2.exception(f"Превышено время ожидания \n{e}", exc_info=True)
                if response.status_code == 400 and "Code not requested yet" in response.json().get("message"):
                    logger2.info("Сервер ещё не запросил код...")
                    time.sleep(15)  # Периодическая проверка каждые 15 секунд
                else:
                    logger2.info("Сервер ожидает код авторизации.")
                    break

            if time.time() - start_time >= 120:
                self.collect_error_data("Не дождались запроса кода")
                exit("Запустите python3 telegram_service.py, как только решите проблемы с соединением к серверу")

            # 3. Отправка кода авторизации
            auth_code = self.get_tg_code()
            response = requests.post(f"{server_url}/auth/telegram/code",
                                     json={"session_id": session_id, "auth_code": auth_code})
            if response.status_code == 200:
                logger2.info("Авторизация завершена успешно!")
                time.sleep(6)
                check_login = self.d(textContains="Вход с нового устройства").exists
                try_n_n = 0
                while not check_login:
                    if try_n_n >= self.TIMEOUT_N + 5:
                        logger2.error("Не удалось подтвердить вход")
                        self.collect_error_data("Не удалось подтвердить вход")
                        break
                    logger2.info("Не удалось подтвердить вход")
                    time.sleep(5)
                    try_n_n += 1
                    check_login = self.d(textContains="Вход с нового устройства").exists
                if try_n_n >= self.TIMEOUT_N + 5:
                    continue
                logger2.info("Вход подтверждён")
                return True
            else:
                logger2.critical("Ошибка завершения авторизации:", response.json().get("message"))
                self.collect_error_data(f"Ошибка завершения авторизации: {response.json().get('message')}")
                continue

    def collect_error_data(self, text):
        logger2.critical(text)
        imagebin = self.d.screenshot()
        formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
        imagebin.save(f"error_{formatted_datetime}.png")

        xml = self.d.dump_hierarchy()
        xml_path = f"xml_dump_{formatted_datetime}.xml"
        with open(xml_path, "w+") as file:
            file.write(xml)

        try:
            logger.send_error_via_tg(f"error_{formatted_datetime}.png",
                                     text,
                                     xml_path=xml_path)
        except Exception as e:
            logger2.critical("Не УДАЛОСЬ ОТПРАВИТЬ ЛОГИ")
            logger2.critical(e)

    def login_telegram_client_local(self, debug=False, phone_number_debug="+7 (000) 123 12 12", code_tg_debug=00000):

        if debug:
            self.phone_number = phone_number_debug

        self.accounts_on_client += 1
        logger2.info(f"login_telegram_client accounts on client {self.accounts_on_client}")
        if (self.accounts_on_client >= 3 or self.target_telegram_path is None or
                self.target_telegram_path.replace(" ", "") == "" or len(self.target_telegram_path) < 1):
            formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
            logger2.info(f"login_telegram_client {formatted_datetime}")
            if self.accounts_on_client >= 3:
                self.accounts_on_client = 1

            num_folder = 0
            while num_folder < 10:
                num_folder += 1
                logger2.info("Попытка создать папку")
                if not os.path.exists(f"telegram{formatted_datetime}_{num_folder}"):
                    os.makedirs(f'telegram{formatted_datetime}_{num_folder}')
                    os.makedirs(f'telegram{formatted_datetime}_{num_folder}/TelegramForcePortable')
                    break
                time.sleep(self.SEC_SLEEP)
            if num_folder >= 10:
                logger2.critical("login_telegram_client ПАПКА НЕ СОЗДАНА")
                self.collect_error_data("login_telegram_client ПАПКА НЕ СОЗДАНА")
                # input("Введите что либо, чтобы продолжить")
                return "login_telegram_client ПАПКА НЕ СОЗДАНА"
            self.target_telegram_path = os.path.join(f'telegram{formatted_datetime}_{num_folder}', 'Telegram.app')
            logger2.info(f"login_telegram_client {self.target_telegram_path}")
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"login_telegram_client копирование exe")
            try:
                shutil.copytree(
                    os.path.join('Telegram.app'),
                    self.target_telegram_path, dirs_exist_ok=True
                )
            except Exception as err:
                logger2.exception(f"login_telegram_client FATAL copy {os.path.join('Telegram.app')} "
                                  f"{self.target_telegram_path} : %s", err, exc_info=True)

                imagebin = self.d.screenshot()
                formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
                imagebin.save(f"error_{formatted_datetime}.png")

                xml = self.d.dump_hierarchy()
                # print(xml)
                xml_path = f"xml_dump_{formatted_datetime}.xml"
                with open(xml_path, "w+") as file:
                    file.write(xml)

                logger.send_error_via_tg(f"error_{formatted_datetime}.png",
                                         f"login_telegram_client FATAL copy {os.path.join('Telegram.app')}\n"
                                         f"{self.target_telegram_path}", xml_path=xml_path)
                # input("Введите что либо, чтобы продолжить")
                exit(f"login_telegram_client FATAL copy {os.path.join('Telegram.app')} {self.target_telegram_path}")
            time.sleep(self.SEC_SLEEP)
            logger2.info("login_telegram_client закрытие существующих PC клиентов telegram")
            for proc in psutil.process_iter():
                if proc.name() == 'Telegram.app':
                    proc.terminate()
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"login_telegram_client запуск telegram PC {self.target_telegram_path}")
            try:
                config = configparser.ConfigParser()  # создаём объекта парсера
                config.read("settings.ini")
                config["GLOBAL"]["target_telegram_path"] = self.target_telegram_path
                config["GLOBAL"]["accounts_on_client"] = str(self.accounts_on_client)
                with open('settings.ini', 'w') as configfile:
                    config.write(configfile)
            except Exception as e:
                logger2.error("НЕ УДАЛОСЬ СОХРАНИТЬ target_telegram_path accounts_on_client")
                logger2.critical(e)
            try:
                os.startfile(self.target_telegram_path)
            except Exception:
                subprocess.call(["/usr/bin/open", "-n", "-a", self.target_telegram_path])
            logger2.info("Ожидание 10 сек")
            time.sleep(10)

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
        if win is not None and len(win) > 0:
            logger2.info(f"трансформация PC окна telegram")
            win[0].size = (800, 600)
            win[0].moveTo(1, 1)
            win[0].show()
            logger2.info("Ожидание 12 сек")
            time.sleep(12)
            if self.accounts_on_client == 1:
                logger2.info(f"click PC по русски")
                pyautogui.click(400, 488, interval=1)  # по русски
                time.sleep(self.SEC_SLEEP)
                logger2.info(f"click PC начать общение")
                pyautogui.click(400, 440, interval=1)  # начать общение
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC по номеру")
            pyautogui.click(400, 493, interval=1)  # по номеру
            time.sleep(self.SEC_SLEEP)
            raw_phone_number = self.phone_number.replace("+7", "").replace(" ", "")
            clear_phone_number = raw_phone_number.replace("(", "").replace(")", "")
            logger2.info(f"PC ввод номер нелефона без +7, после по номеру")
            pyautogui.typewrite(clear_phone_number, 0.3)  # номер нелефона без +7
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC продолжить")
            pyautogui.click(400, 408, interval=1)  # продолжить
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"PC find_number() получение кода тг, после продолжить")
            if not debug:
                code_tg = self.get_tg_code()
            else:
                code_tg = code_tg_debug
            logger2.info(f"PC find_number() {code_tg} ввод")
            pyautogui.typewrite(str(code_tg), 0.3)  # код из тг
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC продолжить, после {code_tg} ввод")
            pyautogui.click(400, 408, interval=1)  # продолжить
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"PC Ввод {self.PASSWORD}, после продолжить")
            pyautogui.typewrite(self.PASSWORD, 0.3)  # пароль
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC продолжить")
            pyautogui.click(400, 408, interval=1)  # продолжить
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC три полоски")
            pyautogui.click(36, 52, interval=1)  # три полоски
            time.sleep(self.SEC_SLEEP // 2)
            logger2.info(f"click PC настройки")
            pyautogui.click(103, 426, interval=1)  # настройки
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC продвинутые настройки")
            pyautogui.click(287, 437, interval=1)  # продвинутые
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC тип соединения")
            pyautogui.click(305, 167, interval=1)  # тип соед
            time.sleep(self.SEC_SLEEP // 2)
            logger2.info(f"click PC использовать собственный прокси")
            pyautogui.click(300, 251, interval=1)  # исп собствен прокси
            time.sleep(self.SEC_SLEEP // 2)
            logger2.info(f"click PC HTTP")
            pyautogui.click(290, 203, interval=1)  # HTTP
            time.sleep(self.SEC_SLEEP // 2)
            logger2.info(f"Ввод PC ip прокси")
            pyautogui.typewrite(self.PROXY["ip"], 0.3)  # ip прокси
            time.sleep(self.SEC_SLEEP // 2)
            pyautogui.typewrite(["tab"])
            logger2.info(f"Ввод PC порт прокси через tab")
            pyautogui.typewrite(self.PROXY["port"], 0.3)  # порт прокси
            time.sleep(self.SEC_SLEEP // 2)
            pyautogui.typewrite(["tab"])
            logger2.info(f"Ввод PC логин прокси через tab")
            pyautogui.typewrite(self.PROXY["login"], 0.3)  # логин прокси
            time.sleep(self.SEC_SLEEP // 2)
            pyautogui.typewrite(["tab"])
            logger2.info(f"Ввод PC пароль прокси через tab")
            pyautogui.typewrite(self.PROXY["password"], 0.3)  # пароль прокси
            time.sleep(self.SEC_SLEEP // 2)
            logger2.info(f"click PC сохранить прокси")
            pyautogui.click(495, 512, interval=1)  # сохранить прокси
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC закрыть прокси")
            pyautogui.click(368, 537, interval=1)  # закрыть прокси
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC закрыть продвинутые настройки")
            pyautogui.click(230, 77, interval=1)  # закрыть продв настройки
            time.sleep(self.SEC_SLEEP)
            logger2.info(f"click PC три точки")
            pyautogui.click(527, 78, interval=1)  # три точки
            time.sleep(self.SEC_SLEEP // 2)
            logger2.info(f"click PC добавить аккаунт")
            pyautogui.click(419, 110, interval=1)  # добавить аккаунт
            time.sleep(self.SEC_SLEEP)
            self.accounts_on_client += 1
        else:
            logger2.critical(f"login_telegram_client не найдено окно telegram {win}")
            self.collect_error_data(f"login_telegram_client не найдено окно telegram {win}")
            # input("Введите что либо, чтобы продолжить")
            exit(f"login_telegram_client не найдено окно telegram {win}")
        time.sleep(self.SEC_SLEEP)

    def confirm_client(self):
        time.sleep(self.SEC_SLEEP)
        #  назад
        with self.d.watch_context() as ctx:
            logger2.info(f"click подтвердить добавленный аккаунт")
            ctx.when('//*[@content-desc="Назад"]').click()
            time.sleep(self.delay_sleep)
        with self.d.watch_context() as ctx:
            time.sleep(self.SEC_SLEEP // 2)
            ctx.when('//android.widget.TextView[@text="Да, это я"]').click()
        time.sleep(self.SEC_SLEEP)

    def quit_telegram_phone(self):
        # logger2.warning("ВЫ ДЕЙСТВИТЕЛЬНО ХОТИТЕ ВЫЙТИ ИЗ АККАУНТА НА ТЕЛЕФОНЕ?")
        # logger2.warning("ПРОВЕРЬТЕ ВХОД В АККАУНТ НА ПК ИЛИ СОХРАНИТЕ(ВОЙДИТЕ) ВРУЧНУЮ")
        # input("Введите НЕ пустую строку чтобы продолжить или отмеить выход на телефоне")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//*[@content-desc="Открыть меню навигации"]',
                         "quit_telegram_phone click Открыть меню навигации",
                         "quit_telegram_phone Поиск Открыть меню навигации")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Настройки"]',
                         "click Настройки",
                         "Поиск Настройки")
        time.sleep(self.delay_sleep)
        self.check_click('//*[@content-desc="Дополнительные параметры"]',
                         "click Дополнительные параметры",
                         "Поиск Дополнительные параметры")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Выход"]',
                         "click Выход",
                         "Поиск Выход")
        time.sleep(self.SEC_SLEEP // 2)
        self.check_click('//android.widget.FrameLayout[@text="Выход"]',
                         "click Выход 2",
                         "Поиск Выход 2")
        time.sleep(self.delay_sleep)
        with self.d.watch_context() as ctx:
            #  выход
            ctx.when(
                '/hierarchy/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/'
                'android.widget.LinearLayout[1]/android.widget.FrameLayout[2]/android.widget.TextView[2]').click()
        time.sleep(self.SEC_SLEEP)

    def reinstall_telegram(self):
        # logger2.warning("ВЫ ДЕЙСТВИТЕЛЬНО ХОТИТЕ ВЫЙТИ ИЗ АККАУНТА НА ТЕЛЕФОНЕ И ПЕРЕУСТАНОВИТЬ ТЕЛЕГРАМ?")
        # logger2.warning("ПРОВЕРЬТЕ ВХОД В АККАУНТ НА ПК ИЛИ СОХРАНИТЕ(ВОЙДИТЕ) ВРУЧНУЮ")
        # confirm_input = input("Введите НЕ пустую строку чтобы продолжить или отмените выход на телефоне: ")
        # if confirm_input is None or confirm_input == "" or len(confirm_input) < 1:
        #    return False
        # logger2.info("reinstall_telegram click по центральной кнопке - выход")
        with self.d.watch_context() as ctx:
            ctx.when('//*[@resource-id="com.android.systemui:id/center_group"]').click()
            time.sleep(self.SEC_SLEEP)
            logger2.info("click center_group")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Google Play"]',
                         "reinstall_telegram click Google Play",
                         "reinstall_telegram Поиск Google Play")
        time.sleep(self.SEC_SLEEP)
        logger2.info("click Поиск")
        time.sleep(self.delay_sleep)
        with self.d.watch_context() as ctx:
            ctx.when('//android.widget.TextView[@text="Поиск"]').click()
            time.sleep(self.SEC_SLEEP)
            logger2.info("click Поиск в Google Play")
        time.sleep(self.SEC_SLEEP)
        with self.d.watch_context() as ctx:
            ctx.when('//*[@content-desc="Поиск в Google Play"]').click()
            time.sleep(self.SEC_SLEEP)
        time.sleep(self.SEC_SLEEP)
        with self.d.watch_context() as ctx:
            ctx.when('//android.widget.TextView[@text="Поиск приложений и игр"]').click()
            time.sleep(self.SEC_SLEEP)
        time.sleep(self.SEC_SLEEP)
        logger2.info("ввод telegram")
        self.d.send_keys("telegram")
        time.sleep(self.SEC_SLEEP // 2)
        logger2.info("ввод enter")
        self.d.press("enter")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//*[@content-desc="Telegram\nУстановлено\n"]',
                         "click Telegram\nУстановлено\n",
                         "reinstall_telegram Поиск Telegram\nУстановлено\n")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//android.widget.TextView[@text="Удалить"]',
                         "click Удалить",
                         "Поиск Удалить")
        time.sleep(self.delay_sleep)
        self.check_click('//android.widget.TextView[@text="Удалить"]',
                         "click Удалить 2",
                         "Поиск Удалить 2", False)
        logger2.info("ожидание 6 сек")
        time.sleep(6)
        self.check_click('//android.widget.TextView[@text="Установить"]',
                         "click Удалить 2",
                         "Поиск Удалить 2")
        time.sleep(self.SEC_SLEEP // 2)
        while self.d.exists(text="Отмена"):
            logger2.info("ожидание установки")
            time.sleep(self.SEC_SLEEP)
        time.sleep(self.SEC_SLEEP)
        while self.d.exists(text="% из "):
            logger2.info("ожидание установки")
            time.sleep(self.SEC_SLEEP)
        time.sleep(self.SEC_SLEEP)
        while self.d.exists(text="Установка"):
            logger2.info("ожидание установки")
            time.sleep(self.SEC_SLEEP)
        time.sleep(self.SEC_SLEEP)
        while self.d.exists(textContains="Подождите"):
            logger2.info("ожидание установки")
            time.sleep(self.SEC_SLEEP)
        return True

    def open_telegram(self):
        logger2.info("Дача разрешений телеграм на телефоне")
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.BLUETOOTH_CONNECT").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.GET_ACCOUNTS").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.READ_CONTACTS").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.READ_EXTERNAL_STORAGE").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.WRITE_CONTACTS").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.WRITE_EXTERNAL_STORAGE").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.ACCESS_NETWORK_STATE").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.AUTHENTICATE_ACCOUNTS").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.FOREGROUND_SERVICE").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.MANAGE_ACCOUNTS").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.READ_PROFILE").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.READ_PHONE_NUMBERS").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.READ_PHONE_STATE").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.READ_CALL_LOG").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger "
                                  "android.permission.ACCESS_BACKGROUND_LOCATION").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.ACCESS_COARSE_LOCATION").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.ACCESS_FINE_LOCATION").output)
        logger2.info(self.d.shell("pm grant org.telegram.messenger android.permission.CALL_PHONE").output)
        logger2.info("Запуск телеграм на телефоне")
        logger2.info("open_telegram click по цетральной кнопке - выход")
        with self.d.watch_context() as ctx:
            ctx.when('//*[@resource-id="com.android.systemui:id/center_group"]').click()
            time.sleep(self.SEC_SLEEP)
        self.d.app_stop("com.android.vending")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//android.widget.TextView[@text="Google Play"]',
                         "click Google Play",
                         "Поиск Google Play")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//android.widget.TextView[@text="Поиск"]',
                         "click Поиск",
                         "Поиск Поиск")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//android.widget.TextView[@text="Поиск приложений и игр"]',
                         "click Поиск приложений и игр",
                         "Поиск Поиск приложений и игр")
        time.sleep(self.SEC_SLEEP)
        logger2.info("ввод telegram")
        self.d.send_keys("telegram")
        time.sleep(self.delay_sleep)
        logger2.info("ввод enter")
        self.d.press("enter")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//*[@content-desc="Telegram\nУстановлено\n"]',
                         r"Click Telegram\nУстановлено\n",
                         r"поиск Telegram\nУстановлено\n")
        time.sleep(self.SEC_SLEEP)
        self.check_click('//android.widget.TextView[@text="Обновить"]',
                         "click Обновить",
                         "Поиск Обновить", critical=False)
        try_n = 0
        while not self.d.xpath('//android.widget.TextView[@text="Открыть"]').exists:
            if try_n >= 200:
                logger2.error("Не вижу кнопки Открыть, просьба открыть телеграм самостоятельно")
                logger2.info("Ожидание 6 сек")
                time.sleep(6)
                return
            time.sleep(self.SEC_SLEEP)
            try_n += self.SEC_SLEEP
        self.check_click('//android.widget.TextView[@text="Открыть"]',
                         "click Открыть",
                         "Поиск Открыть")
        logger2.info("Ожидание 6 сек")
        time.sleep(6)

    # def reinstall_sim_card():
    # logger2.warning("УСТАНОВИТЕ НОВУЮ СИМКУ")
    # input("Введите что либо или просто нажмите Enter для продолжения")
    # logger2.warning("измените текущий гугл аккаунт в настройках и удалите старый при необходимости")
    # input("Введите что либо или просто нажмите Enter для продолжения")
    # logger2.info("Запуск телеграм на телефоне")
    # with self.d.watch_context() as ctx:
    #    ctx.when('//android.widget.TextView[@text="Открыть"]').click()
    # time.sleep(10)


if __name__ == "__main__":
    print("Запущен как deamon")
    print(os.getenv("server_url"))
    SEC_SLEEP = 3
    TIMEOUT_N = 3
    PASSWORD = "1WSXwsx2"
    NAMES = ["ева"]
    PROXY = {"ip": "",
             "port": "",
             "login": "",
             "password": ""}

    DEVICE = ""

    phone_number = ""
    accounts_on_client = 0
    services_settings = ""
    target_telegram_path = ""
    try:
        config = configparser.ConfigParser()  # создаём объекта парсера
        config.read("settings.ini")
        SEC_SLEEP = int(config["GLOBAL"]["SEC_SLEEP"])
        TIMEOUT_N = int(config["GLOBAL"]["TIMEOUT_N"])
        PASSWORD = config["GLOBAL"]["PASSWORD"]

        NAMES = config["GLOBAL"]["NAMES"].split(",")

        PROXY = dict(config["PROXY"])

        target_telegram_path = config["GLOBAL"]["target_telegram_path"]
        accounts_on_client = int(config["GLOBAL"]["accounts_on_client"])

        DEVICE = config["GLOBAL"]["device"]
    except:
        logger2.error("Не удалось загрузить настройки")
    worker = TelegramService(device=DEVICE, sec_sleep=SEC_SLEEP, timeout_n=TIMEOUT_N, names=NAMES,
                             password=PASSWORD, accounts_on_client=0, proxy=PROXY, target_telegram_path="",
                             phone_number=input("Введите номер телефона без +7 8 в начале и других символов: "))
    # worker.set_2fa()
    # worker.get_tg_code()
    # worker.test_manual_code_enter_sms()
    print(worker.login_telegram_client_on_server())
    worker.confirm_client()
    response_func = worker.reinstall_telegram()
    if not response_func:
        logger2.info("Вы отменили переустановку telegram")
