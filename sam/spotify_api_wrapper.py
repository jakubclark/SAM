import json

from . import spotify_oauth2_session
from .constants import NOT_IMPLEMENTED

valid_types = ['artist', 'album', 'track', 'playlist']


def current_playback_state():
    """
    Get information about the user's current playback state, including track, track progress and active device'
    """
    res = spotify_oauth2_session.get('https://api.spotify.com/v1/me/player')
    return res


def currently_playing():
    """
    Get the currently playing information

    :returns: requests.Response
    """
    res = spotify_oauth2_session.get('https://api.spotify.com/v1/me/player/currently-playing')
    return res


def current_volume():
    """
    Get the user's current volume_percent
    """
    return current_playback_state().json()['device']['volume_percent']


def current_device():
    """
    Get the user's current information
    """
    return current_playback_state().json()['device']


@property
def oauth2_session():
    return spotify_oauth2_session


def login():
    """
    Generate an authorization url to authorize your app to connect to the Spotify API,
    and access user resources, and return the authorization url
    """
    authorization_url, state = spotify_oauth2_session.authorization_url()
    return authorization_url


def callback(callback_url):
    """
    Fetch an access token, based on the callback_url

    :param callback_url: The callback url returned by the Spotify API,
                         after the user authorized (or denied) access to their account
    """
    spotify_oauth2_session.fetch_token(callback_url)


def token_info():
    """
    Return current token info for the OAuth2Session
    """
    res = spotify_oauth2_session.oauth2_session.token
    return res


def get_uri(input_, type_='track'):
    payload = {
        'q': input_,
        'type': type_
    }
    res = spotify_oauth2_session.get('https://api.spotify.com/v1/search', params=payload)
    return res


def skip_forward():
    """
    Skip the currently playing song
    """
    res = spotify_oauth2_session.post('https://api.spotify.com/v1/me/player/next')
    return res


def play(value, type_='artist', device: "str, dict"=None):
    """
    Attempt to play the specified value, based on type_
    :param value: The value to search for and ultimately play (song name, artist name, album name, playlist name)
    :param type_: (song, artist, album, playlist)
    :param device: The device to play one - device_name or device_dict

    :returns: requests.Response
    """
    if type_ not in valid_types:
        raise ValueError('invalid type_ value passed. Valid types: "song", "album", "track", "playlist"')

    json_data = get_uri(value, type_).json()

    if device is None:
        # Play on the currently active device
        if type_ == 'artist':
            uri = json_data['artists']['items'][0]['uri']
        elif type_ == 'album':
            uri = json_data['albums']['items'][0]['uri']
        elif type_ == 'track':
            uri = json_data['tracks']['items'][0]['uri']
        elif type_ == 'playlist':
            uri = json_data['playlist']['items'][0]['uri']
    else:
        # Play on a specific device
        return NOT_IMPLEMENTED

    if type_ == 'track':
        # Play a track
        data = json.dumps({'uris': [uri]})
        res = spotify_oauth2_session.put('https://api.spotify.com/v1/me/player/play', data=data)
    else:
        # Play an artist/album/playlist
        data = json.dumps({'context_uri': uri})
        res = spotify_oauth2_session.put('https://api.spotify.com/v1/me/player/play', data=data)
    return res


def set_volume(volume_percent: int=50, device_id: str=None):
    """
    Set the user's volume_percent
    :param volume_percent: The desired volume level
    :param device_id: The id of the device for which the volume is being changed/set
    :returns: requests.Response
    """
    params = {
        'volume_percent': volume_percent
    }
    if device_id:
        params['device_id'] = device_id
    res = spotify_oauth2_session.put('https://api.spotify.com/v1/me/player/volume', params=params)
    return res
