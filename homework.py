import os
import time
import sys
import logging
import requests
import telegram
from dotenv import load_dotenv
from logging import StreamHandler

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
GLOBAL_VARIABLE_IS_MISSING = 'Отсутствует глобальная переменная'
GLOBAL_VARIABLE_IS_EMPTY = 'Пустая глобальная переменная'
LIST_IS_EMPTY = 'Список пустой'
WRONG_HOMEWORK_STATUS = '{homework_status}'
WRONG_DATA_TYPE = 'Неверный тип данных {type}, вместо "dict"'

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class DataTypeError(Exception):
    """Ошибка, если тип данных не dict."""

    pass


def send_message(bot, message):
    """Отправляет сообщение пользователю в Телегу."""
    return bot.send_message(
        chat_id=TELEGRAM_CHAT_ID, text=message
    )


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time(0))
    params = {'from_date': timestamp}
    all_params = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        response = requests.get(**all_params)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        new_url = 'https://api.thedogapi.com/v1/images/search'
        response = requests.get(new_url)

    response_status = response.status_code
    if response_status != 200:
        raise logging.error('Ошибка статуса страницы')
    try:
        return response.json()
    except Exception as error:
        raise logging.error(f'Формат не json: {error}')


def check_response(response):
    """Проверяет ответ API на корректность."""
    if response['homeworks']:
        return response['homeworks'][0]
    else:
        raise IndexError(LIST_IS_EMPTY)


def parse_status(homework):
    """Извлекает из информации о конкретной."""
    """домашней работе статус этой работы."""
    if not isinstance(homework, dict):
        raise DataTypeError(WRONG_DATA_TYPE.format(type(homework)))
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
            logging.error(GLOBAL_VARIABLE_IS_MISSING)
            return False
        if not key:
            logging.error(GLOBAL_VARIABLE_IS_EMPTY)
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
            logging.info(homework)
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except KeyboardInterrupt:
            message = 'Прерывание клавиатуры'
            logging.info(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            message = 'Бот работает'
            logging.info(message)
        finally:
            time.sleep(RETRY_TIME)
        logging.info(f'Сообщение {message} отправлено'.format(message))


if __name__ == '__main__':
    main()
