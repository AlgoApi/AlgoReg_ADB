import logger
import telegram_service
import uiautomator2 as u2
import datetime
import configparser


logger2 = logger.logger2


SEC_SLEEP = 4
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


def set_settings() -> str:
    global SEC_SLEEP, TIMEOUT_N, PASSWORD, NAMES, PROXY, target_telegram_path, accounts_on_client, services_settings
    global DEVICE

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

    logger2.info("TIMESTAMP")

    logger2.info(f"Пауза: {SEC_SLEEP}\n"
                 f"Попытки: {TIMEOUT_N}\n"
                 f"Пароль: {PASSWORD}\n"
                 f"Имена: {NAMES}\n"
                 f"Прокси: {PROXY}\n"
                 f"Путь к предыдущему телеграмм exe: {target_telegram_path}\n"
                 f"Текущее кол-во аккаунтов на клиенте по заданному пути: {accounts_on_client}\n"
                 f"Имя устройства {DEVICE}")

    logger2.info("TIMESTAMP")

    accepted_settings = 0
    if SEC_SLEEP > 1 and TIMEOUT_N > 0:
        accepted_settings += 3
        if PASSWORD is not None and PASSWORD != "":
            accepted_settings += 1
            if NAMES is not None and len(NAMES) > 0:
                accepted_settings += 1
                if PROXY is not None:
                    accepted_proxy_values = 0
                    for value in PROXY.values():
                        if value != "":
                            accepted_proxy_values += 1
                    if accepted_proxy_values == len(PROXY.values()):
                        accepted_settings += 1
                    if len(PROXY.values()) == 4:
                        accepted_settings += 1
    if accepted_settings != 7:
        settings_input = "НЕверно заданы настройки"
        logger2.warning("НЕверно заданы настройки")
    else:
        settings_input = input("Введите НЕ пустую строку для настройки: ")

    while settings_input is not None and settings_input != "":
        logger2.info("Настройка")
        sec_sleep_input = input("Введите в секундах, целым и не отрицательным числом \n"
                                "сколько будет пауза перед следующим действием \n"
                                "или останется по умолчанию 4 секунды\n "
                                "(отправьте пустую строку(Enter) для значения по умолчанию): ")
        SEC_SLEEP = int(sec_sleep_input) if sec_sleep_input is not None and sec_sleep_input.isdigit() else 4
        logger2.info(f"Теперь значение паузы: {SEC_SLEEP}")

        timeout_n_input = input("Введите кол-во попыток целым и не отрицательным числом \n"
                                "для поиска нужных элементов \n"
                                "или останется по умолчанию 3 попытки\n "
                                "(отправьте пустую строку(Enter) для значения по умолчанию): ")
        TIMEOUT_N = int(timeout_n_input) if timeout_n_input is not None and timeout_n_input.isdigit() else 3
        logger2.info(f"Теперь значение попыток: {TIMEOUT_N}")

        password_input = input("Введите пароль двухфайкторной аутентификации\n"
                               "(отправьте пустую строку(Enter) для значения по умолчанию '1WSXwsx2'): ")
        PASSWORD = password_input if password_input is not None and password_input != "" else "1WSXwsx2"
        logger2.info(f"Теперь пароль: {PASSWORD}")

        while True:
            device_input = input("Введите имя Android устройства (можно получить в консоли: adb devices): ")
            DEVICE = device_input if device_input is not None and device_input != "" else "НЕВЕРНО ЗАДАНО ИМЯ"
            if DEVICE == "НЕВЕРНО ЗАДАНО ИМЯ":
                logger2.warning("НЕВЕРНО ЗАДАНО ИМЯ")
                continue
            logger2.info(f"Теперь имя Android устройства: {DEVICE}")
            break

        good_names = False
        while not good_names:
            names_input = input("Введите НЕ пустую строку для настройки имён: ")
            if names_input is not None and names_input != "":
                NAMES.clear()
                while names_input is not None and names_input != "":
                    names_input = input("Введите имя без пробелов или пустую строку для завершения настройки имён: ")
                    if names_input != "":
                        NAMES.append(names_input)
            if len(NAMES) < 1:
                logger2.error(f"заполните имена {NAMES}")
            else:
                good_names = True

        PROXY = {"ip": input("Введите ip прокси: "),
                 "port": input("Введите порт прокси: "),
                 "login": input("Введите login прокси: "),
                 "password": input("Введите password прокси: ")}

        logger2.info(f"Теперь прокси: {PROXY}")

        account_path_settings_input = input("Введите НЕ пустую строку для настройки пути"
                                            " к рабочей текущей папке телеграм\n"
                                            "(Иначе начнёт с последним сохранённый путём до телеграм\n"
                                            "если сохранённого нет, создаст новый): ")
        if account_path_settings_input is not None and account_path_settings_input != "":
            accounts_on_client_input = input("Введите кол-во аккаунтов на этом клиенте телеграм "
                                             "целым не отрицательынм числом\n"
                                             "(ввод иного или пустой строки, "
                                             "оставляет значение по умолчанию): ")
            accounts_on_client = int(accounts_on_client_input) if accounts_on_client_input.isdigit() else 0
            print(f"Теперь кол-во аккаунтов на этом клиенте телеграм: {accounts_on_client}")
            target_telegram_path_input = input("Введите путь к папке с telegram.exe, кроме текущей дериктории и начиная"
                                               "с ней же\n Пример: telegram2024-12-26_14.12.32_1 (да, просто папка"
                                               "если в ней есть нужный telegram.exe)"
                                               "\nУЧТИТЕ, у вас уже должен быть открыть telegram desctop из этой папки,"
                                               "также должно быть открыто окно добавления нового "
                                               "аккаунта(этап с qr-кодом)"
                                               "\n(ввод пустой строки, оставляет значение по умолчанию): ")
            if target_telegram_path_input is not None and target_telegram_path_input != "":
                target_telegram_path = target_telegram_path_input
            else:
                target_telegram_path = ""
            print(f"Теперь путь к папке с telegram.exe: {accounts_on_client}")

        logger2.info("Настройка завершена")

        logger2.info("TIMESTAMP")

        logger2.info(f"Пауза: {SEC_SLEEP}\n"
                     f"Попытки: {TIMEOUT_N}\n"
                     f"Пароль: {PASSWORD}\n"
                     f"Имена: {NAMES}\n"
                     f"Прокси: {PROXY}\n"
                     f"Путь к предыдущему телеграмм exe: {target_telegram_path}\n"
                     f"Текущее кол-во аккаунтов на клиенте по заданному пути: {accounts_on_client}\n"
                     f"Имя устройства {DEVICE}")

        logger2.info("TIMESTAMP")

        accepted_settings = 0
        if SEC_SLEEP > 1 and TIMEOUT_N > 0:
            accepted_settings += 3
            if PASSWORD is not None and PASSWORD != "":
                accepted_settings += 1
                if NAMES is not None and len(NAMES) > 0:
                    accepted_settings += 1
                    if PROXY is not None:
                        accepted_proxy_values = 0
                        for value in PROXY.values():
                            if value != "":
                                accepted_proxy_values += 1
                        if accepted_proxy_values == len(PROXY.values()):
                            accepted_settings += 1
                        if len(PROXY.values()) == 4:
                            accepted_settings += 1
        if accepted_settings != 7:
            settings_input = "НЕверно заданы настройки"
            logger2.warning("НЕверно заданы настройки")
            continue

        try:
            config = configparser.ConfigParser()  # создаём объекта парсера
            if 'GLOBAL' not in config:
                config.add_section('GLOBAL')
            if 'PROXY' not in config:
                config.add_section('PROXY')
            config["GLOBAL"]["SEC_SLEEP"] = str(SEC_SLEEP)
            config["GLOBAL"]["TIMEOUT_N"] = str(TIMEOUT_N)
            config["GLOBAL"]["PASSWORD"] = str(PASSWORD)

            config["GLOBAL"]["NAMES"] = ",".join(NAMES)

            config["PROXY"] = PROXY

            config["GLOBAL"]["target_telegram_path"] = str(target_telegram_path)
            config["GLOBAL"]["accounts_on_client"] = str(accounts_on_client)

            config["GLOBAL"]["device"] = str(DEVICE)
            # Сохраняем в файл
            with open('settings.ini', 'w') as configfile:
                config.write(configfile)
        except Exception as err:
            logger2.error(f"Не удалось сохранить настройки {err}")

        settings_input = input("Введите НЕ пустую строку для настройки: ")

    good_services = False
    accepted_services = ""
    while not good_services:
        print("")
        print("Настройка сервисов для регистрации")
        print("Доступные сервисы для регистрации и их номер: \n"
              "telegram - 1")
        services_settings = str(input("Введите номера(целые, не отрицательные число) сервисов для регистрации "
                                      "в строку без пробелов и иных символов: "))
        while services_settings is None or len(services_settings) < 1:
            services_settings = str(input("Введите номера(целые, не отрицательные число) сервисов для регистрации "
                                          "в строку без пробелов и иных символов: "))
        accepted_services = 0
        for el in services_settings:
            match el:
                case "1":
                    print("Выбран Telegram")
                    accepted_services += 1
                case _:
                    print(f"Недействительный номер сервиса: {el}")
                    break
        if accepted_services == len(services_settings):
            logger2.info(f"Выбранные сервисы: {services_settings}")
            break

    return str(accepted_services)


