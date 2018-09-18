import telepot
import time
import os.path
import sys
import apiai
import json
import requests
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import pymysql
from user import register_user

BOT_TOKEN  =  '673895642: AAGvtuwlxnUNuysUu7mPifNLAHIWJ0L0uvk'
APIAI_ACCESS_TOKEN = '0193f2bda4ff4c9f9831ff89ba4b79c2'

bot = telepot.Bot(BOT_TOKEN)
ai = apiai.ApiAI(APIAI_ACCESS_TOKEN)

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Just Coding', callback_data=1),
    InlineKeyboardButton(text='Code Buddy', callback_data=2)],
    [InlineKeyboardButton(text='PASC Hackathon', callback_data=3),
    InlineKeyboardButton(text='Dexterous', callback_data=4)],
    [InlineKeyboardButton(text='AI Workshop', callback_data=5)]
])

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type == "photo":
        photoData = msg["photo"][0],
        if 'caption' not in msg:
            caption = None
        else:
            caption = msg["caption"]

        handle_photo(chat_id, photoData, caption)
    else:
        msgText = msg["text"]
        first_name = msg["from"]["first_name"]
        handle_text(chat_id, msgText, first_name)
    

def handle_text(chat_id, msgText, first_name):
    if msgText == '/start':
        register_user(first_name, chat_id)

        greeting = "Hi %s!, \nThank you for connecting. I can help you with information with events at PICT. Please select your interests." % (first_name)
        bot.sendMessage(chat_id, greeting, reply_markup=keyboard)

    elif msgText.startswith("#"):
        get_sender = """SELECT DISTINCT FirstName, isAdmin FROM Users WHERE clientId=%d;""" % (chat_id)
        sender_info = fetch_from_db(get_sender)
        print (sender_info)
        isAdmin = sender_info[0][1]
        if isAdmin == False:
            bot.sendMessage(chat_id, "Only orgainsers can send notifications. Please contact the admins to get organiser rights to send notifications.")
        else:       
            info = msgText.split(':')
            tag = info[0]
            tag = tag.replace(" ", "")
            notification_data = info[1]
            notification_info = "Notification from " + sender_info[0][0] + ": \n" + notification_data

            get_event_id = """SELECT id FROM Events WHERE JSON_CONTAINS(tags, '["%s"]');""" % (tag)
            event = fetch_from_db(get_event_id)
            event_id = event[0]
            get_users_list = """SELECT DISTINCT clientId FROM EventUsers WHERE eventId=%d;""" % (event_id)
            users = fetch_from_db(get_users_list)
            # users = ((525347032,), (504100873,), (551623773,))

            for user in users:
                user_id = user[0]
                print(user_id)
                print(notification_info)
                bot.sendMessage(user_id, notification_info)
                
    else:
        request = ai.text_request()
        request.session_id = "758833"
        request.query = msgText
        response = request.getresponse()
        #print(type (response))
        #print(response.read())
        responseInStr = response.read().decode('utf-8')
        responseInJson = json.loads(responseInStr)
        metadata = responseInJson["result"]["metadata"]
        intentName = metadata["intentName"]

        if intentName == "ListOfEvents":
            bot.sendMessage(chat_id, "List of all upcoming events:", reply_markup=keyboard)

        elif intentName == "Pulzion-poster":
            bot.sendMessage(chat_id, "Okay, here you go.")
            bot.sendPhoto(chat_id, "https://i.imgur.com/WXoPKhJ.jpg")

        elif intentName == "Pasc-hackathon-poster":
            bot.sendMessage(chat_id, "Okay, here you go.")
            bot.sendPhoto(chat_id, "https://i.imgur.com/w1Vv627.jpg")

        elif intentName == "Ai-workshop-poster":
            bot.sendMessage(chat_id, "Okay, here you go.")
            bot.sendPhoto(chat_id, "https://i.imgur.com/4xjbzqb.jpg")  
        elif intentName == "Pasc-hackathon-domains":
            bot.sendMessage(chat_id, "Below is the poster containing relevant domains on which you may work on: ")
            bot.sendPhoto(chat_id,"https://i.imgur.com/w1Vv627.jpg") 

        else:
            fulfillment = responseInJson["result"]["fulfillment"]
            defaultResponse = fulfillment["speech"]
            bot.sendMessage(chat_id, str(defaultResponse))


def handle_photo(chat_id, photoData, caption):
    print(photoData)
    print(caption)
    if caption != None and caption.startswith("#"):
        get_sender = """SELECT DISTINCT FirstName, isAdmin FROM Users WHERE clientId=%d;""" % (chat_id)
        sender_info = fetch_from_db(get_sender)
        isAdmin = sender_info[0][1]
        if isAdmin == False:
            bot.sendMessage(chat_id, "Only orgainsers can send notifications. Please contact the admins to get organiser rights to send notifications.")
        else:
            tag = caption
            file_id = photoData[0]["file_id"]
            get_event_id = """SELECT id FROM Events WHERE JSON_CONTAINS(tags, '["%s"]');""" % (tag)
            event = fetch_from_db(get_event_id)
            event_id = event[0]
            get_users_list = """SELECT clientId FROM EventUsers WHERE eventId=%d;""" % (event_id)
            users = fetch_from_db(get_users_list)
            # users = ((525347032,), (504100873,), (551623773,))

            for user in users:
                user_id = user[0]
                print("sending")
                bot.sendPhoto(user_id, file_id)
    
    else:
        bot.sendMessage(chat_id, "Sorry, I don't know what to do with this ?!")
    
def on_callback_query(data):
    query_id, from_id, query_data = telepot.glance(data, flavor='callback_query')

    event_user = """INSERT INTO EventUsers(eventId, clientId) values (%d, %d);""" % (int(query_data), int(from_id))
    event_name = """SELECT name FROM Events WHERE id= %d;""" % (int(query_data))

    write_to_db(event_user)
    result_from_query = fetch_from_db(event_name)
    eventName = result_from_query[0]

    msg_idf = telepot.message_identifier(data['message'])
    responseMessage = """Thank you for subscribing to %s.""" % (eventName)
    bot.editMessageText(msg_idf, responseMessage )

def write_to_db(insert_query):
    db = pymysql.connect("localhost", "root", "root", "testDB")
    cursor = db.cursor()
    try:
        cursor.execute(insert_query)
        db.commit()    
    except:
        db.rollback()

    cursor.close()
    db.close()

def fetch_from_db(query):
    print(query)
    db = pymysql.connect("localhost", "root", "root", "testDB")
    cursor = db.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall() 
    except:
        print('Invalid search query')

    cursor.close()
    db.close()
    
    return result


#bot.message_loop(on_chat_message)
MessageLoop(bot, {'chat': on_chat_message,
                  'callback_query': on_callback_query}).run_as_thread()

print ('Listening ...')

while 1:
    time.sleep(5)
