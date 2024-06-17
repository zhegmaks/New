# -*- coding: utf-8 -*-
from aiogram import Bot, Dispatcher, executor, types
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiohttp
from datetime import datetime
import time

storage = MemoryStorage()

class Form(StatesGroup):
    file_id = State()  

API_TOKEN = '1058570779:AAHtRKeaOOwHUM07shygcc8m8gL6Gzx7H3k'  # Replace with your token
PASSWORD = 'admin123'  

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()
url_list = []
user_list = [1000337173, 316398758]  # 
TIMEOUT_PING = 10  # 
INTERVAL_MINUTES = 1  # 
last_notification_time = datetime.min  # 

@dp.message_handler(commands=['sendlist'])
async def request_file(message: types.Message):
    password = message.get_args()
    if password == PASSWORD:
        await message.reply("Отправь файл с ссылками list.txt")
        await Form.file_id.set()
    else:
        await message.reply("Некорректный пароль")

@dp.message_handler(state=Form.file_id, content_types=types.ContentTypes.DOCUMENT)
async def handle_file(message: types.Message, state: Form):
    document_id = message.document.file_id
    file_info = await bot.get_file(document_id)
    file = await bot.download_file(file_info.file_path)
    with open('list.txt', 'wb') as f:
        f.write(file.getvalue())
    with open('list.txt', 'r') as f:
        global url_list
        url_list = [line.split(' - ')[0] for line in f.read().splitlines()]
    scheduler.remove_all_jobs()
    scheduler.add_job(check_urls, 'interval', minutes=INTERVAL_MINUTES)
    await message.reply("Список ссылок обновлен и проверка инициирована")
    await state.finish()

@dp.message_handler(lambda message: message.text != PASSWORD, state=Form.file_id)
async def wrong_password(message: types.Message, state: Form):
    await message.reply("Некорректный пароль")
    await state.finish()

@dp.message_handler(commands=['getlist'])
async def get_list(message: types.Message):
    if message.get_args() == PASSWORD:
        with open('list.txt', 'r') as f:
            await bot.send_message(message.from_user.id, f.read())
    else:
        await message.reply("Некорректный пароль")

async def check_urls():
    global last_notification_time
    for url in url_list:
        try:
            response = requests.get(url)
            response.raise_for_status()
            if (datetime.now() - last_notification_time).seconds / 3600 >= 1:
                for user in user_list:
                    await bot.send_message(user, f"Чекер работает корректно")
                last_notification_time = datetime.now()
            mark_url(url, 'available')
            await asyncio.sleep(TIMEOUT_PING)

        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            if not is_marked_unavailable(url):
                for user in user_list:
                    await bot.send_message(user, f"{url} - приложение недоступно в сторе")
                await asyncio.sleep(TIMEOUT_PING)
                mark_url(url, 'unavailable')

def mark_url(url, status):
    with open('list.txt', 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line.startswith(url):
                f.write(f"{url} - {status}\n")
            else:
                f.write(line)
        f.truncate()

def is_marked_unavailable(url):
    with open('list.txt', 'r') as f:
        for line in f:
            if line.startswith(url) and 'unavailable' in line:
                return True
    return False


if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)

"""
# -*- coding: utf-8 -*-
from aiogram import Bot, Dispatcher, executor, types
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiohttp
from datetime import datetime
storage = MemoryStorage()
import time

class Form(StatesGroup):
    file_id = State()  # Состояние для получения file_id от пользователя

API_TOKEN = '1058570779:AAHtRKeaOOwHUM07shygcc8m8gL6Gzx7H3k'
PASSWORD = 'admin123'  # Заменить на свой пароль

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()
url_list = []
user_list = [1000337173] # список пользователей, кого уведомлять в виде id , 316398758
TIMEOUT_PING = 10 # в секундах таймаут на пинг каждого из URL
INTERVAL_MINUTES = 1# в минутах интервал между рассылками

@dp.message_handler(commands=['sendlist'])
async def request_file(message: types.Message):
    password = message.get_args()
    if password == PASSWORD:
        await message.reply("Пожалуйста, отправьте файл.")
        await Form.file_id.set()

@dp.message_handler(commands=['start'])
async def request_file(message: types.Message):
    password = message.get_args()
    if password == PASSWORD:
        await message.reply("Пожалуйста, отправьте файл.")
        await Form.file_id.set()

@dp.message_handler(state=Form.file_id, content_types=types.ContentTypes.DOCUMENT)
async def handle_file(message: types.Message, state: Form):
    document_id = message.document.file_id
    file_info = await bot.get_file(document_id)
    file = await bot.download_file(file_info.file_path)
    with open('list.txt', 'wb') as f:
        f.write(file.getvalue())
    with open('list.txt', 'r') as f:
        global url_list
        url_list = f.read().splitlines()
    scheduler.remove_all_jobs()
    scheduler.add_job(check_urls, 'interval', minutes=INTERVAL_MINUTES)
    await message.reply("Список URL обновлен и проверка запущена.")
    await state.finish()

@dp.message_handler(lambda message: message.text not in [PASSWORD], state=Form.file_id)
async def wrong_password(message: types.Message, state: Form):
    await message.reply("Неверный пароль.")
    await state.finish()

# Команда для получения списка URL
@dp.message_handler(commands=['getlist'])
async def get_list(message: types.Message):
    if message.get_args() == PASSWORD:
        with open('list.txt', 'r') as f:
            await bot.send_message(message.from_user.id, f.read())
    else:
        await message.reply("Неверный пароль.")

async def check_urls():
    for url in url_list:
        try:
            response = requests.get(url)
            response.raise_for_status()
            for user in user_list:
                await bot.send_message(user, f"Чекер работает корректно")
            await asyncio.sleep(TIMEOUT_PING) #10 секунд задержки на пинг url из списка

        except requests.RequestException as e:
            print(f"Error for fetch url {url}: {e}")
            for user in user_list:
                await bot.send_message(user, f"{url} - приложение недоступно.")


# Запуск бота
if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)


Есть функция check_urls() которая пингует приложения ios на сайте и в случае except
присылает пользователям что приложение недоступно, сообщение что Чекер работает корректно (именно в try блоке) в try блоке должно присылаться
не более раза в час это сообщение, остальная часть try блока должна отрабатывать обычно.
Сообщение {url} - приложение недоступно должно присылаться один раз в уведомления, потом в list.txt
данный url как-то помечать и не присылать повторно в except блоке.
Например в list.txt помечать как {url} - available В try блоке если url доступен или {url} - unvailable как недоступный в except блоке помечать. Исправь мой код полностью


"""
