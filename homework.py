import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

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
        logger.info('Message was sent')
    except Exception as error:
        logger.error(f'Бот не смог отправить сообщение: ошибка {error}')


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

    if hw_statuses.status_code != HTTPStatus.OK:
        raise Exception(f'Получен Неверный код {hw_statuses.status_code}')

    try:
        return hw_statuses.json()
    except Exception as error:
        raise Exception(f'Ошибка перевода в json {error}')


def check_response(response):
    """Проверка корректности полученого json ответа."""
    if not isinstance(response, dict):
        raise TypeError('Убедитесь, что передаётся словарь')

    try:
        hwks = response.get('homeworks')
    except Exception:
        raise KeyError('Прислана неверная форма')

    if not isinstance(hwks, list):
        raise TypeError('Убедитесь, что передаётся список в словаре')

    logging.info('Ответ корректен')
    return hwks


def parse_status(homework):
    """Перевод статуса дз из json на человеческий язык."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
    except Exception:
        raise KeyError('Ошибка получения имени или статуса')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов пользователя."""
    token_list = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    )
    for token in token_list:
        if token is None:
            logger.critical('Отсутствует токен, проверьте файл .env')
            return False

    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise Exception('Остутствуют ключи')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1549962000
    old_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            # print(response)
            homework = check_response(response)
            print(homework)
            if not homework:
                logging.info('Нет дз за указанный период')
                message = 'За указаный период нет изменений дз'
            else:
                message = parse_status(homework[0])

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

        finally:
            if message != old_message:
                send_message(bot, message)
                old_message = message

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
