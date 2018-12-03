from slacker import Slacker
import pandas as pd
import numpy as np
import pickle
import warnings
warnings.filterwarnings("ignore")
from holidays import *


adi = '<Slack token here>'
server = Slacker('<Slack token here>')
bot, adi = Slacker(
    '<bot API here>'),  Slacker(adi) 
sf_ta = '<channel id>'
general = '<channel id>'
ta_group = '<channel id>'


def retrieve_last_messages(channel, count=5):
    return bot.groups.history(channel).body['messages'][0:count]


def post_message(msg, channel_name, ch_id=''):
    # TODO ch_id csv for getting channel id of a given channel
    # check line below
    bot.chat.post_message('#' + channel_name, msg, as_user=True)
    # bot.chat.update(channel=sf_ta,ts=1503913930.000061,text=msg)
    # pass


def get_slotDf(holidays):
    slots = [" 10:00-12:00"," 14:00-16:00"," 18:00-20:00"]
    days = {0:"Mon",1:"Tues",2:"Wed",3:"Thurs",4:"Fri",5:"Sat",6:"Sun"}
    slotStrings = []
    
    for i in days:
        if(i in holidays):
            for slot in slots:
                temp = []
                temp.append(days[i])
                temp.append(slot)
                slotStrings.append(temp)
        else:
            slotStrings.append([days[i],slots[-1]])
        
    slotStrings = pd.DataFrame(slotStrings,columns = ['Day','Time'])

    return slotStrings

def post_poll():
    defaultText = '"TA Availabilities" "Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday 10:00-12:00" "Saturday 14:00-16:00" "Saturday 18:00-20:00" "Sunday 10:00-12:00" "Sunday 16:00-18:00"'
    defaultHolidays = [0,1,2,3,4,5,6]
    #holidays = getHolidays()
    slots = [" 10:00-12:00"," 14:00-16:00"," 18:00-20:00"]
    days = {0:"Mon",1:"Tues",2:"Wed",3:"Thurs",4:"Fri",5:"Sat",6:"Sun"}
    slotStrings = get_slotDf(holidays=defaultHolidays)

    if( len(slotStrings) == 21 ):
        slotStrings = slotStrings[((slotStrings.Day != "Sunday") & (slotStrings.Time != slots[0]))]

    if ( len(slotStrings) > 10):
        poll1_length = int(len(slotStrings)/2)
        poll1_df = slotStrings.iloc[0:poll1_length]
        poll2_df = slotStrings.iloc[poll1_length: len(slotStrings)]

        poll1_string = '\"TA Availabilities-1\" '
        poll2_string = '\"TA Availabilities-2\" ' 
        
        poll1_df['combined'] = poll1_df['Day'] + poll1_df['Time'] 
        poll2_df['combined'] = poll2_df['Day'] + poll2_df['Time']  
        
        for i in poll1_df.combined :
            poll1_string += '\"'+ i+'\"' + " "
        for i in poll2_df.combined:
            poll2_string += '\"'+ i+'\"' + " "
        
        print (poll1_string)
        print ("\n\n\n")
        print (poll2_string)

        server.chat.command(channel=ta_group, command="/poll",text=poll1_string)
        server.chat.command(channel=ta_group, command="/poll",text=poll2_string)

    else:
        server.chat.command(channel=ta_group, command="/poll",text=defaultText)
    
    


'''
 def get_details_of_user(user):
     res=bot.users.list()
     for user_details in res.body.get('members'):
         if user_details['name'] :
             print(user_details['id'],user_details['name'],user_details['profile']['email'],user_details['real_name'])
'''


def get_userdf(only_names=False):
    # read user list and getting orientation_students from the user_list
    user_df = pickle.load(open('data/user_db.p', 'rb'))
    # user_list.index=[i.lower() for i in user_list.index]
    if not only_names:
        return user_df
    else:
        return list('@' + user_df['name'])


def update_users():
    members = bot.users.list().body['members']
    user_df = pd.DataFrame()
    count = 0
    for m in members:
        first_name, last_name, email, phone = '', '', '', ''
        phone = ''
        try:
            first_name = m['profile']['first_name']
        except:
            pass
        try:
            last_name = m['profile']['last_name']
        except:
            pass
        try:
            email = m['profile']['email']
        except:
            pass
        name = first_name + ' ' + last_name
        user_df[count] = [m['id'], m['name'], email, name]
        count += 1
    user_df = user_df.T
    user_df.columns = ['id', 'name', 'email', 'full_name']
    pickle.dump(user_df, open('data/user_db.p', 'wb'))


def update_channels():
    channels = bot.channels.list().body['channels']
    channels_df = pd.DataFrame()
    count = 0
    for c in channels:
        channels_df[count] = [c['id'], c['name']]
        count += 1
    channels_df = channels_df.T
    channels_df.columns = ['id', 'name']
    pickle.dump(channels_df, open('data/channel_db.p', 'wb'))


def update_tas():
    tas = bot.groups.info(sf_ta).body['group']['members']
    tas = pd.DataFrame(tas)
    tas.columns = ['id']
    pickle.dump(tas, open('data/tas.p', 'wb'))


def send_dm(user, message):
    if user in ('vineethv', 'aashish_jain', 'ateexd'):
        return 'Can\'t send'
    user_df = pickle.load(open('data/user_db.p', 'rb'))
    user_df.index = user_df['name']
    user_df = user_df.T
    user_id = user_df[user]['id']
    dm_channel_id = bot.im.open(user_id).body["channel"]['id']
    bot.chat.post_message(dm_channel_id, message, as_user=True)
    return 'Sent'


def post_question(ques, user):
    # Month Dictionary
    monthDict = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul',
                 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

    # Loading question from Pickle Files
    questions = pickle.load(open('data/questions.p', 'rb'))
    if ques not in questions.keys():
        return False

    # Generate the date of deadline
    hours = 24 * 7
    if ques == 'M':
        hours = 24 * 31

    date_to_submit = pd.to_datetime(
        pd.datetime.now() + pd.Timedelta(str(hours) + ':00:00'))
    date_to_submit = date_to_submit.date()
    d, m, y = date_to_submit.day, date_to_submit.month, date_to_submit.year

    # Post to the student
    m = "\nYou have time until "\
        + str(d) + " " + str(monthDict[m]) + ", " + str(y)\
        + " to complete it. If any doubts, please contact the TA's."
    msg = "*" + str(ques) + '*\n' + questions[ques] + m

    send_dm(user, msg)


def is_ta(id):
    tas = pickle.load(open('data/tas.p', 'rb'))
    ta_flag = False
    if id in list(tas['id']):
        ta_flag = True
    return ta_flag


def update_data():
    print('Updating slack data')
    update_channels()
    update_users()
    update_tas()
    print('Update completed')


def print_data():
    print(pickle.load((open('data/channel_db.p', 'rb'))))
    print(pickle.load((open('data/user_db.p', 'rb'))))
    print(pickle.load((open('data/tas.p', 'rb'))))
