import telebot as tb
import datetime as dt
import json
import csv
import re
import time
import pandas as pd
from telebot.types import Update

tb.apihelper.Timeout = 24 * 60 * 60

config = json.load(open('config.json'))
bot = tb.TeleBot(config.get('bot'))
chanel_id = config.get('chanel_id')
feedback_path = config.get('feedback_path')
feedback_chanel = config.get('feedback_chanel')
admin_id = config.get('admin_id')
user_status = {}
last_message_time = {}

def censore(text: str) -> bool:
    with open("bad_words.txt", 'r', encoding='ISO-8859-1') as bad_file:
        bad_words = {word.strip().lower() for word in bad_file}
    text = re.sub(r'[^\w\s]', '', text)
    words = text.lower().split()

    for word in words:
        if word in bad_words:
            return False
    return True

def read_ban_list():
    try:
        with open("ban_users.txt", "r") as ban_user_file:
            return [line.strip() for line in ban_user_file.readlines()]
    except FileNotFoundError:
        return []  # Return an empty list if the file doesn't exist

def update_ban_list(ban_user_list):
    with open("ban_users.txt", "w") as ban_user_file:
        for user in ban_user_list:
            ban_user_file.write(f"{user}\n")


def check_user_ban(user_id) -> None:
    ban_user_list = read_ban_list()
    if user_id in ban_user_list:
        return False
    else:
        return True

def show_menu(chat_id: int) -> None:
    menu_text = ("Основний канал: @KSEgossip \n"
                 "Виберіть опцію:\n"
                 "/menu - повернення до головного меню\n"
                 "/message - Відправити повідомлення\n"
                 "/anonymous_message - Відправити анонімне повідомлення\n"
                 "/feedback - зворотній зв'язок для команди\n"
                 )
    bot.send_message(chat_id, menu_text)

@bot.message_handler(commands=["menu"])
def menu(message) -> None:
    user_status[message.from_user.id] = 'menu'
    show_menu(message.chat.id)

@bot.message_handler(commands=["feedback"])
def feedback(message) -> None:
    user_status[message.from_user.id] = "feedback"
    bot.send_message(message.chat.id, "Готові вислуховувати тебе")

@bot.message_handler(commands=["anonymous_message"])
def anonymous_message(message) -> None:
    user_status[message.from_user.id] = "anonymous_message"
    bot.send_message(message.chat.id, "Анонімне повідомлення:")

@bot.message_handler(commands=['start'])
def main(message) -> None:
    user_status[message.from_user.id] = "menu"
    bot.reply_to(message, text=f"Привіт {message.from_user.username}")
    bot.send_message(message.chat.id, text="Цей бот створений для поширення думок без засудження\n")
    show_menu(message.chat.id)

@bot.message_handler(commands=["reboot"])
def echo(message) -> None:
    if message.from_user.id == int(admin_id):
        bot.send_message(chanel_id, "Teхнічні роботи")
        bot.reply_to(message, "Reboot, Success")
        exit()
    else:
        bot.reply_to(message, text="Не достатньо прав")

@bot.message_handler(commands=["banhammer"])
def ban_user(message) -> None:
    if message.from_user.id == int(admin_id):
        bot.reply_to(message, "Кому банхаммер?")

        ban_user_list = read_ban_list()

        if message.text in ban_user_list:
            bot.reply_to(message, f"{message.text} already banned")
        else:
            ban_user_list.append(message.text)
            update_ban_list(ban_user_list)
            bot.reply_to(message, f"{message.text} is banned")

@bot.message_handler()
def echo(message) -> None:
    current_time = dt.datetime.now()
    last_time = last_message_time.get(message.from_user.id)

    if last_time and (current_time - last_time).total_seconds() < 15:
        remaining_time = 15 - (current_time - last_time).total_seconds()
        bot.reply_to(message, text=f"Please wait {int(remaining_time)} seconds before sending another message.")
        return

    last_message_time[message.from_user.id] = current_time
    if check_user_ban(int(message.from_user.id)):
        if message.from_user.id not in user_status.keys():
            show_menu(message.chat.id)
        elif user_status.get(message.from_user.id) == "anonymous_message":
            user_status.pop(message.from_user.id, None)
            if censore(message.text):
                bot.send_message(feedback_chanel, f"{message.text}\n {message.from_user.id},\n #message")
                bot.send_message(chanel_id, f"{message.text}\nвід анонімного користувача")
            else:
                bot.reply_to(message, f"підбирай слова")
            show_menu(message.chat.id)
        elif user_status.get(message.from_user.id) == "feedback":
            feedback = {
                "message": message.text,
                "user_id": message.from_user.id,
                "user_name": message.from_user.username,
                "user_full_name": message.from_user.first_name + " " + (message.from_user.last_name or "")
            }
            bot.send_message(feedback_chanel, text=f"{feedback['user_id']}\n"
                                                   f"{feedback['user_name']}\n"
                                                   f"{feedback['user_full_name']}, "
                                                   f"{feedback['message']},"
                                                   f"#feedback")
            bot.reply_to(message, "Дякуємо за ваш відгук!")
            user_status[message.from_user.id] = "menu"
            show_menu(message.chat.id)
    else:
        bot.reply_to(message, "На жаль вам не доступна можливість надсилати повідомлення")
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(15)

if __name__ == "__main__":
    run_bot()
