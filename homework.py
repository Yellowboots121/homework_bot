import os
import time
import sys
import logging
import requests
import telegram
from dotenv import load_dotenv
from logging import StreamHandler
from http import HTTPStatus

load_dotenv()

logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filemode='w',
    filename='logfile.log',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
fileHandler = logging.FileHandler("logfile.log")
streamHandler = StreamHandler(stream=sys.stdout)
streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')
LIST_IS_EMPTY = 'Список пустой'
WRONG_HOMEWORK_STATUS = '{homework_status}'
WRONG_DATA_TYPE = 'Неверный тип данных {type}, вместо "dict"'

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

all = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ENDPOINT)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class DataTypeError(Exception):
    """Ошибка, если тип данных не dict."""

    pass


class MessageSendingError(Exception):
    """Ошибка отправки сообщения."""

    pass


class FailedRequestError(Exception):
    """Ошибка запроса API"""

    pass


class EmptyError(Exception):
    """Ответ API пуст"""

    pass


class NoKeyError(Exception):
    """Отсутствует ключ"""

    pass


class WrongDataTypeError(Exception):
    """Ошибка, если тип данных не list."""

    pass


def send_message(bot, message):
    """Отправляет сообщение пользователю в Телегу."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        raise MessageSendingError('Ошибка при отправке сообщеия') from error


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            **dict(url=ENDPOINT, headers=HEADERS, params=params))
    except Exception as error:
        raise FailedRequestError(
            'Ошибка при запросе к основному API') from error

    response_status = response.status_code
    if response_status != HTTPStatus.OK:
        raise logging.error('Ошибка статуса страницы')
    try:
        return response.json()
    except Exception as error:
        raise logging.error(f'Формат не json: {error}')


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) is not dict:
        logging.error('Тип данных ответа от API адреса не dict.')
        raise TypeError('Тип данных ответа от API адреса не dict.')
    try:
        homeworks_list = response['homeworks']
    except KeyError:
        logging.error('В ответе API отсутствует ожидаемый ключ "homeworks".')
        raise KeyError('В ответе API отсутствует ожидаемый ключ "homeworks".')
    try:
        homework = homeworks_list[0]
    except IndexError:
        logging.error('Список работ на проверке пуст.')
        raise IndexError('Список работ на проверке пуст.')
    return homework


def parse_status(homework):
    """Извлекает из информации о конкретной."""
    """домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        message = 'Ключ homework_name недоступен'
        logging.error(message)
        raise KeyError(message)
    if 'status' not in homework:
        message = 'Ключ status недоступен'
        logging.error(message)
        raise KeyError(message)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        raise NameError(WRONG_HOMEWORK_STATUS.format(homework_status))

    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    for key in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ENDPOINT):
        if key is None:
            logging.error('Глобальная переменная отсутсвует')
            return False
        if not key:
            logging.error('Глобальная переменная пучта')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise logging.error('Ошибка переменной. Смотрите логи.')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            logging.info(f'Сообщение {message} отправлено'.format(message))
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logging.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
