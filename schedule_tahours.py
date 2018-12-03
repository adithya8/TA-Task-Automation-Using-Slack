import datetime
import sf_bot
import pandas as pd
import google_api
from sf_bot import send_dm
bot = sf_bot.bot
flag = 0

global res, gen, d


def get_poll_data():
    # get the  poll data list
    poll_dic = dict()
    count = 1
    for msg in bot.groups.history(channel=sf_bot.sf_ta).body['messages']:
        if msg.get('attachments') != None:
            dic = dict(msg['attachments'][0])
            if "title" in dic and "Avail" in dic["title"]:
                votes = msg["attachments"][0]["fields"]
                for v in votes:
                    # forming the poll dic
                    poll_dic[count] = v["value"].split(
                        "\n")[1].strip().split(",")
                    for i in range(len(poll_dic[count])):
                        poll_dic[count][i] = str(poll_dic[count][i].strip())
                    count += 1
                break
    # get count of ta days for each ta
    ta_days_count = dict()
    for d in poll_dic:
        for ta in poll_dic[d]:
            ta_days_count[ta] = 1 if ta not in ta_days_count else ta_days_count[ta] + 1
    del ta_days_count['']

    # sorted days for which ta is available
    ta_day_list = []
    for days in ta_days_count:
        ta_day_list.append([days, ta_days_count[days]])
    ta_day_list = (ta_day_list[::-1])
    ta_day_list = sorted(ta_day_list, key=lambda x: x[1])

    return poll_dic, ta_day_list


def assign_slots(ta_day_list, poll_dic):
    # get tas available for one day
    one_day_available_ta = [tdl[0] for tdl in ta_day_list if tdl[1] <= 1]
    print (one_day_available_ta)

    # creating a assigned slot dict
    assigned = {}
    for i in range(1, 11):
        assigned[i] = []

    # assign tas with 1 day availablity first
    for k in poll_dic:
        for e in poll_dic[k]:
            if e in one_day_available_ta:
                assigned[k].append(e)
    print(assigned)
    print()

    # assigning the remaining slots to other tas
    for k in poll_dic:
        if not poll_dic[k]:
            assigned[k][0] = "No TA Hours"
        elif len(poll_dic[k]) == 1 and poll_dic[k][0] in one_day_available_ta:
            continue
        elif len(poll_dic[k]) == 1 and poll_dic[k][0] not in one_day_available_ta:
            assigned[k].append(poll_dic[k][0])
        elif (len(poll_dic[k]) >= 2):
            if(len(assigned[k]) == 0):
                assigned[k].append(poll_dic[k][0])
                assigned[k].append(poll_dic[k][1])
            elif(len(assigned[k]) == 1):
                for u in poll_dic[k]:
                    if(u not in one_day_available_ta):
                        assigned[k].append(u)

    return assigned


def generate_msg(sx, ex, assigned, user_df):

    res = "*TA Hours of the Week : " + \
        str(sx.date()) + " - " + str(ex.date()) + "*\n"
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday Slot 1 (10:00-12:00)", "Saturday Slot 2 (14:00-16:00)", "Saturday Slot 3 (18:00-20:00)", "Sunday Slot 1(10:00-12:00)", "Sunday Slot 2 (16:00-18:00)"]
    gen = "*TA Hours of the Week " + \
        str(sx.date()) + " - " + str(ex.date()) + "*\n"
    for k in assigned.keys():
        if assigned[k] == ['']:
            res += days[k - 1] + " : No TA hours"
            gen += days[k - 1] + " : No TA hours"
        else:
            gen += days[k - 1] + " : 6 PM to 8 PM" if k <= 5 else days[k - 1]
            l = assigned[k]
            # l=[x[2:-1] for x in l]
            # print (l)
            if(len(l) <= 1):
                res += days[k - 1] + " : " + l[0]
            elif(len(l) >= 2):
                text = ""
                for i in range(len(l)):
                    if(i >= 2):
                        break
                    text += l[i] + ","
                res += days[k - 1] + " : " + text[:-1]
        res += "\n"
        gen += "\n"

    # Writing to a file - think of it as a log file of sorts
    f = open('log/ta_reipcord.txt', 'a')
    f.writelines(res)
    f.close()

    return res


