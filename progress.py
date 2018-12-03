from datetime import timedelta
import pandas as pd
import pickle
import sf_bot
import math
from datetime import datetime

"""returns a pandas dataframe after parsing the dates"""


def parse_df_dates(df):
    for c in df.columns:
        df[c] = pd.to_datetime(df[c], infer_datetime_format=True)
    return df


"""Returns the currently working assignment pandas series with last completed as input"""


def get_currently_working(df):
    # gets the index of the dataframe with highest date
    temp = df.idxmax(axis=1)
    current = pd.Series()
    cols = list(df.columns)
    to_drop = []
    for t in temp.index:
        # skip if the student has completed the orientation
        if temp[t] == 'R3':
            to_drop.append(t)
            continue
        # At least one assignment was verfied
        if not pd.isnull(temp[t]):
            nxt = cols.index(temp[t]) + 1
            # if nxt<len(cols):
            current[t] = cols[nxt]
            # else:
            #     current[t]=cols[nxt-1]
        # no assingment verified
        else:
            current[t] = 'A1-a'
    return current, to_drop


"""Returns the last completed assignment pandas series with last completed as input"""


def last_completed(completed):
    # get last completed date
    completed = completed.T
    temp = completed.max(axis=0)
    temp = temp - datetime.now()

    # impossible case used as flag for no work completed
    temp.fillna(value=timedelta(days=7), inplace=True)
    last = pd.Series()
    for t in temp.index:
        # to weeks
        last[t] = int(temp[t].days / 7)
    return last


"""Computes the status by subracting doj and today"""


def compute_status(doj, curr):
    days_per_assignment = 7
    stat = pd.Series(dtype=timedelta)
    # date after joining for each student
    days_elapsed = datetime.now() - doj
    # print(curr)
    for i in days_elapsed.index:
        # check the currently working assignment
        if 'A' in curr[i]:
            assignment = int(curr[i][1])
        elif curr[i][0] == 'M' or curr[i][0] == 'R':
            assignment = 7
        else:
            assignment = 8
        # if in assingments
        if assignment < 7:
            stat[i] = days_elapsed[i] - \
                timedelta(days=days_per_assignment * assignment)
        # else if in motor project
        elif assignment == 7:
            # buffer period of 45 days for completion
            stat[i] = timedelta(days=-7) if days_elapsed[i] < timedelta(days=days_per_assignment *
                                                                        6 + 45) else days_elapsed[i] - timedelta(days=days_per_assignment * 6 + 45)
    return stat

# draft a slack messsage


def create_message(status, current, o_data, user_df, last):
    work_dict = {
        'A1-a': 'Assignment 1a', 'A1-b': 'Assignment 1b', 'A2-a': 'Assignment 2-a', 'A2-b': 'Assignment 2-b', 'A3-a': 'Assignment 3-a', 'A3-b': 'Assignment 3-b', 'A4-a': 'Assignment 4-a', 'A4-b': 'Assignment 4-b', 'A5-a': 'Assignment 5-a', 'A5-b': 'Assignment 5-b', 'A6-a': 'Assignment 6-a', 'A6-b': 'Assignment 6-b', 'M1': 'Project module 1', 'M2': 'Project module 2', 'M3': 'Project module 3', 'R1': 'Review 1', 'R2': 'Review 2', 'R3': 'Review 3'
    }
    global msg

    msg = '_*Weekly Performance Update:*_\n+ => Lead and - => Lag'
    for i in status.index:
        # remove i
        msg += '\n*' + user_df.loc[i]['full_name'] + \
            " (<@" + user_df.loc[i]['id'] + ">)" + \
               "*:\n In " + work_dict[str(current[i])]
        if o_data.loc[i]['Track'] != 2:
            # convert the days into weeks (and rounding it off)
            weeks = math.ceil(int(str(status[i]).split(' ')[0]) / 7 + 1)
            weeks = '-' + str(weeks) if weeks > 0 else '+' + str(abs(weeks))
            if weeks != '+0':
                msg += ": _" + weeks + " Week(s)_"
            else:
                msg += ": on track"
        msg += '\n'
        # impossible flag i.e. not yet started
        if last[i] == 1:
            msg += 'No work completed yet'
        elif last[i] == 0:
            msg += 'Last work completed this week'
        else:
            msg += 'Last work completed before %d week(s) ' % abs(last[i])
    return msg


'''
    Returns Parsed spreadsheet data
    Arguments: None
    Returns:
    o_data-> A pandas dataframe consisting of students D.o.J and their o_data
    completed -> A pandas dataframe consting of dates when the assignments were completed
'''


def get_progress():
    '''    
        # usernames,duration,post_it=arg_parser.get_parsed_arguments()
        # print(usernames,duration,post_it)
    '''
    o_data = pd.read_csv(
        'orientation/orientation_data.csv', sep=',', index_col=0)
    o_data['doj'] = pd.to_datetime(o_data['doj'], infer_datetime_format=True)

    completed = parse_df_dates(pd.read_csv(
        'orientation/completed.csv', sep=',', index_col=0))

    # get D.o.J which is the date when the first assignment was sent
    doj = o_data['doj']
    # print(doj)
    # get current work
    current, to_drop = get_currently_working(df=completed)
    # get last completed
    last = last_completed(completed)

    # drop if completed orientation only from doj,o_data,last,completed
    completed.drop(to_drop, inplace=True), doj.drop(to_drop, inplace=True)
    o_data.drop(to_drop, inplace=True), last.drop(to_drop, inplace=True)
    # save them if anything was dropped
    if to_drop != []:
        # print('Updating the data (SCT)')
        completed.to_csv('orientation/completed.csv', sep=',')
        o_data.to_csv('orientation/orientation_data.csv', sep=',')

    # calculate expected dates
    status = compute_status(doj, current)
    # print('Status is:\n {}'.format(status))
    # making slack user_name the primary key
    user_df = sf_bot.get_userdf()
    user_df.index = user_df['name']
    del user_df['name']

    # drafting a message to be posted on the slack
    msg = create_message(status, current, o_data, user_df, last)
    print('Message is %s' % msg)
    # #post to aashish
    # sf_bot.bot.chat.post_message('U39BM0PCN',msg,as_user=True)
    # post to sf_ta
    sf_bot.post_message(msg, "sf_ta")
    return msg


if __name__ == "__main__":
    get_progress()
