import json
import logging
from copy import deepcopy
from datetime import datetime

from dateutil import parser as date_parser

from ..exceptions import InvalidDataFormatError

from ..constants import (DARK_SKY_KEY, DARK_SKY_URL, GOOGLE_MAPS_GEOCODE_KEY,
                         GOOGLE_MAPS_GEOCODE_URL, GOOGLE_MAPS_TIMEZONE_KEY,
                         GOOGLE_MAPS_TIMEZONE_URL, WEATHER_PARAMETERS)
from ..sessions.web import WebSession

log = logging.getLogger(__name__)

web = WebSession()


def generate_darksky_url(coordinates):
    # type: (dict) -> str
    """
    Generate a dark_sky url with lat and lng

    :param coordinates: dict containing the lat and lng keys (and their respective values)
    :return: The generated dark_sky url, with lat and lng properly formatted and positioned
    """
    lat = coordinates['lat']
    lng = coordinates['lng']
    url = f'{DARK_SKY_URL}{DARK_SKY_KEY}/{lat},{lng}'
    return url


def get_coordinates(location):
    # type: (str) -> dict
    """
    Returns a dict (json), with the coordinates for specified location

    :param location: the location for which coordinates are to be parsed
    :returns: dict that contains lat and lng
    """
    location = location.replace(' ', '+')
    params = {
        'address': location,
        'key': GOOGLE_MAPS_GEOCODE_KEY
    }
    json_data = web.get_json(GOOGLE_MAPS_GEOCODE_URL, params=params)
    coordinates = json_data['results'][0]['geometry']['location']
    coordinates['lng'] = round(coordinates['lng'], 7)
    coordinates['lat'] = round(coordinates['lat'], 7)
    return coordinates


def get_datetime_from_string(datetime_str):
    # type: (str) -> datetime
    """
    Given a str, generate equivalent datetime object

    :param datetime_str: string representation of time
    :return: the corresponding datetime object
    """
    datetime_object = date_parser.parse(datetime_str)
    return datetime_object


def get_offset_from_utc(coordinates):
    # type: (dict) -> int
    """
    Calculate the offset coordinates has from utc

    :param coordinates: dict containing the lat and lng keys (and their respective values)
    :return: the offset, in seconds, that coordinates has from utc time
    """

    current_epoch_time = datetime.utcnow().timestamp()
    lat = coordinates['lat']
    lng = coordinates['lng']
    location_param = f'{lat},{lng}'

    params = {'key': GOOGLE_MAPS_TIMEZONE_KEY,
              'location': location_param,
              'timestamp': current_epoch_time}

    json_data = web.get_json(GOOGLE_MAPS_TIMEZONE_URL, params=params)
    return json_data['dstOffset'] + json_data['rawOffset']


def get_weather_data(coordinates, include=None):
    # type: (dict, Optional(list[str])) -> dict
    """
    Returns a dict (json), with weather data for the specified coordinates.
    If include is specified, only that data is retrieved.
    Otherwise, all data is retrieved.

    :param coordinates: dict containing the lat and lng keys (and their respective values)
    :param include: Optional list of json data to include
    :returns: a dict (json) with (the specified) data
    """
    url = generate_darksky_url(coordinates)
    params = {'units': 'si'}
    if include is not None:
        weather_parameters = deepcopy(WEATHER_PARAMETERS)
        for param in include:
            weather_parameters.remove(param)
        params['exclude'] = ','.join(weather_parameters)
    return web.get_json(url, params=params)


def generate_summary(json_data, index=None):
    if index is not None:
        summary = json_data[index]['summary']
        temperature = json_data[index]['apparentTemperature']
    else:
        summary = json_data['summary']
        temperature = (json_data['apparentTemperatureMax'] + json_data['apparentTemperatureMin']) / 2
    result = f'{summary} with a temperature of {str(round(temperature, 2))} degrees celsius'
    return result


def get_weather_summary_current(coordinates):
    # type: (dict) -> str
    """
    Returns current weather summary

    :param coordinates: dict containing the lat and lng keys (and their respective values)
    :returns: a str summary  of the current weather located at coordinates
    """
    json_data = get_weather_data(coordinates, include=['currently'])
    result = generate_summary(json_data, 'currently')
    return result


def get_weather_summary_no_datetime(coordinates):
    # type: (dict) -> str
    """
    Returns weather summary for the next few hours

    :param coordinates: dict containing the lat and lng keys (and their respective values)
    :returns: a str summary  of the upcoming weather (next few hours) located at coordinates
    """
    json_data = get_weather_data(coordinates, include=['currently'])
    result = generate_summary(json_data, 'currently')
    return result


def get_weather_summary_for_hour(datetime_, coordinates):
    # type: (dict) -> str
    """
    Returns weather summary for the specific hour

    :param datetime_: The specific hour to get weather summary for
    :type datetime_: datetime_
    :param coordinates: The coordinates to get weather summary for
    :returns: a str summary  of the upcoming weather at the specified hour located at coordinates
    """
    timestamp = datetime_.timestamp()

    json_data = get_weather_data(coordinates, include=['hourly'])
    for entry in json_data['hourly']['data']:
        if entry['time'] == timestamp:
            summary = entry['summary']
            apparent_temperature = entry['apparentTemperature']
            res = f'{summary} with a temperature of {str(int(round(apparent_temperature)))} degrees Celsius.'
            return res


