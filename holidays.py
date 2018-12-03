import datetime
import pandas as pd
import google_api


def getHolidays():
    service = google_api.get_service('calendar', 'v3')
    now = (pd.to_datetime(datetime.datetime.utcnow()) + 
    datetime.timedelta(days=2, hours=5, minutes=30))
    later = (now + datetime.timedelta(days=6, hours=5, minutes=30))

#    print (now.date().isoformat(), later.date().isoformat())
    now = now.isoformat() + 'Z'
    later = later.isoformat() + 'Z'
#    print('Getting the upcoming 10 events')
    calendarId = 'en.indian#holiday@group.v.calendar.google.com'
    events_result = service.events().list(calendarId=calendarId, timeMin=now,timeMax=later, 
    singleEvents=True,orderBy='startTime').execute()
    events = events_result.get('items', [])
    holidays = [5,6]
    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
#        print(start, event['summary'], pd.to_datetime(start).dayofweek)
        if (pd.to_datetime(start).dayofweek not in holidays):
            holidays.append(pd.to_datetime(start).dayofweek)  

    return sorted(holidays)