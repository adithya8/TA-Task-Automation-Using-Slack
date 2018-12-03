import pandas as pd
"""
    Returns a pandas dataframe containing userdata
"""
def get_userlist(only_names=False):
    #read user list and getting orientation_students from the user_list
    user_list=pd.read_csv('data/user_db.csv',index_col=0)
    user_list.index=[i.lower() for i in user_list.index]
    if not only_names:
        return user_list
    else:
        return list('@'+user_list['name'])