def get_weather_summary_for_day(datetime_: datetime, coordinates: str) -> str:
    """
    Returns weather summary for the entire day

    :param datetime_: The specific day to get weather summary for
    :type datetime_: datetime
    :param coordinates: dict containing the lat and lng keys (and their respective values)
    :returns: a str summary of the weather on the specified day located at coordinates
    """

    if datetime_.timestamp() < datetime.utcnow().timestamp():
        raise InvalidDataFormatError(f'{datetime_.isoformat()} is in the past')
    new_datetime = datetime(
        datetime_.year,
        datetime_.month,
        datetime_.day

    )
    timestamp = new_datetime.timestamp()
    json_data = get_weather_data(coordinates, include=['daily'])

    for entry in json_data['daily']['data']:
        try:
            if entry['time'] == timestamp:
                summary = generate_summary(entry)
                return summary
        except IndexError:
            return 'weather.get_weather_for_day()_1'


def get_weather_summary_for_time_period(datetime_, coordinates):
    # type: (datetime, dict) -> str
    """
    Return weather summary for a a time period (around 4 hours)

    :param datetime_: The time to get weather summary for
    :param coordinates: dict containing the lat and lng keys (and their respective values)
    :returns: a str summary of the weather for the specified datetime_ located at coordinates
    """
    timestamp = datetime_.timestamp()
    json_data = get_weather_data(coordinates, include=['hourly'])
    for entry in json_data['hourly']['data']:
        if entry['time'] == timestamp:
            summary = entry['summary']
            apparent_temperature = entry['apparentTemperature']
            res = f'{summary} with a temperature of {apparent_temperature} degreese Celsius.'
            return res


def weather_action(query_result: dict):
    """
    Perform a weather action
    query_result_example = {
      "action": "weather.weather",
      "parameters": {
        "location": "Amsterdam",
        "date-time": "2018-09-04T12:00:00+02:00"
      }
    }
    """
    if 'queryResult' in query_result:
        query_result = query_result['queryResult']

    parameters = query_result.get('parameters')
    action = query_result.get('action')

    if action.endswith('followup'):
        specific_action = action.split('.')[1]
        output_contexts = query_result.get('outputContexts')
        if specific_action == 'location':
            # Have to get date-time from previous request
            date_time = output_contexts[0]['parameters']['date-time']
            location = parameters.get('location')
        elif specific_action == 'time':
            # Have to get location from previous request
            location = output_contexts[0]['parameters']['location']
            date_time = parameters.get('date-time', None)

    else:
        date_time = parameters.get('date-time', None)
        location = parameters.get('location', None)

    if isinstance(location, dict):
        location = location['city']
    coordinates = get_coordinates(location)

    if date_time:
        # Get weather for specific datetime (day and hour)
        if isinstance(date_time, dict):
            # Assume that the request is for a period of time, with a start and end
            # We simply take the point in time that is between the start and end,
            # and return the weather for that time
            start_hour = date_parser.parse(date_time['startDateTime']).hour
            end_hour = date_parser.parse(date_time['endDateTime']).hour

            average_hour_int = int((start_hour + end_hour) / 2)

            if average_hour_int < 0 or average_hour_int > 24:
                return "Error, average_hour has been calculated as invalid"
            if average_hour_int <= 9:
                average_hour_str = f'0{average_hour_int}'
            else:
                average_hour_str = average_hour_int

            first_part = date_time['startDateTime'][:11]
            second_part = str(average_hour_str)
            third_part = date_time['startDateTime'][13:]
            average_hour_str = f'{first_part}{second_part}{third_part}'

            datetime_object = date_parser.parse(average_hour_str)

            res = get_weather_summary_for_time_period(datetime_object, coordinates)

        else:
            datetime_object: datetime = date_parser.parse(date_time)

            if len(date_time) == 25:
                now_timestamp = datetime.utcnow().timestamp()
                datetime_object_timestamp = datetime_object.timestamp()
                if datetime_object_timestamp - 60.0 <= now_timestamp <= datetime_object_timestamp + 60.0:
                    # Get current weather
                    res = get_weather_summary_current(coordinates)
                else:
                    res = get_weather_summary_for_day(datetime_object, coordinates)

            else:
                raise InvalidDataFormatError(f'The given datetime format is invalid: {datetime_}')

    else:
        # Assume that the weather is for the current time
        res = get_weather_summary_current(coordinates)
        datetime_object = datetime.utcnow()

    coordinates_str = json.dumps(coordinates)
    log.debug(f'Returning weather information for the following:\n'
              f'date: {str(datetime_object)}\n'
              f'coordinates: {coordinates_str}')
    if res:
        return res
    else:
        return f'Specified date-time is invalid: {date_time}'
        # raise InvalidDataFormat(f'Specified date-time is invalid: {date_time}')
