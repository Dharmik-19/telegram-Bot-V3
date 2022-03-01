from keep_alive import keep_alive
import os 
import telebot 
import yfinance as yf
import random
import re
import pandas as pd
from PIL import Image
import io
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from functools import wraps
import pymongo
from datetime import datetime, timedelta
import time
import pytz
import urllib
from dotenv import load_dotenv
from backbone import predict
import seaborn as sns
import matplotlib.pyplot as plt

#db.keys is a set object 

#For yahoofinancials 
#from yahoofinancials import YahooFinancials



#Imports for dash to show the plotly graphs using local html server -> Didn't work though
#*
# import dash
# import dash_core_components as dcc
# import dash_html_components as html

#Authenticated users
#db.keys() has a set of known usernames 

#Restricting Access

load_dotenv()


mongo = os.getenv('mongo')  


myclient = pymongo.MongoClient(mongo)
mydb = myclient['RickyRetardo']
mycol = mydb['users']
#mycol.delete_one({'id': 'dharmikshah58'})

def is_known_username(id):
    '''
    Returns a boolean if the id is known in the user-list.
    '''
    
    users = mycol.find({}, {'id':1, '_id':0})
    check = id in [x['id'] for x in users]
    return check


def private_access():
    """
    Restrict access to the command to users allowed by the is_known_username function.
    """
    def deco_restrict(f):

        @wraps(f)
        def f_restrict(message, *args, **kwargs):
            id = message.from_user.id

            if is_known_username(id):
              isBlocked = mycol.find({'id': id}, {'info.isBlocked':1, '_id':0})
              isBlocked = isBlocked[0]['info']['isBlocked']

              if(isBlocked):
                bot.reply_to(message, text='You have been blocked\nIf you think there is some problem, drop a message <u><a href="https://tally.so/r/mBgk43">here</a></u>', parse_mode='html')
              else:
                return f(message, *args, **kwargs)
            else:
                bot.reply_to(message, text='You are not authorised to use this bot!\nTo get authorized use <b>/key {accessToken}</b> (without braces). \nYou may request the accessToken <u><a href="https://tally.so/r/mBgk43">here</a></u>', parse_mode='html')

        return f_restrict  # true decorator

    return deco_restrict




#PROVIDES ADMIN LEVEL ACCESS
def is_admin(id):   
  isAdmin = mycol.find({'id': id}, {'info.isAdmin':1, '_id':0})
  isAdmin = isAdmin[0]['info']['isAdmin']

  return isAdmin


def admin_access():

  def deco_restrict(f):

    @wraps(f)
    def f_restrict(message, *args, **kwargs):
      id = message.from_user.id

      if is_admin(id):
        return f(message, *args, **kwargs)
      else:
        bot.reply_to(message, text='You are not privileged to run this command!\nTo get admin access, use <b>/privesc {accessToken}</b> (without braces).', parse_mode='html')

    return f_restrict  # true decorator

  return deco_restrict



#PROVIDES SUPERUSER ACCESS  
def is_super(id):   
  isSuper = mycol.find({'id': id}, {'info.isSuper':1, '_id':0})
  isSuper = isSuper[0]['info']['isSuper']

  return isSuper


def super_access():

  def deco_restrict(f):

    @wraps(f)
    def f_restrict(message, *args, **kwargs):
      id = message.from_user.id

      if is_super(id):
        return f(message, *args, **kwargs)
      else:
        bot.reply_to(message, text='You are not privileged to run this command!\nTo get superuser access, use <b>/becomesuper {accessToken}</b> (without braces).', parse_mode='html')

    return f_restrict  # true decorator

  return deco_restrict




#Runs the server and provides seemless access to the bot
keep_alive()


#Connecting to the MongoDB server  




#Initialising the bot parameters
my_secret = os.getenv('API_KEY_Telegram')
#my_secret = os.environ['API_KEY_Telegram']
bot = telebot.TeleBot(my_secret)

#Changing the time zone to India
IST = pytz.timezone('Asia/Kolkata')
utc = pytz.utc

def calls_total(message):

  id = message.from_user.id
  now = datetime.now(IST).strftime('%d/%m/%Y|%I:%M:%S %p')

  
  #updating commands list, last_used and calls_total
  #r = mycol.find_one({'id': id})

  mycol.update_many({'id': id}, {'$push': {'commands': {now: message.text}},
                                            '$set':  {'info.last_used': now},
                                            '$inc':  {'info.count.calls_total': 1}
                                            }
                  )
  

#updating the calls for financials number
def calls_financials(message):
  id = message.from_user.id
  mycol.update_one({'id': id}, {'$inc':  {'info.count.calls_financials': 1}})


def calls_price(message):
  id = message.from_user.id
  mycol.update_one({'id': id}, {'$inc':  {'info.count.calls_price': 1}})

def calls_wl(message):
  id = message.from_user.id
  mycol.update_one({'id': id}, {'$inc':  {'info.count.calls_wl': 1}})

def calls_memes(message):
  id = message.from_user.id
  mycol.update_one({'id': id}, {'$inc':  {'info.count.calls_memes': 1}})

def calls_admin(message):
  id = message.from_user.id
  mycol.update_one({'id': id}, {'$inc':  {'info.count.calls_admin': 1}})




def line(data, tick, first, last, message):
  fig = px.line(data, x=data.columns[0], y='Close', title="Line chart for ${} from {} to {}".format(tick.upper(), first, last), width=1300, height=650)
  img_bug = io.BytesIO()
  fig.write_image(img_bug, format='png')
  bot.send_photo(message.chat.id, Image.open(img_bug), "Line chart for <b>${}</b> from <i>{}</i> to <i>{}</i>".format(tick.upper(), first, last), 'html')
  img_bug.close()


