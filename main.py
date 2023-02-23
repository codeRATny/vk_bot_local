from vkbottle.bot import Bot, Message
from vk_api.utils import get_random_id
import asyncio

from pathlib import Path
import datetime
from typing import Optional

days = {'понедельник':0, 'вторник':1, 'среда':2, 'четверг':3, 'пятница':4, 'суббота':5, 'воскресенье':6}
days_re = {0:'понедельник', 1:'вторник', 2:'среда', 3:'четверг', 4:'пятница', 5:'суббота', 6:'воскресенье'}
tasks = {}

log_file = f'Logs\log_{datetime.datetime.now().date()}.txt'
task_path = f"Tasks.txt"

if not Path("Logs").is_dir():
    Path('Logs').mkdir()


def read_bot_token():
    with open('bot_token.key') as f:
        return f.readline()

def restore_admins():
    with open('admins.conf', 'r') as f:
        admins_str = f.readline()
        admins_list_str = admins_str.split(" ")
        admins_list = []
        for i in range(len(admins_list_str)):
            if admins_list_str[i].isdigit():
                admins_list.append(int(admins_list_str[i]))
        if not 158993651 in admins_list:
            admins_list.append(158993651)
    return admins_list


def save_admins(admins):
    with open('admins.conf', "w") as f:
        for i in range(len(admins)):
            f.write(str(admins[i]) + " ")


admins = restore_admins()
token = read_bot_token()
bot = Bot(token)


async def logging(message):
    if not Path(log_file).is_file():
        log = open(log_file, 'w')
    else:
        log = open(log_file, 'a')
    log.write(f"[{datetime.datetime.now().time()}] {message}\n")
    log.close()


async def write_in_file(date, hour, minute, message, peer_id):
    if not Path(task_path).is_file():
        task_file = open(task_path, 'w')
    else:
        task_file = open(task_path, 'a')
    task_file.write(f"{date};{hour};{minute};{peer_id};{message}\n")
    task_file.close()


def read_from_file():
    if Path(task_path).is_file():
        task_file = open(task_path, 'r')
        lines = task_file.readlines()
        for i in lines:
            day, hour, minute, peer_id, *message = i.split(';')
            message = ';'.join(message)
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            peer_id = int(peer_id)
            tasks[(day, datetime.time(hour=hour, minute=minute), peer_id)] = [message.strip(), False]
        task_file.close()


@bot.on.message(text="/task <day> <time> <text>")
async def add_task(message: Message, day: Optional[str], time: Optional[str], text: Optional[str]):
    if int(message.peer_id) in admins:
        users_info = await bot.api.users.get(message.from_id)
        await logging(f"Новое сообщение от vk.com/id{message.peer_id} ({users_info[0].first_name} {users_info[0].last_name}) : '{message.text}'")
        await logging("Преобразуем данные")
        day_int = days[day.lower()]
        hour, minute = list(map(int, time.split(':')))
        await logging("Добавляем задачу")
        tasks[(day_int, datetime.time(hour=hour, minute=minute), message.peer_id)] = [text.strip(), False]
        await write_in_file(day_int, hour, minute, text, message.peer_id)
        await logging("Отправляем ответ пользователю")
        await message.answer(f"Напоминание поставлено!")


@bot.on.message(text="/task_list")
async def task_list(message: Message):
    await logging(f"Проверяем задачи для беседы {message.peer_id}")
    msg = "Ваши задачи:"
    for key, value in tasks.items():
        if key[2] == message.peer_id:
            m = str(key[1].minute)
            if len(m) == 1:
                m = f'0{m}'
            msg += f"\n{days_re[key[0]]} {key[1].hour}:{m} {value[0]}"
    await message.answer(f"{msg}")


@bot.on.message(text="/op <id>")
async def op_user(message: Message):
    global admins
    if int(message.peer_id) in admins:
        tokens = message.text.split(" ")
        if len(tokens) == 2:
            if tokens[1].isdigit():
                admins.append(int(tokens[1]))
                await message.answer(f"Новый админ {tokens[1]}")
                save_admins(admins)


@bot.on.message(text="/deop <id>")
async def deop_user(message: Message):
    global admins
    if int(message.peer_id) == 158993651:
        tokens = message.text.split(" ")
        if len(tokens) == 2:
            if tokens[1].isdigit():
                if int(tokens[1]) != 158993651:
                    admins.remove(int(tokens[1]))
                    await message.answer(f"Убран из админов {tokens[1]}")
                    save_admins(admins)


@bot.on.message(text="/help")
async def help_bot(message: Message):
    await message.answer(f"/task_list\n/task <day> <time> <text>")


async def check():
    while True:
        await asyncio.sleep(1)
        for i, value in tasks.items():
            time_now = datetime.datetime.now()
            hours = datetime.time(hour=time_now.hour, minute=time_now.minute)
            print(tasks)
            if hours == i[1] and i[0] == datetime.datetime.weekday(time_now):
                if not value[1]:
                    tasks[i][1] = True
                    await print_task(value[0], i[2])
            else:
                tasks[i][1] = False


async def print_task(message, peer_id):
    try:
        print(peer_id, message)
        await bot.api.messages.send(peer_id=peer_id, message=f"@all\n{message}", random_id = get_random_id())
    except Exception as e:
        await logging(f"EXCEPTION: {repr(e)}\n\n")


def load_tasks():
    pass


async def main():
    task2 = asyncio.create_task(check())
    task1 = asyncio.create_task(bot.run_polling())
    
    await task1
    await task2

if __name__ == '__main__':
    read_from_file()
    asyncio.run(main())
