from ..constants import (GOOGLE_CALENDAR_AUTHORIZATION_URI,
                         GOOGLE_CALENDAR_CLIENT_ID,
                         GOOGLE_CALENDAR_CLIENT_SECRET,
                         GOOGLE_CALENDAR_REDIRECT_URI, GOOGLE_CALENDAR_SCOPE,
                         GOOGLE_CALENDAR_TOKEN_URI,
                         GOOGLE_CALENDAR_WRAPPER_STR)
from ..sessions.oauth2 import Session

oauth2 = Session(client_id=GOOGLE_CALENDAR_CLIENT_ID,
                 client_secret=GOOGLE_CALENDAR_CLIENT_SECRET,
                 redirect_uri=GOOGLE_CALENDAR_REDIRECT_URI,
                 token_uri=GOOGLE_CALENDAR_TOKEN_URI,
                 authorization_uri=GOOGLE_CALENDAR_AUTHORIZATION_URI,
                 scope=GOOGLE_CALENDAR_SCOPE,
                 state=GOOGLE_CALENDAR_WRAPPER_STR,
                 component='Google Calendar')


def get_events(calendar_id='primary')-> dict:
    """
    Return a list of events
    """
    res_json = oauth2.get(
        f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events').json()
    res = res_json['items']
    return res