def candlestick(data, tick, first, last, message):
  fig = go.Figure(data=[go.Candlestick(x=data[data.columns[0]], open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
        
  fig.update_layout(
      xaxis_rangeslider_visible=False,
      title="Candlestick chart for ${} from {} to {}".format(tick.upper(), first, last),
      yaxis_title="Price",
      xaxis_title="Timeframe",
      width=1300, 
      height=650,
      font=dict(
          family="Courier New, monospace",
          size=18,
          color="RebeccaPurple"
      )
  )      

  img_bug = io.BytesIO()
  fig.write_image(img_bug, format='png')
  bot.send_photo(message.chat.id, Image.open(img_bug), "Candlestick chart for $<b>{}</b> from <i>{}</i> to <i>{}</i>".format(tick.upper(), first, last), 'html')
  img_bug.close()


def checkyChecker(ticks):
  periods = ['1d','5d', '14wk', '1mo','3mo','6mo','1y','2y','5y','10y','ytd','max']
  #infact wk also works in periods
  intervals = ['1m','2m','5m','15m','30m','60m','90m','1h','1d','5d','1wk','1mo','3mo']

  interval = ''
  period = ''


  check1 = False
  check2 = False

  #Check for the interval and period in the code 

  #print((ticks[-2][-3].isnumeric()))

  try:
    if((ticks[-1].lower() in intervals) and ((ticks[-2].lower() in periods) or 
                                             ((ticks[-2][-1].lower() in ['d', 'w', 'o', 'y', 'm', 'h']) and ticks[-2][0].isnumeric() and ticks[-2][-2].isnumeric()) or 
                                             ((ticks[-2][-2:].lower()=='mo' or ticks[-2][-2:].lower()=='wk') and ticks[-2][-3].isnumeric())
                                            )
    ):
      interval = ticks[-1].lower()
      period = ticks[-2].lower()
      check1 = True
  except:
    pass

  #check for the date in the code -> Will be used in retriving data 
  check = '^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
  date1 = ticks[-2]
  date2 = ticks[-1]
  if re.search(check, date1):
    if re.search(check, date2):
      check2 = True
  
  if(not(check1) and not(check2)):
    interval = '1m'
    period = '5m'

  return [check1, check2, interval, period, date1, date2]
 


def sendResponse(message, response):
  if(len(response)==0): return
  
  while(len(response)>4095):
    words = response[:4095].split('\n')
    text = '\n'.join(words[:-1])
    remaining_text = words[-1]
    response = remaining_text+response[4095:]
    bot.send_message(message.chat.id, text, parse_mode='html')

  bot.send_message(message.chat.id, response, parse_mode='html')
  time.sleep(1)


def invalidUseOfCommand(message, command):
  bot.send_message(message.chat.id, 'Invalid use of /{} command. No ticker found!\nPlease refer to /help for walkthough on this command.'.format(command))
  time.sleep(0.5)
 
def invalidUseOfCommand_noTickerNeeded(message, command):
  bot.send_message(message.chat.id, 'Invalid use of /{} command.\nPlease refer to /help for walkthough on this command.'.format(command))
  time.sleep(0.5)

def invalidUseOfCommand_noTickerNeeded_admin(message, command):
  bot.send_message(message.chat.id, 'Invalid use of /{} command.\nPlease refer to /helpadmin for walkthough on this command.'.format(command))
  time.sleep(0.5)


def dataNotRetrreived(message, command, tick):
  response = "/{} data not retreived for: {}\nTry using another time frame or recheck ticker. Refer to /help?".format(command.upper(), tick.upper())
  bot.send_message(message.chat.id, response, parse_mode='html')
  time.sleep(0.5)



def notEquity(message, command, tick):
  response = "/{} data is only for equity markets, not for: {}\n".format(command.lower(), tick.upper())
  bot.send_message(message.chat.id, response, parse_mode='html')
  time.sleep(0.5)

def tickerNotValid(message, tick):
  response='Ticker: <b>{}</b> is not valid.\n'.format(tick.upper())
  bot.send_message(message.chat.id, response, parse_mode='html')
  time.sleep(0.5)

def noDataFound(message, command, tick):
  response = 'No /{} data for {}'.format(command.lower(), tick.upper())
  bot.send_message(message.chat.id, response, parse_mode = 'html')
  time.sleep(0.5)
#Atcual model of BTC-USD working 
# stock = 'btc-usd' 
# data = yf.download(tickers = stock, period='2d', interval='15m')
# print(data)
# data.reset_index(inplace = True) 
# fig = plt.figure(figsize=(8,6))
# plt.plot(data[data.columns[0]], data['Open'])
# plt.title("{} Stock prices".format(stock.upper()))
# plt.show()






















#=============ADMIN COMMANDS================#




#Implement: Escalation from admin to superuser
@bot.message_handler(commands=['becomesuper', 'Becomesuper'])
@private_access()
@admin_access()
def become_superuser(message):
  calls_total(message)
  calls_admin(message)

  id = message.from_user.id
  userKey = message.text.split()[-1]
  key = os.getenv('accessTokenSuperuser')
  reply = ''
  
  isSuper = mycol.find({'id': id}, {'info.isSuper':1, '_id':0})
  isSuper = isSuper[0]['info']['isSuper']

  if(isSuper): 
    sendResponse(message, 'You are already a Superuser!')
    return 
  
  if(userKey==key):
  
    mycol.update_one({'id': id}, {'$set': {'info.isSuper': True}})

    reply+='Welcome master! Hope eveything is alright at the wall street.\nI had a word with Bogdanoff, and he asks for our collaboration to manipulate the prices of bitcoin.\nI think good times are just around the corner\n\nTo access the user help docs use: /help\nTo access the admin help docs use: /helpadmin\nTo access the Superuser help docs use: /helpsuper'

    
    print("NEW Superuser: "+str(id))
    print('\n\n')

  else:
    reply+='Incorrect key! Try again\nEg. {} password'.format(message.text.split()[0])
  sendResponse(message, reply)





@bot.message_handler(commands=['adduser', 'Adduser'])
@private_access()
@admin_access()
def add_user(message):
  calls_total(message)
  calls_admin(message)

  input = message.text.split() 
  command = input[0][1:]

  if(len(input)==5):
    
    id = input[1]
    if(id.isnumeric()): id = int(id)
    else:
      sendResponse(message, 'ID must be numeric!')
      return 

    users = mycol.find({}, {'id':1, '_id':0})
    check = id in [x['id'] for x in users]


    if(check):
      error = 'User with id: <b>{}</b> already exists!'.format(id)
      sendResponse(message, error)
      return 

    now = datetime.now(IST)
    first_name = str(input[2])
    last_name = str(input[3])
    join_date = now.strftime('%d/%m/%Y')
    join_time = now.strftime('%I:%M:%S %p')
    username = str(input[4])
    lastUsed = 'NA'

    mycol.insert_one({'id': id, 
                      'watchlist': [],
                      'info': {'first_name': first_name, 
                               'last_name': last_name, 
                               'join_date': join_date, 
                               'join_time': join_time, 
                               'username': username, 
                               'canPredict': True,
                               'nextPrediction': now.strftime('%D %T'), #Using this to get rid of can't comaper offset-naive and offset-aware datetimes 
                               #It removes the microseconds aspect and even the time zone info, comes finally as 2022-02-07 02:14:30+00:00
                               'isSuper': False,
                               'isAdmin': False,
                               'isBlocked': False,
                               'last_used': lastUsed,
                               'count': {'calls_total': 0,
                                         'calls_price': 0,
                                         'calls_financials': 0,
                                         'calls_wl': 0,
                                         'calls_memes': 0,
                                         'calls_admin': 0
                                        }
                              },
                      'commands': {}
                    })
    
    response = 'id: <b>{}</b> is added as <i>user</i>'.format(id)
    print(response)
    sendResponse(message, response)
  
  else:
    invalidUseOfCommand_noTickerNeeded_admin(message, command)







def bot_blacklist(message):
  id = message.from_user.id
  mycol.update_one({'id': id}, {'$set': {'info.isBlocked': True}})
  mycol.update_one({'id': id}, {'$set': {'info.isAdmin': False}})
  

  print('!!!!!!Bot has banned {} for trachery !!!!!!!'.format(message.from_user.id))
  sendResponse(message, 'You are being blocked from the very moment for committing <b>TRACHERY</b>')


@bot.message_handler(commands=['removeuser', 'Removeuser'])
@private_access()
@admin_access()
def delete_user(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  command = terms[0][1:]

  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]
 

  response = ''
  for index, jerk in enumerate(terms):
    if(index==0): continue

    jerkInUser = False

    try:
      jerk = int(jerk)
      if(jerk in users):
        jerkInUser = True
    except:
      pass

    if(jerkInUser):
      id = message.from_user.id
      if(jerk == id):
        response+='You can\'t remove yourself!\n'
        continue
      
      jerk_info = mycol.find_one({'id': jerk})
      isJerkAdmin = jerk_info['info']['isAdmin']
      isJerkSuper = jerk_info['info']['isSuper']
     
      user_info = mycol.find_one({'id': id})
      isUserAdmin = user_info['info']['isAdmin']
      isUserSuper = user_info['info']['isSuper']


      if((isJerkAdmin and isUserAdmin) and ((not isJerkSuper) and (not isUserSuper))): 
        response+='You can\'t remove <b>{}</b>!\n'.format(jerk)
        continue
    
      if(isJerkSuper and isUserAdmin):
        bot_blacklist(message)
        return 

      if(isJerkSuper and isUserSuper):
        sendResponse(message, 'You can\'t remove <b>{}</b>!\n'.format(jerk))
        return 

      print("\n===================\nDeleting user {}. Details are as follows\n".format(jerk))
      print(jerk_info)
      
      mycol.delete_one({'id': jerk})
      users.remove(jerk)
      response+='Removed user: <b>{}</b>\n'.format(jerk)

    else:
      response+='No user found with id <b>{}</b>\n'.format(jerk)

  sendResponse(message, response)





@bot.message_handler(commands=['userinfo', 'Userinfo'])
@private_access()
@admin_access()
def user_info(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  command = terms[0][1:]

  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]
  
  for index, jerk in enumerate(terms):
    if(index==0): continue

    response = ''
    
    jerkInUser = False

    try:
      jerk = int(jerk)
      if(jerk in users):
        jerkInUser = True
    except:
      pass

    if(jerkInUser):
      jerk = int(jerk)

      jerk_info = mycol.find_one({'id': jerk})
      watchlist = jerk_info['watchlist']
      info = jerk_info['info']
      count = info['count']
      
      
      response+='<b>Information of: {}\n\n</b>'.format(info['first_name']+' '+info['last_name'])
      response+='ID: {}\n'.format(jerk)
      response+='First name: {}\n'.format(info['first_name'])
      response+='Last name: {}\n'.format(info['last_name'])
      response+='Join date: {}\n'.format(info['join_date'])
      response+='Join time: {}\n'.format(info['join_time'])
      response+='Username: {}\n'.format(info['username'])
      response+='Is blocked: {}\n'.format(info['isBlocked'])
      response+='Is admin: {}\n'.format(info['isAdmin'])
      response+='Last seen: {}\n\n'.format(info['last_used'])

      response+='\n<b>Watchlist of: {}\n\n</b>'.format(info['first_name']+' '+info['last_name'])
      iswatchlistempty = True
      for ticker in watchlist:
        iswatchlistempty = False
        response+='${} | '.format(ticker.upper())

      if(iswatchlistempty): response+='No tickers found!\n'
      else: response+='\n\n'

      
      response+='\n<b>API calls by: {}\n\n</b>'.format(info['first_name']+' '+info['last_name'])
      
      calls_dict = {
        'calls_total': 'Total calls made',
        'calls_price': 'Price quotations',
        'calls_financials': 'Financials informations',
        'calls_wl': 'Watchlist information',
        'calls_memes': 'Info calls',
        'calls_admin': 'Admin calls'
      }

      for key in count:
        response+='{}: {}\n'.format(calls_dict[key], count[key])

    else:
      response+='No user found with id <b>{}</b>\n'.format(jerk)

    sendResponse(message, response)



@bot.message_handler(commands=['showusers',  'Showusers'])
@private_access()
@admin_access()
def show_users(message):
    calls_total(message)
    calls_admin(message)

    users = mycol.find({}, {'id': 1, '_id': 0})
    users = [x['id'] for x in users]
    
    normal_users = '<b><u>Users with their sign up date</u></b>\n\n'
    blocked_users = '<b><u>Blocked users with their sign up date</u></b>\n\n'
    
    num_blocked = 0
    num_users = 0

    num_blocked = 0
    num_users = 0

    for i in users:
        user_info = mycol.find_one({'id': i})
        first_name = user_info['info']['first_name']
        last_name = user_info['info']['last_name']
        name = '{} {}'.format(first_name, last_name)


        

        areBlocked = False
        if(user_info['info']['isBlocked']):
            num_blocked+=1
            blocked_users+='{}) <b>{}</b>: <i>{} | </i> {}  {}\n'.format(num_blocked, i, name, user_info['info']['join_date'], user_info['info']['join_time'])


        #Changing the code to show all the users, including admins
        # if((not user_info['info']['isAdmin']) and (not user_info['info']['isBlocked'])):
        #     num_users+=1
        #     normal_users+='{}) <b>{}</b> ~ <i>{}:</i> {} ~ {}\n'.format(num_users, i, name, user_info['info']['join_date'], user_info['info']['join_time'])

        if(not user_info['info']['isBlocked']):
            num_users+=1
            normal_users+='{}) <b>{}</b>: <i>{} | </i> {}  {}\n'.format(num_users, i, name, user_info['info']['join_date'], user_info['info']['join_time'])
    
    if(num_users==0):
            normal_users+='No normal users found\n'
    
    if(num_blocked==0):
            blocked_users+='No blocked users found\n'

    sendResponse(message, normal_users+'\n\n'+blocked_users)



@bot.message_handler(commands=['privdesc', 'Privdesc'])
@private_access()
@admin_access()
def priv_desc(message):
  calls_total(message)
  calls_admin(message)

  id = message.from_user.id

  user_info = mycol.find_one({'id': id})
  first_name = user_info['info']['first_name']
  last_name = user_info['info']['last_name']
  name = '{} {}'.format(first_name, last_name)

  if(user_info['info']['isSuper']): 
    response='Master, this command is not you, it\'s for admins only.\n'
    sendResponse(message, response)
    return 

  mycol.update_one({'id': id}, {'$set': {'info.isAdmin': False}})
  response='Done! {}, you are now a normal user'.format(name)
  
  sendResponse(message, response)
 




#=============SUPER USER COMMANDS================#

@bot.message_handler(commands=['makeadmin', 'Makeadmin'])
@private_access()
@super_access()
def make_admin(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  command = terms[0][1:]

  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]

  response = ''
  for index, person in enumerate(terms):
    if(index==0): continue

    personInUser = False

    try:
      person = int(person)
      if(person in users):
        personInUser = True
    except:
      pass

    if(personInUser):
      person = int(person)

      user_info = mycol.find_one({'id': person})
      isPersonBlocked = user_info['info']['isBlocked']
      isPersonAdmin = user_info['info']['isAdmin']
      
      if(isPersonAdmin): 
        response+='<b>{}</b> is already an admin!\n'.format(person)
        continue

      if(isPersonBlocked):
        response+='<b>{}</b> is a blocked user! Try again after whitelisting\n'.format(person)
        continue

      print("\n===================\nAdding user {} as admin\n".format(person))

      mycol.update_one({'id': person}, {'$set': {'info.isAdmin': True}})

      print(user_info)
      print()
      response+='Added user <b>{}</b> as admin\n'.format(person)

    else:
      response+='No user found with id: <b>{}</b>\n'.format(person)

  sendResponse(message, response)




@bot.message_handler(commands=['removeadmin', 'Removeadmin'])
@private_access()
@super_access()
def remove_admin(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  command = terms[0][1:]

  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]
  

  response = ''
  for index, person in enumerate(terms):
    if(index==0): continue

    personInUser = False

    try:
      person = int(person)
      if(person in users):
        personInUser = True
    except:
      pass

    if(personInUser):
      person = int(person)

      if(person==message.from_user.id):
        response+='You can\'t remove yourself as admin. Use /becomeadmin command\n'
        continue
      
      user_info = mycol.find_one({'id': person})
      isPersonBlocked = user_info['info']['isBlocked']
      isPersonAdmin = user_info['info']['isAdmin']
      
      if(not isPersonAdmin): 
        response+='<b>{}</b> not an admin!\n'.format(person)
        continue

      if(isPersonBlocked):
        response+='<b>{}</b> is a blocked user!\n'.format(person)
        continue

      print("\n===================\nRemoving user {} as admin\n".format(person))

      mycol.update_one({'id': person}, {'$set': {'info.isAdmin': False}})
      
      print(user_info)
      print()
      response+='Removed user <b>{}</b> as Admin\n'.format(person)

    else:
      response+='No user found with id <b>{}</b>\n'.format(person)

  sendResponse(message, response)



@bot.message_handler(commands=['userwatchlist', 'Userwatchlist'])
@private_access()
@super_access()
def user_watchlist(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  command = terms[0][1:]

  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]


  
  for index, jerk in enumerate(terms):
    if(index==0): continue

    response = ''

    jerkInUser = False

    try:
      jerk = int(jerk)
      if(jerk in users):
        jerkInUser = True
    except:
      pass

    if(jerkInUser):
      jerk = int(jerk)

      user_info = mycol.find_one({'id': jerk})
      watchlist = user_info['watchlist']
  
  
      response+='Watchlist of: <b>{}</b>\n\n'.format(jerk)

      len_ticker = 0
      for ticker in watchlist:
        len_ticker+=1 
        response+='${}\n'.format(ticker.upper())

      if(len_ticker == 0):
        response+='No tickers found!\n'
      response+='\n\n' 
     

    else:
      response+='No user found with id <b>{}</b>\n'.format(jerk)

    

    sendResponse(message, response)


@bot.message_handler(commands=['usercommands', 'Usercommands'])
@private_access()
@super_access()
def user_commands(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
 
  command = terms[0][1:]
  
  max_limit = ''
  try:
    max_limit = int(terms[-1])
    terms = terms[:-1]
    #max_limit adds tge functionality of geting a custom number of commars for the end
  except:
    terms = terms[:-1]
    max_limit = ''


  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]

  if(max_limit==''):
    for index, jerk in enumerate(terms):
      if(index==0): continue

      response = ''

      jerkInUser = False

      try:
        jerk = int(jerk)
        if(jerk in users):
          jerkInUser = True
      except:
        pass

      if(jerkInUser):

        user_info = mycol.find_one({'id': jerk})
        commands = user_info['commands']
        #commands = dict(reversed(list(commands.items())))

        
        if(len(commands)!=0):
          commands.reverse() 
       

        for query in commands:
          key = list(query.keys())[0]
          value = list(query.values())[0]
          response+='{}: {}\n'.format(key, value)
        if(response==''):
          response='Nothing to show for <b>{}</b>\n'.format(jerk)
        else:
          head = 'Commands ran by user: <b>{}</b>\n\n'.format(jerk)
          response = head+response


      else:
        response+='No user found with id <b>{}</b>\n'.format(jerk)

      sendResponse(message, response)
  
  else:
    for index, jerk in enumerate(terms):
      if(index==0): continue

      response = ''
      
      jerkInUser = False

      try:
        jerk = int(jerk)
        if(jerk in users):
          jerkInUser = True
      except:
        pass

      if(jerkInUser):

        user_info = mycol.find_one({'id': jerk})
        commands = user_info['commands']

        if(len(commands)!=0):
          commands.reverse() 

      
        #commands = commands.reverse()
        #commands = dict(reversed(list(commands.items())))


        i=0
        for query in commands:
          key = list(query.keys())[0]
          value = list(query.values())[0]
          response+='{}: {}\n'.format(key, value)
          
          i+=1
          if(i==max_limit): break
        if(response==''):
          response='Nothing to show for <b>{}</b>\n'.format(jerk)
        else:
          head = 'Commands ran by user: <b>{}</b>\n\n'.format(jerk)
          response = head+response

      else:
        response+='No user found with id <b>{}</b>\n'.format(jerk)

      sendResponse(message, response)





@bot.message_handler(commands=['clearcommands', 'Clearcommands'])
@private_access()
@super_access()
def clear_user_commands(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  
  command = terms[0][1:]
  
  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]
  
  response = ''
  for index, jerk in enumerate(terms):
    if(index==0): continue

    jerkInUser = False

    try:
      jerk = int(jerk)
      if(jerk in users):
        jerkInUser = True
    except:
      pass

    if(not jerkInUser):
      response+='No user found with id <b>{}</b>\n'.format(jerk)

    else:
      commands = mycol.find_one({'id': jerk})['commands']  #get the commands

      if(len(commands)==0):
        response+='Command list of user <b>{}</b> is empty!\n'.format(jerk)
      else:
        sent_msg = bot.send_message(message.chat.id, "Are you sure you want to delete commands ran by <b>{}</b>\nThis action can be undone. ".format(jerk), parse_mode='html')
        bot.register_next_step_handler(sent_msg, delete_commands, jerk) 
        #When next message received, it will call the balancesheet_type function

  sendResponse(message, response)
      


def delete_commands(message, jerk):
  #https://github.com/eternnoir/pyTelegramBotAPI/issues/461#issuecomment-686858030
  #Passing additional context using this command above -> Solved 

  type = message.text.lower()
 
  response = ''

  if(type=='yes'):
    user_info = mycol.find_one({'id': jerk})
    mycol.update_one({'id': jerk}, {'$set': {'commands': []}})
    
    response+='Cleared the commands ran by <b>{}</b>\n'.format(jerk)

  else:
    response+='Action terminated\n'

  sendResponse(message, response)


    

@bot.message_handler(commands=['showadmins', 'Showadmins'])
@private_access()
@super_access()
def show_admins(message):
  calls_total(message)
  calls_admin(message)

  admins = mycol.find({'info.isAdmin': True}, {'id': 1, '_id': 0})
  admins = [x['id'] for x in admins]
  
  response = '<b>Admins with their sign up date</b>\n\n'
  
  admin_count = 0

  if(admins == []):
    response = 'No admins found\n'
    sendResponse(message, response)
    return

  for i in admins:

    user_info = mycol.find_one({'id': i})

    first_name = user_info['info']['first_name']
    last_name = user_info['info']['last_name']
    
    name = first_name + ' ' + last_name

    admin_count += 1 
    response+='{}) <b>{}</b>: <i>{} | </i> {}  {}\n'.format(admin_count, i, name, user_info['info']['join_date'], user_info['info']['join_time'])

  sendResponse(message, response)



@bot.message_handler(commands=['blacklist', 'Blacklist'])
@private_access()
@super_access()
def blacklist(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  command = terms[0][1:]

  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]
 
  id = message.from_user.id

  for index, jerk in enumerate(terms):
    if(index==0): continue

    
    response = ''

    jerkInUser = False

    try:
      jerk = int(jerk)
      if(jerk in users):
        jerkInUser = True
    except:
      pass


    if(jerkInUser):
      
      user_info = mycol.find_one({'id': jerk})
      if(user_info['info']['isBlocked']): 
        response+='User <b>{}</b> is already blacklisted'.format(jerk)
        continue

      if(jerk == id):
        response+='You can\'t blacklist yourself!\n'
        continue
      
      mycol.update_one({'id': jerk}, {'$set': {'info.isBlocked': True}})
      mycol.update_one({'id': jerk}, {'$set': {'info.isAdmin': False}})
    
      response+='Blocked user: <b>{}</b>\n'.format(jerk)

    else:
      response+='No user found with id <b>{}</b>\n'.format(jerk)

  sendResponse(message, response)



@bot.message_handler(commands=['whitelist', 'Whitelist'])
@private_access()
@super_access()
def whitelist(message):
  calls_total(message)
  calls_admin(message)

  terms = message.text.split()
  command = terms[0][1:]

  if(len(terms)<2):
    invalidUseOfCommand_noTickerNeeded_admin(message, command)
    return
  
  users = mycol.find({}, {'id': 1, '_id': 0})
  users = [x['id'] for x in users]
  
  for index, jerk in enumerate(terms):
    if(index==0): continue

    response = ''

    jerkInUser = False

    try:
      jerk = int(jerk)
      if(jerk in users):
        jerkInUser = True
    except:
      pass
    
    if(jerkInUser):
      
      user_info = mycol.find_one({'id': jerk})
      isPersonBlocked = user_info['info']['isBlocked']

      if(not isPersonBlocked): 
        response+='User <b>{}</b> is already whitelisted'.format(jerk)
        continue

      mycol.update_one({'id': jerk}, {'$set': {'info.isBlocked': False}})
      mycol.update_one({'id': jerk}, {'$set': {'info.isAdmin': False}})
      response+='Whitelisted user: <b>{}</b>\n'.format(jerk)

    else:
      response+='No user found with id <b>{}</b>\n'.format(jerk)

  sendResponse(message, response)




@bot.message_handler(commands=['becomeadmin', 'Becomeadmin'])
@private_access()
@super_access()
def become_admin(message):
  calls_total(message)
  calls_admin(message)
 
  id = message.from_user.id
  user_info = mycol.find_one({'id': id})
  first_name = user_info['info']['first_name']
  last_name = user_info['info']['last_name']
  name = first_name + ' ' + last_name
  
  mycol.update_one({'id': id}, {'$set': {'info.isSuper': False}})
  mycol.update_one({'id': id}, {'$set': {'info.isAdmin': True}})
  
  response='Done! Master {}, you are now an admin'.format(name)
  
  sendResponse(message, response)
























#=============MEME COMMANDS================#


@bot.message_handler(commands=['key', 'Key'])
def get_stock(message):
    userKey = message.text.split()[-1]
    key = os.getenv('accessToken')
    reply = ''
    
    users = mycol.find({}, {'id': 1, '_id': 0})
    users = [x['id'] for x in users]

    if(message.from_user.id in users): 
        sendResponse(message, 'You are already an authenticated user')
        return 

    if(userKey==key):
        first_name = str(message.from_user.first_name)
        last_name = message.from_user.last_name
        if(last_name==None): last_name = ''
        
        username = message.from_user.username
        if(username==None): username = ''
        
        dateTime = message.date
        id = message.from_user.id

        reply+='Congratulations, <i>{}</i>, you are now an authenticated user!\nI am Porcellian at your disposal. Use /start to fire me up and /help to get a walkthrough of commands'.format(first_name+' '+last_name)  
        sendResponse(message, reply)

        #img = open('./photos/macd-wsb.jpg', 'rb')
        #bot.send_photo(message.chat.id, img, None)

        
        print("NEW USER: "+ first_name+' '+last_name) 
        print("NEW id: "+str(message.from_user.id))
        print('\n\n')

        now = datetime.fromtimestamp(dateTime).astimezone(IST)
        join_date = now.strftime('%d/%m/%Y')
        join_time = now.strftime('%I:%M:%S %p')


        mycol.insert_one({'id': message.from_user.id, 
                        'watchlist': [],
                        'info': {'first_name': first_name, 
                                'last_name': last_name, 
                                'join_date': join_date, 
                                'join_time': join_time,  
                                'username': username,
                                'canPredict': True,
                                'nextPrediction': datetime.now(IST).strftime('%D %T'), 
                                'isSuper': False,
                                'isAdmin': False,
                                'isBlocked': False,
                                'last_used': datetime.now(IST).strftime('%d/%m/%Y|%I:%M:%S %p'),
                                'count': {'calls_total': 0,
                                            'calls_price': 0,
                                            'calls_financials': 0,
                                            'calls_wl': 0,
                                            'calls_memes': 0,
                                            'calls_admin': 0
                                            }
                                },
                        'commands': []
                        })


    else:
        reply+='Incorrect key! Try again\nEg. {} password'.format(message.text.split()[0])
        sendResponse(message, reply)
  





#IMPLEMENT: Escalation from user to admin
@bot.message_handler(commands=['privesc', 'Privesc'])
@private_access()
def privesc(message):
  calls_total(message)
  calls_admin(message)

  person = message.from_user.id
  userKey = message.text.split()[-1]
  key = os.getenv('accessTokenAdmin')
  reply = ''
  
  user_info = mycol.find_one({'id': person})
  isPersonAdmin = user_info['info']['isAdmin']

  if(isPersonAdmin): 
    sendResponse(message, 'You are already an Admin!')
    return 
  
  if(userKey==key):
    

    first_name = user_info['info']['first_name']
    last_name = user_info['info']['last_name']
    mycol.update_one({'id': person}, {'$set': {'info.isAdmin': True}})

  

    reply+='Congratulations, <i>{}</i>, you are now an Admin.\nWe trust you have received the usual lecture from your conscience. It usually boils down to these three things:\n1) Respect the privacy of others.\n2) Think before you type.\n3) With great power comes great responsibility.\n\nTo access the user help docs use: /help\nUse /helpadmin to get a walkthrough of Admin commands'.format(first_name+' '+last_name)  

     

    print("NEW ADMIN: "+ first_name+' '+last_name) 
    print("NEW ADMIN: "+str(user_info['id']))
    print('\n\n')

  else:
    reply+='Incorrect key! Try again\nEg. {} password'.format(message.text.split()[0])
  sendResponse(message, reply)



 
@bot.message_handler(commands=['calls', 'Calls'])
@private_access()
def total_calls(message):
  calls_memes(message)
  calls_total(message)


  response = 'API calls made by you are as follows:\n\n'

  person = message.from_user.id
  user_info = mycol.find_one({'id': person})
  calls = user_info['info']['count']
  
  calls_dict = {
    'calls_total': 'Total calls made',
    'calls_price': 'Price quotations',
    'calls_financials': 'Financials informations',
    'calls_wl': 'Watchlist information',
    'calls_memes': 'Info calls',
    'calls_admin': 'Admin calls'
  }

  for key in calls:
    #print(key)
    #print(calls_dict[key], calls[key])
    response+='<b>{}</b>: {}\n'.format(calls_dict[key], calls[key])
  
  sendResponse(message, response)
  



@bot.message_handler(commands=['start', 'Start'])
@private_access()
def greeting(message):
  calls_total(message)
  calls_memes(message)

  fn = message.from_user.first_name 
  ln = message.from_user.last_name

  if(ln==None): ln = ""
  name = fn+' '+ln

  user_info = mycol.find_one({'id': message.from_user.id})
  bot.reply_to(message, "Greetings! Please use the /help command for a walkthrough of commands. \nTotal API calls you made: <b>{}</b>".format(user_info['info']['count']['calls_total']), parse_mode="html")



@bot.message_handler(commands=['wsb', 'Wsb'])
@private_access()
def get_banner(message):
  calls_total(message)
  calls_memes(message)


  num = random.randint(1,16)
    
  if(num==1):
    path = './banners/current-wsb-overlay.jpg'
  elif(num==2):
    path = './banners/wsb-beach.jpg'
  elif(num==8):
    path = './banners/wsb-casino.jpg'
  elif(num==3):
    path = './banners/wsb-dollar.jpg'
  elif(num==4): 
    path = './banners/wsb-nyse-guy-overlay.jpg'
  elif(num==5):
    path = './banners/wsb-stock-overlay.jpg'
  elif(num==6):
    path = './banners/wsb-tesla-overlay.png'
  elif(num==7):
    path = './banners/wsb-yatch.png'
  elif(num==9):
    path = './banners/yatch-wsb-overlay.png'
  elif(num==10):
    path = './photos/dfv.jpg'
  elif(num==11):
    path = './photos/crash.jpg'
  elif(num==12):
    path = './photos/loss.jpg'
  elif(num==13):
    path = './photos/gme.jpg'
  elif(num==14): 
    path = './photos/bubble-wsb.jpg'
  else:
    path = './photos/macd-wsb.jpg'

  img = open(path, 'rb')
  bot.send_photo(message.chat.id, img, None)
  




@bot.message_handler(commands=['wsbhidden', 'Wsbhidden'])
@private_access()
def get_wsbhidden(message):
  calls_total(message)
  calls_memes(message)


  response = ""

  stocks = ['gme', 'amc', 'nok', 'BTC-USD']
  stock_data = [] 

  for stock in stocks:
    data = yf.download(tickers=stock,interval='1d', period='3d')

    try:
      data = data.tz_localize('UTC')
    except:
      pass
    data = data.tz_convert(IST)

    data.reset_index(inplace = True)
    response += f"------------{stock}------------\n"

    stock_data.append([stock])
    columns = ['stock']
     
    for index, row in data.iterrows():
      stock_pos = len(stock_data)-1
      price = round(row['Close'], 2)
      format_date = row['Date'].strftime('%m/%d')
      response += f"{format_date}: {price}\n"
      stock_data[stock_pos].append(price)
      columns.append(format_date)
    

  response = f"{columns[0] : <10}{columns[1] : ^12}{columns[2] : >12}\n"
  for row in stock_data: 
    response += f"{row[0].lower() : <10}{row[1] : ^12}{row[2] : >12}\n"
  response += "\nStock Data"
  #print(response)
  sendResponse(message, response)










#=============WATCHLIST COMMANDS================#

@bot.message_handler(commands=['add', 'Add'])
@private_access()
def update_watchlist(message):
  calls_total(message)
  calls_wl(message)


  user = message.from_user.id
  user_info = mycol.find_one({'id': user})
  
  try:
    user_watchlist = user_info['watchlist']
  
  except:
    user_watchlist = []

  
  ticks = message.text.split()
  command = ticks[0][1:]

  response = ''
  for i, ticker in enumerate(ticks):
    if(i==0):
      continue

    if(ticker.upper() in user_watchlist):
      response+='Ticker: <b>{}</b> is already in your watchlist.\n'.format(ticker.upper())
      continue
      

    stock = yf.Ticker(ticker)
    info = stock.info
    if (info['regularMarketPrice'] == None):
      response+='Ticker: <b>{}</b> is not valid.\n'.format(ticker)
    else:
      response+='Ticker: <b>{}</b> is added to your watchlist.\n'.format(ticker.upper())
      user_watchlist.append(ticker.upper())

  if(len(response)==0):
    invalidUseOfCommand(message, command)
    
  else:
    mycol.update_one({'id': user}, {'$set': {'watchlist': user_watchlist}})
    sendResponse(message, response)
  



@bot.message_handler(commands=['getwatchlist', 'Getwatchlist'])
@private_access()
def show_watchlist(message):
  calls_total(message)
  calls_wl(message)
 

  user = message.from_user.id
  response = ''
  user_info = mycol.find_one({'id': user})

  try:
    user_watchlist = user_info['watchlist']
  except:
    user_watchlist = []
 
  if(len(user_watchlist)==0):
    response+='Your watchlist is empty! \nAdd tickers using /add command'
    sendResponse(message, response)
    return

  response+='Your watchlist:\n---------------\n'
  for index, ticker in enumerate(user_watchlist):
    response+='{}) {}\n'.format(index+1, ticker)
  response+='---------------\n\nAdd tickers using /add command\nRemove tickers using /remove command'
  sendResponse(message, response)


def get_current_price(symbol, interval, period):
  ticker = yf.Ticker(symbol)
  interval = '1m'
  period = '1d'
  todays_data = ticker.history(period=period, interval=interval)
  if(todays_data.size>0):
    todays_data.reset_index(inplace=True)
    todays_data=todays_data.tail(1)
    price =  round(todays_data['Close'].iloc[0], 2)
    dateTime = todays_data[todays_data.columns[0]].iloc[0]
    dateTime = dateTime.strftime('%I:%M %p')
  else:
    price = 'NA'
    dateTime = 'NA'

  return price, dateTime


@bot.message_handler(commands=['watchlist', 'Watchlist'])
@private_access()
def show_watchlist_prices(message):
  calls_total(message)
  calls_wl(message)
 

  queries = message.text.split()
  try:
    command = queries[1].lower()
  except:
    command = ''
  
  queries_len = len(queries)

  if(queries_len <2 or (command not in ['price', 'chart'])):
    overallCommand = 'watchlist'
    invalidUseOfCommand_noTickerNeeded(message, overallCommand)
    return


  user = message.from_user.id
  response = ''
  user_info = mycol.find_one({'id': user})

  try:
    user_watchlist = user_info['watchlist']
  except:
    user_watchlist = []

  if(len(user_watchlist)==0):
    response+='Your watchlist is empty! \nAdd tickers using /add command'
    sendResponse(message, response)
    return

  [check1, check2, interval, period, date1, date2] = checkyChecker(queries)

  #For price
  if(command=='price'):
    response+='Latest price data in your watchlist:\n-----------------------------\n\n'
    for index, ticker in enumerate(user_watchlist):
      [price, dateTime] = get_current_price(ticker, interval, period)
      
      if(price=='NA'):
        response += "{}) Failed to retreived price for {} ticker\n".format(index+1, ticker)
      else: 
        response += f"{index+1}) {ticker : <10}{dateTime : ^10}{price : >10}\n"
    
    sendResponse(message, response)


  #For chart 
  if(command=='chart'):
    
    #/wishlist chart line (interval/period or dates - options)
    #/wishlist chart (interval/period or dates - options)
    #/wishlist chart candlestick (interval/period or dates - options)
    #If we receive no argument on candlestick
    graph_type = 'candlestick' #Default set to candlestick
    try: 
      input_graph_type = queries[2] #Try to see if we have a query aafter /wishlist graph
      if(input_graph_type=='line'): #If that query is line, then we shall plot line chart otherwise candlestick
        graph_type = 'line' 
    except:
      graph_type = 'candlestick'
    
    chartAbsent='' #Helps to tell us if the chart is absent 
    for index, tick in enumerate(user_watchlist):
       
      response+='Ticker present in fuction'
      if check2:
        print(tick, date1, date2)
        data = yf.download(tickers = tick, start = date1, end = date2)
      else: 
        print(tick, period, interval)
        data = yf.download(tickers = tick, period = period, interval = interval) 

      try:
        data = data.tz_localize('UTC')
      except:
        pass
      data = data.tz_convert(IST)



      if(data.size>0):
        #Updates the data and makes it presentable
        data.reset_index(inplace = True)
        date_df = data[data.columns[0]]
        date_list = list(date_df)
        first = date_list[0].strftime('%d/%m/%Y|(%I:%M %p)')
        last = date_list[-1].strftime('%d/%m/%Y|(%I:%M %p)')
          

        if(graph_type=='line'):
          #This one uses plotly and plots line chart
          line(data, tick, first, last, message)
          
        elif(graph_type=='candlestick'):
          #This uses graph_objects of plotly
          candlestick(data, tick, first, last, message)

      else:
        #Send text that chart can't be reteived
        chartAbsent += "Chart not retreived for: {}\n".format(tick.upper())
    
    if(chartAbsent!=''): 
      chartAbsent+='\nTry using a bigger time frame.'
      sendResponse(message, chartAbsent)

    if(len(response)==0):
      invalidUseOfCommand(message, command)
        

  


@bot.message_handler(commands=['remove', 'Remove'])
@private_access()
def remove_watchlist(message):
  calls_total(message)
  calls_wl(message)


  user = message.from_user.id
  user_info = mycol.find_one({'id': user})

  try:
    user_watchlist = user_info['watchlist']
  except:
    user_watchlist = []

  ticks = message.text.split()
  command = ticks[0][1:]
  response = ''
  for i, ticker in enumerate(ticks):

    if(i==0):
      continue

    if(ticker.upper() in user_watchlist):
      user_watchlist.remove(ticker.upper())
      response+='Ticker: <b>{}</b> is removed from your watchlist.\n'.format(ticker.upper())
      continue
    
    else:
      response+='Ticker: <b>{}</b> is not found in your watchlist.\n'.format(ticker.upper())


  if(len(response)==0):
    invalidUseOfCommand(message, command)
    
  else:
    mycol.update_one({'id': user}, {'$set': {'watchlist': user_watchlist}})
    sendResponse(message, response)
  















#=============PRICE COMMANDS================#


@bot.message_handler(commands=['predict', 'Predict'])
@private_access()
def making_prediction(message):

  cool_down = 300
  userId = message.from_user.id
  user = mycol.find_one({'id': userId})
  if(user['info']['isAdmin']): cool_down = 0
  
  now = datetime.now(IST)

  current_time = now.strftime('%d/%m/%y %H:%M:%S')
  current_time = datetime.strptime(current_time,'%d/%m/%y %H:%M:%S')
  #We are gatting current time in ISt and then converting into string and back into date time
  
  predict_time = user['info']['nextPrediction']
  predict_time = datetime.strptime(predict_time,'%d/%m/%y %H:%M:%S')

  #The following print commands were for debugging thwe issue #1
  # print(current_time.strftime('%d/%m/%y %H:%M:%S'))
  # print(predict_time.strftime('%d/%m/%y %H:%M:%S'))
  # print(current_time, predict_time)
  # print(current_time - predict_time)
  #In database predict_time is stored as string and here we convert it into a datatime object

  if(current_time>predict_time):
    #time_dilation = current_time-predict_time
    can_user_predict = True
  
  else:
    wait_for = predict_time-current_time
    print(wait_for)
    can_user_predict = False
  
  mycol.update_one({'id': userId}, {'$set': {'info.canPredict': can_user_predict}})
  #mycol.update_many({'info.isSuper': True}, {'$set': {'info.canPredict': True}})

  # print(can_user_predict)
  # print(current_time)
  # print(predict_time)
  user = mycol.find_one({'id': userId})
  if(user['info']['canPredict']):  
    sendResponse(message, 'Hold tight. Predicting...')

    ticks = message.text.split() 
    command = ticks[0].lower()[1:]

    if(len(ticks)<2):
      invalidUseOfCommand(message, command)
      return
    

    stock = ticks[1]
    stock_info = yf.Ticker(stock).info
    if (stock_info['regularMarketPrice'] == None):
      tickerNotValid(message, stock)  
      return 


    

    calls_total(message)
    calls_price(message)

    #Restricting for the next 300 seconds
    mycol.update_one({'id': userId}, {'$set': {'info.nextPrediction': (datetime.now()+timedelta(seconds = cool_down)).strftime('%d/%m/%y %H:%M:%S')}})
    mycol.update_one({'id': userId}, {'$set': {'info.canPredict': False}})


    #Checking if we need to provide output or not
    show_output = False
    inputs_length = len(ticks)
    try: 
      if(inputs_length==3 and ticks[2].lower()=='-output'): show_output = True 
    except:
      pass

    prediction = predict(stock)
    stocks_df = prediction.get_df()

    date_lastday = stocks_df.iloc[-1, 0]
    date = date_lastday + timedelta(days=1)

    #Check if the market is equity type
    try: 
      isEquity = stock_info['quoteType']
    except:
      isEquity = ''

    #Equity markets are close on sundays and saturdays 
    if(isEquity!='CRYPTOCURRENCY'):
      while(date.weekday() in [5,6]):
        date = date + timedelta(days=1)
    #Now we have the date which we are predicting for 

  
    myPrediction = prediction.updatedRRModelStandAloneV1(stocks_df, 0.0001, 1)
    LRScore = round(myPrediction[0], 4)
    predicted_df = myPrediction[1]
    predict_df_for_metrics = predicted_df.copy()
    yesterday_price = round(myPrediction[2], 2)
    future_price = round(myPrediction[3], 2)

    predicted_metrics = prediction.get_metrics(predict_df_for_metrics, date, stock, future_price)
    mape = round(predicted_metrics[0], 2)
    trueError_average = predicted_metrics[1]
    #trueError_std = predicted_metrics[2]
    #minus_sd = predicted_metrics[3]
    #plus_df = predicted_metrics[4]
    minus_price = round(predicted_metrics[5], 2)
    plus_price = round(predicted_metrics[6], 2)
    future_price = round(future_price * ((100 - trueError_average)/100), 2)
    true_error_df = predicted_metrics[7]


    #All the sementics are with us, only send messages and charts now
    response=''
    response+='Predictions for <b>{}</b>\n\n'.format(stock.upper())
    response+='Date: <b>{}</b>\n'.format(date.strftime('%d/%m/%Y'))  
    response+='LR Score: <b>{}</b>\n'.format(LRScore)
    response+='MAPE: <b>{}</b>\n'.format(mape)
    response+='Predicted Price: <b>{}</b>\n'.format(future_price)
    response+='Yesterday\'s Closing price: <b>{}</b>\n'.format(yesterday_price)
    response+='Expected %Change: <b>{}</b>\n'.format(round(((future_price-yesterday_price)*100)/yesterday_price, 2))
    response+='Expected price range: <b>{}</b>-<b>{}</b>\n'.format(minus_price, plus_price)
    response+='Expected %Change range: <b>{}</b> to <b>{}</b>\n\n'.format(round(((minus_price-yesterday_price)*100)/yesterday_price, 2), round(((plus_price-yesterday_price)*100)/yesterday_price, 2))
    response+='<b><i>This model is in Alpha stage!\n</i></b>\n'
    sendResponse(message, response)
    
    if(show_output):

      #Trying to work with the seaborn 
      #Ended up working with the plotly distplot and sending image as a buffer 
      #ff.create_distplot()
      data = true_error_df.copy()[:-2]
      fig = ff.create_distplot([data['True Error (with Target)'].tolist()], ['True Error (with Target)'],bin_size=.1, show_rug=False)
      fig.update_layout({
        'title': 'Distribution of True Error',
        'xaxis': {'title': 'True Error in predictions (%)',
                  'range': [-50, 50]},
        'yaxis': {'title': 'Density'},
        'font': {'family': 'Arial',
                    'size': 12,
                    'color': 'black'},
        #'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'height': 650,
        'width': 1300,
        'margin': {'l': 40, 'r': 40, 'b': 40, 't': 40},
        'showlegend': False
      })

      img_bug = io.BytesIO()
      fig.write_image(img_bug, format='png')
      bot.send_photo(message.chat.id, Image.open(img_bug), "Distplot for True error: <b>{}</b>".format(stock.upper()), 'html')
      img_bug.close()

      #sending the True error
      # fig = prediction.get_histogram(predicted_df, stock)
      # img_bug = io.BytesIO()
      # fig.savefig(img_bug, format='png')
      # bot.send_photo(message.chat.id, Image.open(img_bug), "{}_trueError".format(stock.upper()), 'html')
      # img_bug.close()


      #Trying something new
      # fig = plt.figure(figsize=(12,16))
      # sns.displot(predicted_df['True Error (with Target)'], kde=True)

      # img_bug = io.BytesIO()
      # plt.savefig(img_bug, format='png')
      # bot.send_photo(message.chat.id, Image.open(img_bug), "{}_trueError".format(stock.upper()), 'html')
      # img_bug.close()

    
    
      #Sending the line chart of past prices
      #The below part is working for producting a line chart 
      #now I do not want to plot this chart as it is pointless 
      '''fig = px.line(title = 'Test title')
      data = predicted_df
      for stock in data.columns[1:]:
        fig.add_scatter(x=data['Date'], y=data[stock], name=stock)


      img_bug = io.BytesIO()
      fig.write_image(img_bug, format='png')
      bot.send_photo(message.chat.id, Image.open(img_bug), "{}_prediction".format(stock.upper()), 'html')
      img_bug.close()'''
      
      #The below lines can be used to make the chart in a better way
      '''fig.update_layout(
      title="Candlestick chart for ${} from {} to {}".format(tick.upper(), first, last),
      yaxis_title="Price",
      xaxis_title="Timeframe",
      width=1300, 
      height=650,
      font=dict(
          family="Courier New, monospace",
          size=18,
          color="RebeccaPurple"
              )
      )'''      

      # fig = prediction.interactivePlot(predicted_df, 'Prices for {}'.format(stock.upper()))
      # fig.update_layout(
      # yaxis_title="Price",
      # xaxis_title="Timeframe",
      # width=1300, 
      # height=650,
      # font=dict(
      #     family="Courier New, monospace",
      #     size=18,
      #     color="RebeccaPurple"
      #         )
      # )
      # img_bug = io.BytesIO()
      # fig.savefig(img_bug, format='png')
      # bot.send_photo(message.chat.id, Image.open(img_bug), "{}_prediction</b>".format(stock.upper()), 'html')
      # img_bug.close()




      #Sending the csv file
      textStream = io.StringIO()
      true_error_df.to_csv(textStream, index=False)
      textStream.seek(0)
      #print(textStream.getvalue())
      #predicted_df.to_csv(textStream, sep='\t', encoding='utf-8')
      #bot.send_document(message.chat.id, textStream, "{}_prediction".format(stock.upper()), 'csv')
      bot.send_document(message.chat.id, textStream, caption="{}_trueError".format(stock.upper()), visible_file_name='{}_trueError.csv'.format(stock.upper()))
      textStream.close()
      #csv_buffer = io.BytesIO()
      #predicted_df.to_csv(csv_buffer, index=False)
      #The documents are sent





  else:
    sec = int(wait_for.total_seconds())
    min = sec//60
    sec = sec%60
    sendResponse(message, 'You can only use this command once every five minutes.\nTry again in {}:{}'.format(min, sec))







def stock_request(message):
  request = message.text.split()
  if(len(request) < 2 or request[0].lower() not in "price"):
    return False
  return True



#@bot.message_handler(func = stock_request)
@bot.message_handler(commands=['price', 'Price'])
@private_access()
def send_custom_ticker(message): 
  calls_total(message)
  calls_price(message)


  response = ''

  # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
  # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
  ticks = message.text.split() 
  ticks_len = len(ticks) 
  command = ticks[0][1:]

  if(ticks_len<2):
    invalidUseOfCommand(message, command)
    return 
  [check1, check2, interval, period, date1, date2] = checkyChecker(ticks)
  
  
  dataNotReceived = ''

  for index, tick in enumerate(ticks):
    response = '=====' + tick.upper()+'=====\n'
    response += '--------\nPeriod: {}\nInterval: {}\n--------\n\n'.format(period, interval)
    if(index==0): continue
  
    if((check1 or check2) and (index==ticks_len-1 or index==ticks_len-2)):
      continue

    if check2:
      print(tick, date1, date2)
      data = yf.download(tickers = tick, start = date1, end = date2)
    else:  
      print(tick, period, interval)
      data = yf.download(tickers = tick, period = period, interval = interval) 

    try:
      data = data.tz_localize('UTC')
    except:
      pass
    data = data.tz_convert(IST)

  
    if(data.size>0):
      data.reset_index(inplace = True)
      data['format_date'] = data[data.columns[0]].dt.strftime('%d/%m/%Y|%I:%M %p')
      data.set_index('format_date', inplace = True) 
      #print(data.to_string())
      
      response+=data['Close'].to_string(header=False) 
      response += '\n\n'
    else:
      dataNotReceived+='/{} data not retreived for: {}\n'.format(command, tick.upper())
      
      response = ''
      #Only 7 days worth of 1m granularity data are allowed to be fetched per request.		  
      #The requested range must be within the last 60 days.

    sendResponse(message, response)
  
  if(dataNotReceived!=''):
    dataNotReceived+='\nCheck if the ticker is valid or try using another time frame.'
    sendResponse(message, dataNotReceived)









def chart_request(message):
  request = message.text.split()
  if(len(request) < 2 or request[0].lower() not in "chart"):
    return False
  return True

#@bot.message_handler(func = chart_request)
@bot.message_handler(commands=['candlestick', 'line', 'Candlestick', 'Line'])
@private_access()
def send_chart(message): 
  calls_total(message)
  calls_price(message)


  response = ''

  # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
  # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
  ticks = message.text.split() 
  command = ticks[0][1:]
  ticks_len = len(ticks) 

  if(ticks_len <2):
    invalidUseOfCommand(message, command)
    return


  [check1, check2, interval, period, date1, date2] = checkyChecker(ticks)
  
  chartAbsent = '' #Sends message if the chart is not found
  for index, tick in enumerate(ticks):
    
    if(index==0): continue
    if((check1 or check2) and (index==ticks_len-1 or index==ticks_len-2)):
      continue

    response+='Ticker present in fuction'
    if check2:
      print(tick, date1, date2)
      data = yf.download(tickers = tick, start = date1, end = date2)
    else: 
      print(tick, period, interval)
      data = yf.download(tickers = tick, period = period, interval = interval) 


    try:
      data = data.tz_localize('UTC')
    except:
      pass
    data = data.tz_convert(IST)

    if(data.size>0):
      
      #This one uses matplotlib bor line chart
      '''data.reset_index(inplace = True)
      fig = plt.figure(figsize=(12, 16))
      plt.plot(data[data.columns[0]], data['Close'])
      plt.grid()
      plt.title("Chart for {}".format(tick))

      img_bug = io.BytesIO()
      plt.savefig(img_bug, format='png')
      #im = Image.open(img_bug)
      
      bot.send_photo(message.chat.id, Image.open(img_bug), "Chart for <b>{}</b>".format(tick), 'html')
      #data['format_date'] = data[data.columns[0]].dt.strftime('%d/%m/%Y %I:%M %p')
      #data.set_index('format_date', inplace = True) 
      img_bug.close()'''

      #Updates the data and makes it presentable
      data.reset_index(inplace = True)
      date_df = data[data.columns[0]]
      date_list = list(date_df)
      first = date_list[0].strftime('%d/%m/%Y|(%I:%M %p)')
      last = date_list[-1].strftime('%d/%m/%Y|(%I:%M %p)')
        

      if(command=='line'):
        #This one uses plotly and plots line chart
        line(data, tick, first, last, message)

      elif(command=='candlestick'):
        #This uses graph_objects of plotly
        candlestick(data, tick, first, last, message)

    else:
      #Send text that chart can't be reteived
      chartAbsent += "Chart not retreived for: {}\n".format(tick.upper())
  
  if(chartAbsent!=''): 
    chartAbsent+='\nCheck if tickers are valid or try changing timeframe.' 
    sendResponse(message, chartAbsent)
  

  if(len(response)==0):
    invalidUseOfCommand(message, command)
    







#=============FINANCE COMMANDS================#


@bot.message_handler(commands=['info', 'Info'])
@private_access()
def send_info(message):
  calls_total(message)
  calls_financials(message)


  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info

    try:  
      if(info==None or len(info)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    if(info['regularMarketPrice']!=None):
      response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

      try: 
        bot.send_photo(message.chat.id, info['logo_url'], "<i><b>{}</b> logo</i>".format(tick.upper()), "html")
      except:
        pass
            
      for key in info:
        response+='<b>{}</b>: {}\n'.format(key, info[key])
        
    else:
      tickerNotValid(message, tick)

    sendResponse(message, response)





@bot.message_handler(commands=['splits', 'Splits'])
@private_access()
def send_splits(message):
  calls_total(message)
  calls_financials(message)


  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    splits = stock.splits

    try: 
      if(splits==None or len(splits)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    try: 
      isEquity = info['quoteType']
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        splits_df = pd.DataFrame(data=splits)
        splits_df.reset_index(inplace = True)
        splits_df['format_date'] = splits_df[splits_df.columns[0]].dt.strftime('%d/%m/%Y')
        splits_df.set_index('format_date', inplace = True)
        response+=splits_df['Stock Splits'].to_string(header=False) 
        response += '\n\n'
        
      else:
        notEquity(message, command, tick)

    sendResponse(message, response)



@bot.message_handler(commands=['dividends', 'Dividends'])
@private_access()
def send_dividends(message):
  calls_total(message)
  calls_financials(message) 


  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    dividends = stock.dividends

    try:
      if(dividends==None or len(dividends)==0):
        noDataFound(message, command, tick)
      return
    except:
      pass

    try: 
      isEquity = info['quoteType']
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        dividends_df = pd.DataFrame(data=dividends)
        dividends_df.reset_index(inplace = True)
        dividends_df['format_date'] = dividends_df[dividends_df.columns[0]].dt.strftime('%d/%m/%Y')
        dividends_df.set_index('format_date', inplace = True)
        response+=dividends_df['Dividends'].to_string(header=False) 
        response += '\n\n'
        
      else:
        notEquity(message, command, tick)

    sendResponse(message, response)




@bot.message_handler(commands=['analysis', 'Analysis'])
@private_access()
def send_analysis(message):
  calls_total(message)
  calls_financials(message)

  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  try:  
    if(len(ticks)<2):
      invalidUseOfCommand(message, command)
      return
  except:
    pass

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info

    #Had the same issue as that with shares
    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if(isEquity!='EQUITY'):
      notEquity(message, command, tick)
      continue


    anal = stock.get_analysis(as_dict=True)

    try:
      if(anal==None or len(anal)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        for key in anal:
          
          response+='<b>{}</b>\n'.format(key)
          query = anal[key]
          for interval in query:
            response+='{}: {}\n'.format(interval, query[interval])
          response+='\n\n'

      else:
        notEquity(message, command, tick)

    sendResponse(message, response)





@bot.message_handler(commands=['balancesheet', 'Balancesheet'])
@private_access()
def send_balancesheet(message):
  calls_total(message)
  calls_financials(message)

  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    
    try: 
      isEquity = info['quoteType']
    except:
      isEquity = ''

    try:
      if (info['regularMarketPrice'] == None):
        tickerNotValid(message, tick)
    except:
      pass

    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        sent_msg = bot.send_message(message.chat.id, "'Annual' or 'Quarterly' balancesheet for {}?".format(tick.upper()))
        bot.register_next_step_handler(sent_msg, balancesheet_type, stock, command, response, tick) #When next message received, it will call the balancesheet_type function
      else:
        notEquity(message, command, tick)

def balancesheet_type(message, stock, command, response, tick):
  #https://github.com/eternnoir/pyTelegramBotAPI/issues/461#issuecomment-686858030
  #Passing additional context using this command above -> Solved 
  type = message.text.lower()
  
  if(type=='quarterly'):
    bs = stock.get_balancesheet(as_dict=True, freq='quarterly')
  elif(type=='annual'):
    bs = stock.get_balancesheet(as_dict=True, freq='quarterly')
  else:
    invalidUseOfCommand(message, command)
    return 

  try:
    if(bs==None or len(bs)==0):
      noDataFound(message, command, tick)
      return
  except:
    pass

  for date in bs:
    response+='<b>{}</b>\n'.format(date.strftime('%d/%m/%Y'))
    query = bs[date]
    for term in query:
      response+='<i>{}:</i> {}\n'.format(term, query[term])
    response+='\n\n'

  sendResponse(message, response)










@bot.message_handler(commands=['calendar', 'Calendar'])
@private_access()
def send_calendar(message):
  calls_total(message)
  calls_financials(message)


  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  try:  
    if(len(ticks)<2):
      invalidUseOfCommand(message, command)
      return
  except:
    pass

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if(isEquity!='EQUITY'):
      notEquity(message, command, tick)
      continue

    cal = stock.get_calendar(as_dict=True)

    try:
      if(cal==None or len(cal)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        for key in cal:

          response+='<b>{}</b>\n'.format(key)
          query = cal[key]
          for interval in query:
            response+='{}: {}\n'.format(interval, query[interval])
          response+='\n\n'

      else:
        notEquity(message, command, tick)

    sendResponse(message, response)





@bot.message_handler(commands=['cashflow', 'Cashflow'])
@private_access()
def send_cashflow(message):
  calls_total(message)
  calls_financials(message)

  
  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    cashflow = stock.get_cashflow(as_dict=True)

    try:  
      if(cashflow==None or len(cashflow)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        for key in cashflow:
          response+='<b>{}</b>\n'.format(key.strftime('%d/%m/%Y'))
          query = cashflow[key]
          for interval in query:
            response+='{}: {}\n'.format(interval, query[interval])
          response+='\n\n'

      else:
        notEquity(message, command, tick)

    sendResponse(message, response)





@bot.message_handler(commands=['earnings', 'Earnings'])
@private_access()
def send_earnings(message):
  calls_total(message)
  calls_financials(message)

  
  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    earnings = stock.get_earnings(as_dict=True)

    try:
      if(earnings==None or len(earnings)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        for key in earnings:
          response+='<b>{}</b>\n'.format(key)

          if(type(earnings[key])==str):
            response+='{}: {}\n'.format(key, earnings[key])
          else:
            query = earnings[key]
            for interval in query:
              response+='{}: {}\n'.format(interval, query[interval])
          response+='\n\n'

      else:
        notEquity(message, command, tick)

    sendResponse(message, response)




@bot.message_handler(commands=['financials', 'Financials'])
@private_access()
def send_financials(message):
  calls_total(message)
  calls_financials(message)

  
  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    financials = stock.get_financials(as_dict=True)
    
    try:
      if(financials==None or len(financials)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'

        for key in financials:
          response+='<b>{}</b>\n'.format(key.strftime('%d/%m/%Y'))
          query = financials[key]
          for interval in query:
            response+='{}: {}\n'.format(interval, query[interval])
          response+='\n\n'

      else:
        notEquity(message, command, tick)

    sendResponse(message, response)




@bot.message_handler(commands=['institutional_holders', 'Institutional_holders'])
@private_access()
def send_institutional_holders(message):
  calls_total(message)
  calls_financials(message)

  
  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    institutional_holders = stock.get_institutional_holders(as_dict=True)
    
    try:
      if(institutional_holders==None or len(institutional_holders)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    # try: 
    #   isEquity = info['quoteType']
    #   #Coz the Futures do no have the quoteType" Equity in them 
    # except:
    #   isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      #No need to check for isEquity as futures and crypto support it 
      response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'
      for key in institutional_holders:
        response+='<b>{}</b>\n'.format(key)
        query = institutional_holders[key]
        for interval in query:
          response+='{}: {}\n'.format(interval, query[interval])
        response+='\n\n'

    sendResponse(message, response)




@bot.message_handler(commands=['major_holders', 'Major_holders'])
@private_access()
def send_major_holders(message):
  calls_total(message)
  calls_financials(message)
  

  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    major_holders = stock.get_major_holders(as_dict=True)

    try:
      if(major_holders==None or len(major_holders)==0):
        noDataFound(message, command, tick)
        return
    except:
      pass

    # try: 
    #   isEquity = info['quoteType']
    #   #Coz the Futures do no have the quoteType" Equity in them 
    # except:
    #   isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      #No need to check for isEquity as futures and crypto support it 
      response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'
      for key in major_holders:
        response+='<b>{}</b>\n'.format(key)
        query = major_holders[key]
        for interval in query:
          response+='{}: {}\n'.format(interval, query[interval])
        response+='\n\n'

    sendResponse(message, response)




@bot.message_handler(commands=['mutualfund_holders', 'Mutualfund_holders'])
@private_access()
def send_mutualfund_holders(message):
  calls_total(message)
  calls_financials(message)
 

  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    mutualfund_holders = stock.get_mutualfund_holders(as_dict=True)

    try:  
      if(mutualfund_holders==None or len(mutualfund_holders)==0):
        noDataFound(message, command, tick)
        return 
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      if(isEquity=='EQUITY'):
        response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'
        #This is only for EQUITY market, so  isEquity is applied here and futures or crypto won't go furthur

        for key in mutualfund_holders:

          response+='<b>{}</b>\n'.format(key)
          query = mutualfund_holders[key]
          for interval in query:
            response+='{}: {}\n'.format(interval, query[interval])
          response+='\n\n'

      else:
        notEquity(message, command, tick)

    sendResponse(message, response)








@bot.message_handler(commands=['news', 'News'])
@private_access()
def send_news(message):
  calls_total(message)
  calls_financials(message)


  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info
    news = stock.get_news()
 
    try:  
      if(news==None or len(news)==0):
        noDataFound(message, command, tick)
        return 
    except:
      pass

    # try: 
    #   isEquity = info['quoteType']
    #   #Coz the Futures do no have the quoteType" Equity in them 
    # except:
    #   isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      #Not using the isEquity, as news is common to all 
      #If there comes any error, use isEquity from the above command 
      response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'
      for i, key in enumerate(news):

        response+='<b>News article #{}</b>\n'.format(i+1)

        for interval in key:
          response+='{}: {}\n'.format(interval, key[interval])
        response+='\n\n'

    
    sendResponse(message, response)





@bot.message_handler(commands=['shares', 'Shares'])
@private_access()
def send_shares(message):
  calls_total(message)
  calls_financials(message)


  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if(isEquity!='EQUITY'):
      notEquity(message, command, tick)
      continue
    #Some issue like, 'NoneType' object has no attribute 'to_dict so added this line
    shares = stock.get_shares(as_dict=True)
 
    try:  
      if(shares==None or len(shares)==0):
        noDataFound(message, command, tick)
        return 
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      #Not using the isEquity, as news is common to all 
      #If there comes any error, use isEquity from the above command 
      response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'
      for key in shares:

        response+='<b>{}</b>\n'.format(key)
        query = shares[key]
        for interval in query:
          response+='{}: {}\n'.format(interval, query[interval])
        response+='\n\n'

    
    sendResponse(message, response)






@bot.message_handler(commands=['sustainability', 'Sustainability'])
@private_access()
def send_sustainability(message):
  calls_total(message)
  calls_financials(message)


  ticks = message.text.split() 
  command = ticks[0].lower()[1:]

  if(len(ticks)<2):
    invalidUseOfCommand(message, command)
    return

  for index, tick in enumerate(ticks):
    if(index==0): continue

    response = ''

    stock = yf.Ticker(tick)
    info = stock.info

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if(isEquity!='EQUITY'):
      notEquity(message, command, tick)
      continue
    #Some issue like, 'NoneType' object has no attribute to_dict so added this line
    sustainability = stock.get_sustainability(as_dict=True)
 
    try:  
      if(sustainability==None or len(sustainability)==0):
        noDataFound(message, command, tick)
        return 
    except:
      pass

    try: 
      isEquity = info['quoteType']
      #Coz the Futures do no have the quoteType" Equity in them 
    except:
      isEquity = ''

    if (info['regularMarketPrice'] == None):
      tickerNotValid(message, tick)
    
    else:
      #Not using the isEquity, as news is common to all 
      #If there comes any error, use isEquity from the above command 
      response = '====={}: '.format(command.upper()) + tick.upper()+'=====\n\n'
      for key in sustainability:

        response+='<b>{}</b>\n'.format(key)
        query = sustainability[key]
        for interval in query:
          response+='{}: {}\n'.format(interval, query[interval])
        response+='\n\n'

    
    sendResponse(message, response)






#=============HELP COMMANDS================#


@bot.message_handler(commands=['help', 'Help'])
def send_help(message):
  response = '<b><u>PRICE COMMANDS</u></b>\n\n'
  
  response+='1) <b>/predict</b> {ticker} {-output(optional)}\n\n'
  response+='-Predicts the closing price of and ticker (once very five minutes). Use the output parameter to get output\n'
  response+='<u>Eg</u>: /predict BABA -output\nPricts the price for Alibaba Group Holding Limited and provides output.\n\n'

  response+='2) <b>/price</b> {tickers} {date1} {date2}\n\n'
  response+='-ticker: add space seperated tickers (Lookup for tickers on<a href="https://finance.yahoo.com/lookup/">Yahoo! Finance</a>)\n'
  response+='-date1: Start date of prices or period.\n'
  response+="-Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max\n"
  response+='-date2: End date of prices or interval\n'
  response+="-Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo\n"
  response+='-If interval is 1m, period can\'t be more than 7days\n\n'
  response+='<u>Eg</u>: /price gme nvda nflx 2019-01-01 2021-01-29\nPrints prices for GME, NVDA and NFLX from 1st Jan 2019 to 29 Jan 2022.\n\n'
  response+='<u>Eg</u>: /price spy reliance.ns ^NSEI GC=F 20wk 1h\nPrints prices for SP500, Reliance, Nifty and gold-futures for last 20 weeks on 1h time interval\n\n'
  response+='<u>Eg</u>: /price GM \nPrints price of GM for last 5 minutes on 1 minute interval. This is the default parameter, if your provided parameters are invalid, default parameter will be used.\n\n\n'


  response+='3) <b>/candlestick</b> {tickers} {date1} {date2}\n\n'
  response+='-Plots a candlestick chart for the time provided. Date parameters are same as price command\n\n'
  response+='<u>Eg</u>: /candlestick gme nvda nflx 2019-01-01 2021-01-29\nPlots candlestick chart for GME, NVDA and NFLX from 1st Jan 2019 to 29 Jan 2022.\n\n'
  response+='<u>Eg</u>: /candlestick spy reliance.ns ^NSEI GC=F 100d 1h\nPlots candlestick chart for SP500, Reliance, Nifty and gold-futures for last 100days on 1h time interval\n\n'
  response+='<u>Eg</u>: /candlestick GM \nPlots candlestick chart of GM for last 5 minutes on 1 minute interval.\n\n\n'

  response+='4) <b>/line</b> {tickers} {date1} {date2}\n\n'
  response+='-Plots line chart for the time interval. Time parameters are same as price command\n\n'
  response+='<u>Eg</u>: /line gme nvda nflx 2019-01-01 2021-01-29\nPlots line chart for GME, NVDA and NFLX from 1st Jan 2019 to 29 Jan 2022.\n\n'
  response+='<u>Eg</u>: /line spy reliance.ns ^NSEI GC=F 100d 1h\nPlots line chart for SP500, Reliance, Nifty and gold-futures for last 100days on 1h time interval\n\n'
  response+='<u>Eg</u>: /line GM \nPlots line chart of GM for last 5 minutes on 1 minute interval.\n\n\n\n'


  

  response+='<b><u>WATCHLIST COMMANDS</u></b>\n\n'
  
  response+='5) <b>/watchlist</b> {price/chart} {line/candlestick(optional)} {date1} {date2}\n\n'
  response+='-Providess price-data/chart. Time parameters are same as price command\n'
  response+='-Default chart is candlestick, line chart can be obtained by third argument\n\n'
  response+='<u>Eg</u>: /watchlist price\nPrints latest prices for your tickers\n\n'
  response+='<u>Eg</u>: /watchlist chart 100d 1h\nPlots line candlestick chart for your tickers for last 100days on 1h time interval\n\n'
  response+='<u>Eg</u>: /watchlist chart line 2d 1m \nPlots line chart of your tickers for last 2 days on 1 minute interval.\n\n'
  response+='<u>Eg</u>: /watchlist chart line \nPlots line chart of your tickers for last 5 minutes on 1 minute interval.\n\n'
  response+='<u>Eg</u>: /watchlist chart candlestick 2019-01-01 2021-01-29 \nPlots candlestick chart of your tickers from 1st jan 2019 to 29th jan 2022.\n\n\n'

  response+='6) <b>/add</b> {tickers}\n'
  response+='-Adds tickers to your watchlist\n\n'
  
  response+='7) <b>/remove</b> {tickers}\n'
  response+='-Removes tickers from your watchlist\n\n'

  response+='8) <b>/getewatchlist</b> {tickers}\n'
  response+='-Shows contents of your watchlist\n\n'

  response+='9) <b>/calls</b> {tickers}\n'
  response+='-Breakdown of total API calls by you\n\n\n\n'




  response+='<b><u>FINANCE COMMANDS</u></b>\n\n'

  response+='10) <b>/info</b> | <b>/news</b> | <b>/balancesheet</b> | <b>/cashflow</b> | <b>/sustainability</b> | <b>/analysis</b> | <b>/calendar</b> | <b>/splits</b>, <b>/dividends</b> | <b>/earnings</b> | <b>/financials</b>, <b>/institutional_holders</b> | <b>/major_holders</b> | <b>/mutualfund_holders</b> | <b>/shares</b>\n'
  response+='-Functions followed by tickers. Only tickers of Equity market allowed\n\n'
  response+='<u>Eg</u>: /balancesheet msdt reliance.ns BA T 10d 1h\nPrints the balancesheet of Microsoft, Reliance, Boeing and AT&T\n\n\n\n'



  response+='<b><u>MEME COMMANDS</u></b>\n\n'
  response+='11) <b>/wsb</b>\n'
  response+='-A banner from <a href="https://www.reddit.com/r/wallstreetbets/">r/wsb</a>\n\n'
  
  response+='12) <b>/start</b>\n'
  response+='-Starts the bot\n\n'

  response+='12) <b>/key</b>\n'
  response+='-Get authorized to use the bot.\n\n'

  response+='<b><u>ADMIN COMMANDS</u></b>\n\n'
  response+='13) <b>/privesc</b>\n'
  response+='-Get admin access\n'
  response+='14) <b>/helpadmin</b>\n'
  response+='-Admin help docs'
  response+='\n\n\n\n'
  bot.send_message(message.chat.id, response, parse_mode='html')

 
  response=''
  response+='---------<b>Special instructions</b>---------\n\n'
  response+='1. Get price quotation for Indices, Forex, ETFs, Mutual Funds, Cryptocurrency, Stocks, Commodity Futures, US Treasury bond rates\n'
  response+='2. Adding tickers takes time - because it undergoes authentication\n'
  response+='3. Let me know if there are any bugs <a href="https://tally.so/r/mBgk43">here</a>\n'
  response+='5. Treshold on API calls is not tested, if the limit is excedded, Porcellian will hand in resignation\n'
  response+='4. I follow IST (UTC +5:30) time zone\n'
  response+='6. Finance commands have higher time complexity \n'
  response+='7. Predicting prices for tickers may take >30 seconds \n'
  response+='-----------------------------------\n\n'
  response+='BUY HIGH, SELL LOW!\n©  Porcellian'
  bot.send_message(message.chat.id, response, parse_mode='html')

 






@bot.message_handler(commands=['helpadmin', 'Helpadmin'])
@admin_access()
def send_helpadmin(message):
  response = '<b><u>ADMIN COMMANDS</u></b>\n\n\n'
  
  response+='1) <b>/privdesc</b>\n'
  response+='Downgrades your access to normal user\n\n'
  
  response+='2) <b>/becomesuper</b> {acessToken}\n'
  response+='Gain superuser priviledges\n\n'

  response+='3) <b>/adduser</b> {ID} {FirstName} {SecondName} {Username}\n'
  response+='Adds the said user as a normal user\n\n'

  response+='4) <b>/removeuser</b> {IDs}\n'
  response+='Revokes the access of usernames from the script and database is erased\n\n'
    
  response+='5) <b>/userinfo</b> {IDs}\n'
  response+='Provides user information of the said usernames. Admins are not shown here. (So you won\'t find your own info here)\n\n'
  
  response+='6) <b>/showusers</b>\n'
  response+='Shows the Usernname, names with their sign up dates for users and blocked users.\n\n\n'

  response+='<b><u>SUPERUSER COMMANDS</u></b>\n\n'
  response+='7) <b>/becomesuper</b>\n'
  response+='Get Superuser access\n'
  response+='8) <b>/helpsuper</b>\n'
  response+='Superuser help docs'
  
  
  bot.send_message(message.chat.id, response, parse_mode='html')









@bot.message_handler(commands=['helpsuper', 'Helpsuper'])
@super_access()
def send_helpsuper(message):
  response = '<b><u>SUPERUSER COMMANDS</u></b>\n\n\n'
  
  response+='1) <b>/makeadmin</b> {IDs}\n'
  response+='Provide admin access to usernames\n\n'
  
  response+='2) <b>/removeadmin</b> {IDs}\n'
  response+='Revoke admin access from usernames\n\n'

  response+='3) <b>/userwatchlist</b> {IDs}\n'
  response+='Shows watchlist of usernames\n\n'

  response+='4) <b>/usercommands</b> {IDs} {integer/all}\n'
  response+='Shows latest commands ran by users. Ifnumber is given at last, then it cuts down results to that number\n\n'

  response+='5) <b>/clearcommands</b> {IDs}\n'
  response+='Clear the commands ran by usernames\n\n'
    
  response+='6) <b>/showadmins</b>\n'
  response+='Shows the Usernname, names with their sign up dates of admins\n\n'
  
  response+='7) <b>/blacklist</b> {IDs}\n'
  response+='Blacklists the usernames and restricts access to the bot at all\n\n'

  response+='8) <b>/whitlist</b> {IDs}\n'
  response+='Whitelists the usernames and provides access to the bot\n\n'

  response+='9) <b>/becomeadmin</b>\n'
  response+='Downgrade your access to admin level\n\n'
  
  
  bot.send_message(message.chat.id, response, parse_mode='html')









bot.polling(none_stop = True)


# while True: #Continuously checks for messages 
#   try:
#     bot.polling(none_stop = True)
#   except Exception as e:
#     print("ERROR!!!!", e)
#     time.sleep(15)




#LOokup for symbols: https://finance.yahoo.com/lookup/









# #Getting the prices of AAPl 
# aapl_df = yf.download('AAPL', start='2020-01-01', end='2021-06-12', progress=False,)
# aapl_df.reset_index(inplace = True)

#Showing the plot of AAPL 
# plt.figure(figsize=(8,6))
# plt.plot(aapl_df['Date'], aapl_df['Open'])
# plt.title('AAPL STOCK')
# plt.show()












#FOR THE PLOTLY GRAPH USING THE DASH
# fig = px.line(aapl_df, x='Date', y='Open', title='HI', width=100, height=200)
# app = dash.Dash(__name__)

# app.layout = html.Div([
#     dcc.Graph(id="line-chart", figure=fig),
# ])
# app.run_server(debug=True)

# plt.figure(figsize=(2,2))
# plt.plot(aapl_df['Date'], aapl_df['Open'])
# plt.show()

