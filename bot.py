from config import *

from threading import Thread
import random
import schedule, time

import telebot
from telebot import types

import psycopg2

bot = telebot.TeleBot(token)
 
users = {}    # this dictionaries needed for tranision data in "next step handlers"
remindings = {}

##### Some classes needed for bot functioning
class User:
    def __init__(self,chat_id,goal='no goal'):
        self.chat_id = chat_id
        self.goal = goal

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


def get_data_from_db():
    with psycopg2.connect(f"dbname={db_name} user={db_user} password={db_password} host='localhost'") as conn:
            with conn.cursor() as curs:
                curs.execute('SELECT * FROM reminders;')
                for row in curs.fetchall():
                    data = (row[1],row[2],row[0])
                    create_reminding(*data)

    with psycopg2.connect(f"dbname={db_name} user={db_user} password={db_password} host='localhost'") as conn:
            with conn.cursor() as curs:
                curs.execute('SELECT * FROM users;')
                for row in curs.fetchall():
                    chat_id = row[0]
                    goal = row[1]
                    users[chat_id] = User(chat_id,goal)
def commit_user(user):
    with psycopg2.connect("dbname='workoutbot' user='workoutbot' password='snoopdogg12' host='localhost'") as conn:
        with conn.cursor() as curs:
            curs.execute(f"INSERT INTO users VALUES({user.chat_id}, '{user.goal}');")
def update_user(user):
    with psycopg2.connect("dbname='workoutbot' user='workoutbot' password='snoopdogg12' host='localhost'") as conn:
        with conn.cursor() as curs:
            curs.execute(f"UPDATE users SET goal='{user.goal}' WHERE chat_id={user.chat_id};")


#### User creation process
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Howdy, I am a bot, and I will be your personal training assistan")
    users[chat_id] = User(chat_id)
    ask_type_of_training(message)
#@bot.message_handler(commands=['Goal'])
def ask_type_of_training(messsage):
    chat_id = messsage.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1)
    g1 = types.KeyboardButton('Muscle gain / Heavy weights')
    g2 = types.KeyboardButton('Fat loss / HiT + Weights')
    g3 = types.KeyboardButton('Aesthetics fullbody/ Calisthenics')
    markup.add(g1, g2, g3)
    msg = bot.send_message(
        chat_id,
         "*What is your goal?*",
        reply_markup=markup, 
        parse_mode='Markdown')
    bot.register_next_step_handler(msg, set_goal)

def set_goal(message):
    chat_id = message.chat.id
    user = users[chat_id]
    prev_goal = user.goal
    user.goal = message.text.split()[1]
    if prev_goal == 'no goal':
        commit_user(user)
    else:
        update_user(user)
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(
        chat_id,
        f'Ok, you have set your goal as *{user.goal}*, for getting your program just type /program',
        reply_markup=markup,
        parse_mode='Markdown')

@bot.message_handler(commands=['goal'])
def change_goal(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1)
    g1 = types.KeyboardButton('Muscle gain / Heavy weights')
    g2 = types.KeyboardButton('Fat loss / HiT + Weights')
    g3 = types.KeyboardButton('Aesthetics fullbody/ Calisthenics')
    markup.add(g1, g2, g3)
    msg = bot.send_message(
        chat_id,
         "*What is your new goal?*",
        reply_markup=markup, 
        parse_mode='Markdown')
    bot.register_next_step_handler(msg, set_goal)


####   Reminding creation process
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
            curs.execute(f"INSERT INTO reminders VALUES({chat_id}, '{reminder.day}', '{reminder.time_}');")   


#### Get training program
@bot.message_handler(commands=['program'])
def which_day(message): 
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1)
    day1 = types.KeyboardButton('Day 1')
    day2 = types.KeyboardButton('Day 2')
    day3 = types.KeyboardButton('Day 3')
    markup.add(day1, day2, day3)
    msg = bot.send_message(
            chat_id,
            '*What day is it* ?',
            reply_markup=markup,
            parse_mode = 'Markdown'
            )
    bot.register_next_step_handler(msg,send_program)
    
def send_program(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardRemove(selective=False)
    user = users[chat_id]
    day = message.text.split()[1]
    with open(f'train_programs/{user.goal}/{day}.md', 'r') as content_file:
        content = content_file.read()
    bot.send_message(
        chat_id,
        content,
        parse_mode='Markdown',
        reply_markup=markup
    )



#### get tips
def send_tip(user):
    rand_int = random.randint(1,10) 
    with open(f'tips/{rand_int}.md', 'r') as content_file:
        content = content_file.read()
    bot.send_message(user.chat_id, content,parse_mode="Markdown")

def spam_tips():
    for user in users:
        send = random.choice((True, False))
        if send:
            send_tip(users[user])



#### Send user data
@bot.message_handler(commands=['data'])
def send_data(message):
    "send user his data"
    chat_id =message.chat.id
    bot.send_message( chat_id,chat_id )


#### running procesess
def schedule_main():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__=='__main__':
    schedule.every().day.at('14:11').do(spam_tips)
    get_data_from_db()        
    Thread(target = schedule_main).start() 
    Thread(target = bot.polling).start()

