from config import *

from threading import Thread
import schedule, time

import telebot
from telebot import types

import psycopg2

bot = telebot.TeleBot(token)

 
users = {}    # this dictionaries needed for tranision data in "next step handlers"
remindings = {}

#----- Some classes needed for bot functioning
class User:
    def __init__(self,chat_id):
        self.chat_id = chat_id

class Reminding:
    def __init__(self,day,time_,chat_id):
        self.day = day
        self.time_ = time_
        self.chat_id = chat_id
    
    def call(self):
        bot.send_message(self.chat_id,'It`s time to train!')
        
def create_reminding(day,time_,chat_id):
    call = Reminding(day,time_,chat_id).call
    if day == 'monday':
        schedule.every().monday.at(time_).do(call)
    elif day == 'tuesday':
        schedule.every().tuesday.at(time_).do(call)
    elif day == 'wednesday':
        schedule.every().wednesday.at(time_).do(call)
    elif day == 'thursday':
        schedule.every().thursday.at(time_).do(call)
    elif day == 'friday':
        schedule.every().friday.at(time_).do(call)
    elif day == 'saturday':
        schedule.every().saturday.at(time_).do(call)
    elif day == 'sunday':
        schedule.every().sunday.at(time_).do(call)

with psycopg2.connect("dbname='workoutbot' user='workoutbot' password='snoopdogg12' host='localhost'") as conn:
        with conn.cursor() as curs:
            curs.execute('SELECT * FROM reminders;')
            for row in curs.fetchall():
                data = (row[1],row[2],row[0])
                create_reminding(*data)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Howdy, I am a bot, and I will be your personal training assistan")
    users[chat_id] = User(chat_id)

# ***  BOT reminder creatin process
@bot.message_handler(commands=['reminder'])
def set_reminder(message):
    "Firs step of reminder creation"
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=3)
    monday = types.KeyboardButton('monday')
    tuesday = types.KeyboardButton('tuesday')
    wednesday = types.KeyboardButton('wednesday')
    thursday = types.KeyboardButton('thursday')
    friday = types.KeyboardButton('friday')
    saturday = types.KeyboardButton('saturday')
    sunday = types.KeyboardButton('sunday')
    markup.add(monday,tuesday,wednesday,thursday,friday,saturday,sunday)
    msg = bot.send_message(chat_id, "Which day you want to go:", reply_markup=markup)
    bot.register_next_step_handler(msg,set_date)
    remindings[chat_id] = Reminding('','',chat_id)

def set_date(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=3)
    morning = types.KeyboardButton('morning (9:00)')
    noon = types.KeyboardButton('at noon')
    afternoon = types.KeyboardButton('afternoon (15:00)')
    five = types.KeyboardButton("five o'clock")
    evening = types.KeyboardButton('evening (19:00)')
    late = types.KeyboardButton('late (22:00)')
    markup.add(morning,noon,afternoon,five,evening,late)

    reminder = remindings[chat_id]
    reminder.day = message.text
    
    msg = bot.send_message(chat_id,'What hour you want to go?',reply_markup = markup)
    bot.register_next_step_handler(msg,set_time)

def set_time(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardRemove(selective=False)
    reminder = remindings[chat_id]
    reminder.time_ = message.text.split(' ')[0]
    bot.send_message(
        chat_id,
        f'ok, i will remind you on {reminder.day} at {reminder.time_} ',
        reply_markup=markup)
    create_reminding(reminder.day,reminder.time_,chat_id)
    with psycopg2.connect("dbname='workoutbot' user='workoutbot' password='snoopdogg12' host='localhost'") as conn:
        with conn.cursor() as curs:
            curs.execute(f"INSERT INTO reminders VALUES({int(chat_id)}, '{reminder.day}', '{reminder.time_}');")   


@bot.message_handler(commands=['data'])
def send_data(message):
    "send user his data"
    chat_id =message.chat.id
    bot.send_message( chat_id,chat_id)



def bot_main():
    bot.polling()

def schedule_main():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__=='__main__':        
    Thread(target = schedule_main).start() 
    Thread(target = bot_main).start()

