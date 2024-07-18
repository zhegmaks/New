# -*- coding: utf-8 -*-
from aiogram import Bot, Dispatcher, executor, types
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()

class Form(StatesGroup):
    file_id = State()  

API_TOKEN = ''  
PASSWORD = 'admin123'  

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()
url_list = []
user_list = [316398758]  
TIMEOUT_PING = 10  
INTERVAL_MINUTES = 5

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
        f.write(file.read())
    with open('list.txt', 'r') as f:
        global url_list
        url_list = [line.strip() for line in f.readlines()]
    scheduler.remove_all_jobs()
    scheduler.add_job(check_urls, 'interval', minutes=INTERVAL_MINUTES)
    scheduler.add_job(check_urls_hourly, 'cron', hour='8', minute='0')
    await message.reply("Список ссылок обновлен и проверка инициирована")
    await state.finish()


@dp.message_handler(lambda message: message.text != PASSWORD, state=Form.file_id)
async def wrong_password(message: types.Message, state: Form):
    await message.reply("Введите корректный пароль")
    await state.finish()

@dp.message_handler(commands=['getlist'])
async def get_list(message: types.Message):
    if message.get_args() == PASSWORD:
        with open('list.txt', 'r') as f:
            await bot.send_message(message.from_user.id, f.read())
    else:
        await message.reply("Некорректный пароль")

async def check_urls():
    for line in url_list:
        parts = line.split(' - ')
        url = parts[-1]
        name = ' - '.join(parts[:-1])
        try:
            response = requests.get(url)
            response.raise_for_status()
            mark_url(name, 'available', url)
            await asyncio.sleep(TIMEOUT_PING)
        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            if not is_marked_unavailable(name):
                for user in user_list:
                    await bot.send_message(user, f"{name} - {url} приложение недоступно в сторе")
                await asyncio.sleep(TIMEOUT_PING)
                mark_url(name, 'unavailable', url)

async def check_urls_hourly():
    for line in url_list:
        parts = line.split(' - ')
        url = parts[-1]
        name = ' - '.join(parts[:-1])
        try:
            response = requests.get(url)
            response.raise_for_status()
            for user in user_list:
                await bot.send_message(user, "Чекер работает корректно")
            mark_url(name, 'available', url)
            break  
        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            if not is_marked_unavailable(name):
                for user in user_list:
                    await bot.send_message(user, f"{name} - приложение недоступно в сторе")
                await asyncio.sleep(TIMEOUT_PING)
                mark_url(name, 'unavailable', url)

def mark_url(name, status, url):
    with open('list.txt', 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        for i, line in enumerate(lines):
            if url in line:
                lines[i] = f"{name} - {status} - {url}\n"
        f.writelines(lines)
        f.truncate()


def is_marked_unavailable(name):
    with open('list.txt', 'r') as f:
        return any(f"{name} - unavailable" in line for line in f)


if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
