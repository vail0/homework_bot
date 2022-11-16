import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Message \'{message}\' sent')
    except Exception as error:
        logger.error(f'Бот не смог отправить сообщение: ошибка {error}')


# print(send_message(bot = telegram.Bot(token=TELEGRAM_TOKEN),
#       message = 'test_message'))


def get_api_answer(current_timestamp):
    """Получение ответа от Яндекс Практикума."""
    url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        hw_statuses = requests.get(url, headers=headers, params=params)
    except Exception as error:
        logging.error(f'Ошибка при запросе к API Яндекса {error}')

    if hw_statuses.status_code != 200:
        raise Exception(f'Получен Неверный код {hw_statuses.status_code}')

    try:
        return hw_statuses.json()
    except Exception as error:
        raise Exception(f'Ошибка перевода в json {error}')

# print(get_api_answer(1549962000))


def check_response(response):
    """Проверка корректности полученого json ответа."""
    try:
        resp = response.get('homeworks')
        if resp == []:
            logging.error('Нет дз за указанный период')
            return None
            # raise Exception('Отсутствует дз за текущий срок')
        else:
            logging.info('')
            return resp[0]

    except Exception:
        logging.error('Ошибка в присланной форме ответа')
        # return None
        if not isinstance(response, dict):
            raise TypeError('Убедитесь, что передаётся словарь')
        else:
            raise Exception('Прислана неверная форма')


# print(check_response(get_api_answer(1549962000)))
# print(check_response(get_api_answer(1668164848)))

def parse_status(homework):
    """Перевод статуса дз из json на человеческий язык."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if (homework_name is None) or (homework_status is None):
        raise Exception(f'Имя или статус отсутсвуют {homework}')

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'

# print(parse_status(check_response(get_api_answer(1549962000))))
# print(parse_status(check_response(get_api_answer(1668164848))))


def namestr(obj, namespace):
    """Извлечение названия переменной."""
    return [name for name in namespace if namespace[name] is obj]


def check_tokens():
    """Проверка наличия токенов пользователя."""
    token_list = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    )
    for token in token_list:
        if token is None:
            logger.critical(f'Отсутствует {namestr(token, globals())[0]}')
            return False
        else:
            logger.debug(f'{namestr(token, globals())[0]} существует')
    return True

# check_tokens()


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        raise Exception('Остутствуют ключи')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework is not None:
                message = parse_status(homework)
            else:
                message = 'Нет ответа'

        except Exception as error:
            message = f'Сбой в работе программы: {error}'

        finally:
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