def send_except(msg_text, err):
    d = u2.connect(DEVICE)
    imagebin = d.screenshot()
    formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    imagebin.save(f"error_{formatted_datetime}.png")

    xml = d.dump_hierarchy()
    # print(xml)
    xml_path = f"xml_dump_{formatted_datetime}.xml"
    with open(xml_path, "w+") as file:
        file.write(xml)

    logger.send_error_via_tg(f"error_{formatted_datetime}.png", f"{msg_text}\n{err}", xml_path)
    d.stop_uiautomator()


def init_telegram_worker(telegram_worker):
    try:
        telegram_worker.open_telegram()
    except Exception as err:
        logger2.exception(f"TelegramWorker open_telegram FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker open_telegram FATAL ERROR :", err)
    try:
        telegram_worker.login_form()
    except Exception as err:
        logger2.exception(f"TelegramWorker login_form FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker login_form FATAL ERROR :", err)
    try:
        telegram_worker.set_name()
    except Exception as err:
        logger2.exception(f"TelegramWorker set_name FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker set_name FATAL ERROR :", err)
    try:
        telegram_worker.skip_contacts()
    except Exception as err:
        logger2.exception(f"TelegramWorker skip_contacts FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker skip_contacts FATAL ERROR :", err)
    try:
        telegram_worker.set_2fa()
    except Exception as err:
        logger2.exception(f"TelegramWorker set_2fa FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker set_2fa FATAL ERROR :", err)
    try:
        telegram_worker.login_telegram_client_on_server()
    except Exception as err:
        logger2.exception(f"TelegramWorker login_telegram_client FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker login_telegram_client FATAL ERROR :", err)
    try:
        logger2.warning("ВОЙДИТЕ В АККАУНТ НА ПК")
        input("Если вы вошли в аккаунт на пк, то введите что угодно, чтобы продолжить: ")
        telegram_worker.confirm_client()
    except Exception as err:
        logger2.exception(f"TelegramWorker confirm_client FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker confirm_client FATAL ERROR :", err)
    #try:
    #    telegram_worker.quit_telegram_phone()
    #except Exception as err:
    #    logger2.exception(f"TelegramWorker quit_telegram_phone FATAL ERROR : %s", err, exc_info=True)
    #    send_except("TelegramWorker quit_telegram_phone FATAL ERROR :", err)
    try:
        response_func = telegram_worker.reinstall_telegram()
        if not response_func:
            logger2.info("Вы отменили переустановку telegram")
    except Exception as err:
        logger2.exception(f"TelegramWorker reinstall_telegram FATAL ERROR : %s", err, exc_info=True)
        send_except("TelegramWorker reinstall_telegram FATAL ERROR :", err)
    return True


