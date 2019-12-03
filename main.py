import os
import pymongo
import logging
import datetime
import requests
import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram

if os.getenv('ENV') != 'production':
  import config
from helpers import *

now = datetime.datetime.now()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Get environment variables
USER = os.getenv('DB_USER')
PASSWORD = os.environ.get('DB_PASSWORD')

bot = telegram.Bot(os.environ.get('BOT_KEY'))

chat_id = 0

client = pymongo.MongoClient(f"mongodb+srv://{USER}:{PASSWORD}@cluster0-dioya.mongodb.net/test?retryWrites=true&w=majority")
db = client.sidapp
users = db.users


def get_usage_message():
  return '''
  Available commands:
  /help - print this message
  *<person_name>* to view a person's profile
  Example: David Miller
  */people displays your list of people*
  Example: /people
  */add a person*
  Example: /add
  '''

def get_signup_message():
  return '''
  *New User*
  First Name: (Joe)
  Last Name: (Smith)
  Email: (joe@example.com)
  Phone: (9998887777)
  Gender: (M)
  Birth Year: (1900)
  City: (Cityville)
  State: (NY)
  Zip: (07000)
  Country: (USA)
  '''

def get_newperson_message():
  return '''
  *New Person*
  First Name: (Joe)
  Last Name: (Smith)
  Email: (joe@example.com)
  Phone: (9998887777)
  Gender: (M)
  Birth Year: (1900)
  City: (Cityville)
  State: (NY)
  Zip: (07000)
  Country: (USA)
  High School: (Kushner)
  Gap Year: (HaKotel)
  College: (YU)
  Graduate School: (NYU)
  Graduate Degree: (MBA)
  Shul: (AABJD)
  Personality Traits Checklist: (quiet, athletic)
  Personality Traits Desired: (funny, outgoing)
  Location Radius: (tri-state area)
  Names to Avoid: (Ali Stein, Jen Goldberg)
  Notes: (any other info here)
  '''

def getProfile(id):
  user = users.find_one({ '_id' : id })
  return f'''
  *{user['name']['first']} {user['name']['last']}*\n
  *Email:* {user['email']}
  *Phone:* {user['phone']}
  *Gender:* {user['gender']}
  *Age Range:* {now.year - int(user['dob']) - 1} - {now.year - int(user['dob']) + 1}
  *Location:* {user['location']['city']}, {user['location']['state']}, {user['location']['country']}
  *High School:* {user['education']['high_school']}
  *Gap Year:* {user['education']['gap_year']}
  *College:* {user['education']['college']}
  *Graduate School:* {user['education']['grad_school']}
  *Graduate Degree:* {user['education']['grad_degree']}
  *Shul:* {user['shul']}
  *Personality Traits Checklist:* {user['traits_checklist']}
  *Personality Traits Desired:* {user['traits_desired']}
  *Location Radius:* {user['location_radius']}
  *Names to Avoid:* {user['names_to_avoid']}
  *Notes:* {user['notes']}
  '''

def isLoggedIn(update):
  if users.find_one({ 'chat_id' : update.message.chat.id }) == None:
    return False
  else:
    return True

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
  if users.find_one({ 'type' : 1, 'chat_id' : update.message.chat.id }) == None:
    send_signup(update)
  else:
    update.message.reply_markdown('You are already signed up!')
    send_usage(update)


def help(update, context):
  send_usage(update)


def send_usage(update):
  logger.info(f'[bot] received usage request for chat id {update.message.chat.id}')
  update.message.reply_markdown(get_usage_message())

def send_signup(update):
  update.message.reply_markdown('Welcome to the Shidduch App! Well, not an app *yet*. ' +
    'This bot allows you to use *commands* to complete similar tasks to what you might complete in an app. ' +
    'Please sign up using the following format. ' +
    'All you need to do is copy/paste the following message, edit, and send it back! *Please keep all parenthases.*')
  update.message.reply_markdown(get_signup_message())


def error(update, context):
  """Log Errors caused by Updates."""
  logger.warning('Update caused error "%s"', context.error)


def test(update, context):
  update.message.reply_markdown('chatID: ' + str(update.message.chat.id))
  update.message.reply_markdown('message: ' + str(update.message.text))
  # for doc in users.find():
  #   if doc['type'] == 2:
  #     print(update.message.reply_markdown(
  #       'Name: ' + doc['name']['first'] + ' ' + doc['name']['last']
  #   ))

