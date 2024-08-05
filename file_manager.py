import os
import configparser

def ensure_config_exists(config_path):
    config = configparser.ConfigParser()

    # Секции и значения по умолчанию
    default_config = {
        'Settings': {
            'theme': 'Light'
        },
        'Paths': {
            'SteamCMD': ''
        }
    }

    # Если конфигурационный файл существует, читаем его
    if os.path.exists(config_path):
        config.read(config_path)

        # Проверка и добавление недостающих секций и параметров
        for section, params in default_config.items():
            if not config.has_section(section):
                config.add_section(section)
            for param, value in params.items():
                if not config.has_option(section, param):
                    config.set(section, param, value)
    else:
        # Если конфигурационный файл не существует, создаем его с значениями по умолчанию
        for section, params in default_config.items():
            config.add_section(section)
            for param, value in params.items():
                config.set(section, param, value)

    # Сохраняем изменения
    with open(config_path, 'w') as configfile:
        config.write(configfile)