if __name__ == "__main__":
    services = set_settings()

    TelegramWorker = None

    logger.DEVICE = DEVICE

    for el in services:
        match el:
            case "1":
                TelegramWorker = telegram_service.TelegramService(sec_sleep=SEC_SLEEP, timeout_n=TIMEOUT_N,
                                                                  password=PASSWORD, names=NAMES,
                                                                  proxy=PROXY,
                                                                  accounts_on_client=accounts_on_client,
                                                                  target_telegram_path=target_telegram_path,
                                                                  device=DEVICE)
            case _:
                logger2.error(f"Недействительный номер сервиса: {el}")

    next_question = str(input("Введите НЕ пустую строку, чтобы продолжить или завершить работу: "))
    while next_question is not None and len(next_question) > 0:
        logger2.warning("УСТАНОВИТЕ НОВУЮ СИМКУ")
        input("Введите что либо или просто нажмите Enter для продолжения")
        logger2.warning("измените текущий гугл аккаунт в настройках и удалите старый при необходимости")
        input("Введите что либо или просто нажмите Enter для продолжения")
        logger2.warning("Убедитесь что telegram установлен")
        logger2.warning("Убедитесь что при входе в телеграм вас встречает вверху лого телеграма, а внизу кнопки "
                        "'продолжить на русском' или 'Начать общение', "
                        "если этого нет? то переустановите телеграм вручную")
        input("Введите что либо или просто нажмите Enter для продолжения")

        if TelegramWorker is not None:
            logger2.info(f"init Telegram service: {init_telegram_worker(TelegramWorker)}")

        logger2("Цикл сервисов завершён")
        next_question = str(input("Введите НЕ пустую строку, чтобы продолжить или завершить работу: "))