def response_handler(update, context):
  m = update.message.text.strip()

  #handle new account
  if m[0:8] == 'New User':
    f = getFieldValues(m)
    user = {
      'name' : {
        'first' : f[0],
        'last' : f[1]
      },
      'email' : f[2],
      'phone' : f[3],
      'gender' : f[4],
      'dob' : f[5],
      'location' : {
        'city' : f[6],
        'state' : f[7],
        'zip' : f[8],
        'country' : f[9]
      },
      'type' : 1,
      'registered' : now,
      'chat_id' : update.message.chat.id
    }

    if users.find_one({ 'type' : 1, 'email' : f[3] }) == None:
      users.insert_one(user)
      update.message.reply_markdown(f'Welcome {f[1]}, you are now a matchmaker!')
      send_usage(update)
    else:
      update.message.reply_markdown(f'An account with email {f[3]} already exists.')

    #send Perry an update
    send_telegram(m, '269928547')

  #handle new person
  elif m[0:10] == 'New Person':
    #check if logged in
    if isLoggedIn(update) == False:
      update.message.reply_markdown('You must create an account! Please /start')
      return 0

    f = getFieldValues(m)
    user = {
      'name' : {
        'first' : f[0].strip().capitalize(),
        'last' : f[1].strip().capitalize()
      },
      'email' : f[2].strip(),
      'phone' : f[3].strip(),
      'gender' : f[4].strip(),
      'dob' : f[5].strip(),
      'location' : {
        'city' : f[6].strip().capitalize(),
        'state' : f[7].strip().upper(),
        'zip' : f[8].strip(),
        'country' : f[9].strip()
      },
      'education' : {
        'high_school' : f[10].strip(),
        'gap_year' : f[11].strip(),
        'college' : f[12].strip(),
        'grad_school' : f[13].strip(),
        'grad_degree' : f[14].strip()
      },
      'shul' : f[15].strip(),
      'traits_checklist' : f[16].replace(", ", ",").split(','),
      'traits_desired' : f[17].replace(", ", ",").split(','),
      'location_radius' : f[18].strip(),
      'names_to_avoid' : f[19].replace(", ", ",").split(','),
      'notes' : f[20],
      'type' : 2,
      'date_added' : now,
      'chat_id' : update.message.chat.id,
      'owner' : users.find_one({ 'chat_id' : update.message.chat.id })['email']
    }

    if users.find_one({ 'type' : 2, 'chat_id' : update.message.chat.id, 'email' : f[3] }) == None:
      users.insert_one(user)
      update.message.reply_markdown(f'Successfully added {f[1]} {f[2]}!')
      people_handler(update, context)
    else:
      update.message.reply_markdown(f'You have already added person with email {f[3]}.')

  #handle person info
  elif len(m.split(' ')) == 2 and users.find_one({ 'name' : { 'first' : m.split(' ')[0].capitalize(), 'last' : m.split(' ')[1].capitalize() }, 'type' : 2, 'chat_id' : update.message.chat.id }) != None:
    user = users.find_one({ 'name' : { 'first' : m.split(' ')[0].capitalize(), 'last' : m.split(' ')[1].capitalize() }, 'type' : 2, 'chat_id' : update.message.chat.id })
    update.message.reply_markdown(getProfile(user['_id']))


  else:
    help(update, context)

def profile_handler(update, context):
  print('test')

def people_handler(update, context):
  people = users.find({ 'type' : 2, 'chat_id' : update.message.chat.id })
  logger.info(f'[bot] received people request for chat id {update.message.chat.id}')
  ppl_list = '*People List:* \n\n'
  for i, p in enumerate(people):
    if p.get('name') is None:
      logger.error('[bot] people_handler: missing name')
      return update.message.reply_markdown("server error")

    name = p['name']
    if name.get('first') is None or name.get('last') is None:
      logger.error('[bot] people_handler: missing first or last name')
      return update.message.reply_markdown("server error")

    first = name['first']
    last = name['last']
    ppl_list = ppl_list + '*' + str(i) + '.* ' + p['name']['first'] + ' ' + p['name']['last'] + '\n'

  logger.info(f'[bot] replying to people request for chat id {update.message.chat.id}')
  update.message.reply_markdown(ppl_list)
  # bot.send_message(chat_id=update.message.chat.id,
  #                text=ppl_list,
  #                parse_mode=telegram.ParseMode.MARKDOWN)

def add_handler(update, context):
  update.message.reply_markdown('Copy/paste the following message, edit to your needs, and send it back. *Please keep all parenthases.*')
  update.message.reply_markdown(get_newperson_message())

def main():
  """Load environment variables"""
  TOKEN = os.getenv("BOT_KEY")

  """Start the bot."""
  # Create the Updater and pass it your bot's token.
  # Make sure to set use_context=True to use the new context based callbacks
  # Post version 12 this will no longer be necessary
  updater = Updater(TOKEN, use_context=True)

  # Get the dispatcher to register handlers
  dp = updater.dispatcher

  # on different commands - answer in Telegram
  dp.add_handler(CommandHandler("start", start))
  dp.add_handler(CommandHandler("help", help))
  dp.add_handler(CommandHandler("test", test))
  dp.add_handler(CommandHandler("profile", profile_handler))
  dp.add_handler(CommandHandler("people", people_handler))
  dp.add_handler(CommandHandler("add", add_handler))

  # on noncommand i.e message - echo the message on Telegram
  dp.add_handler(MessageHandler(Filters.text, response_handler))

  # log all errors
  dp.add_error_handler(error)

  print("[bot] starting to poll for messages...")
  # Start the Bot
  updater.start_polling()
  print("[bot] successfully polling")

  # Run the bot until you press Ctrl-C or the process receives SIGINT,
  # SIGTERM or SIGABRT. This should be used most of the time, since
  # start_polling() is non-blocking and will stop the bot gracefully.
  print("[bot] starting to idle indefinitely")
  updater.idle()


if __name__ == '__main__':
  main()