def create_event(sx, ex, assigned, user_df):
    service = google_api.get_service('calendar', 'v3')
    start_times = ["T18:00:00", "T10:00:00", "T14:00:00",
                   "T18:00:00", "T10:00:00", "T16:00:00"]
    end_times = ["T20:00:00", "T12:00:00", "T16:00:00",
                 "T20:00:00", "T12:00:00", "T18:00:00"]
    thing = None
    dates_ = pd.date_range(start=sx, end=ex)
    print(dates_)
    dates = []
    for i in range(len(dates_)):
        if i < 5:
            dates.append(str(dates_[i].date()))
        if i == 5:
            dates.append(str(dates_[i].date()))
            dates.append(str(dates_[i].date()))
            dates.append(str(dates_[i].date()))
        if i == 6:
            dates.append(str(dates_[i].date()))
            dates.append(str(dates_[i].date()))
    print(dates)
    for i in range(10):
        print (assigned[i + 1])
        if assigned[i + 1] == [""]:
            continue
        if i < 5:
            thing = 0
        elif i >= 5:
            thing = i - 4
        emails = []
        user_df.columns = user_df.T['id']
        for ix in assigned[i + 1]:
            user_id = ix[2:-1]
            emails.append({"email": user_df[user_id]['email']})
        print (i, start_times[thing], end_times[thing], emails)
        event = {
            "summary": "TA hours",
            "location": "Solarillion Foundation",
            "start": {"dateTime": dates[i] + start_times[thing], "timeZone": "Asia/Kolkata", },
            "end": {"dateTime": dates[i] + end_times[thing], "timeZone": "Asia/Kolkata"},
            "attendees": emails,
            "remainders": {'useDefault': False,
                           'overrides': [
                               {'method': 'popup', 'minutes': 180},
                               {'method': 'popup', 'minutes': 24 * 60}]}
        }
        print ('Gonna create events!')
        event_ = service.events().insert(calendarId="primary", body=event).execute()
        print ("Event created " + event_.get('htmlLink'))


def schedule_ta(post_it=False):
    poll_dic, ta_day_list = get_poll_data()
    # get user_data
    user_df = sf_bot.get_userdf()
    user_df.index = user_df['name']
    del user_df['name']
    user_df = user_df.T

    # asign slots
    assigned = assign_slots(ta_day_list, poll_dic)

    # sx,ex
    sd = pd.to_datetime('today')
    sx, ex = None, None

    if sd.dayofweek == 0:
        sx = pd.to_datetime(sd.date())
        ex = pd.to_datetime(sx + pd.Timedelta("144:00:00"))

    elif sd.dayofweek == 6:
        sx = pd.to_datetime(sd.date() + pd.Timedelta("24:00:00"))
        ex = pd.to_datetime(sx + pd.Timedelta("144:00:00"))

    elif sd.dayofweek == 1:
        sx = pd.to_datetime(sd.date() - pd.Timedelta("48:00:00"))
        ex = pd.to_datetime(sx + pd.Timedelta("144:00:00"))

    else:
        sx = pd.to_datetime(sd.date())
        days_to_sunday = (6 - sx.dayofweek - 1) * 7
        ex = pd.to_datetime(sx + pd.Timedelta(str(days_to_sunday) + ':00:00'))

    # generate message
    res = generate_msg(sx, ex, assigned, user_df)

    if post_it:
    
        sf_bot.post_message(res, "sf_ta")
        sf_bot.post_message(res, "general")
    # send_dm('ateexd',res)

    # google calendar event
    create_event(sx, ex, assigned, user_df)
    print(res)
    return res + '\n\n\n\n'


if __name__ == "__main__":
    schedule_ta()
