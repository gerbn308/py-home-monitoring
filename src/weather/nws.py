import datetime, json, requests
from datetime import datetime, timedelta
import os, pytz, re
from weather_base import *
import json

ABBREVIATING = {
    'Northeast': 'NE',
    'Northwest': 'NW',
    'Southeast': 'S',
    'Southeast': 'SE',
    'Southwest': 'SW',
    'East': 'E',
    'North': 'N',
    'South': 'S',
    'West': 'W',
    'West': 'W',
    'an inch possible': 'an inch',
    'New snow accumulation of': 'New snow',
    ' around ': ' of ',
    ' near ': ' of ',
    'gusts as high as': ' gusts of',
    'less than': '<',
    'rain and snow': 'rain & snow',
    'sleet and rain': 'sleet & rain',
}


class NWS( Weather ):
    # This will default to Centre County, PA, USA if you don't define the environment variable
    regionId = os.environ['nws_region'] if 'nws_region' in os.environ else 'PAC027'

    # Some counties are split into smaller segments, this lets you pick the region(s) you want to get
    regionIds = json.loads(os.environ['nws_regions']) if 'nws_region' in os.environ else [ 'PAZ019', 'PAZ045' ]


    def get_headers( self ):
        return {
            "User-Agent": f"({self.appName}, {self.contact})"
        }


    def get_alerts( self ):
        url = f"https://api.weather.gov/alerts/active/zone/{self.regionId}"
        response = requests.get( url, headers=self.get_headers() )
        raw = json.loads(response.text)

        alerts = []
        for feature in raw['features']:
            isAnExpectedRegion = False
            for attr in ['geocode']:  #, 'references', 'parameters'
                if "UGC" in feature['properties'][attr]:
                    for code in feature['properties'][attr]["UGC"]:
                        if code in self.regionIds:
                            isAnExpectedRegion = True
                            break
                if attr in feature['properties']:
                    del feature['properties'][attr]
            if isAnExpectedRegion is False:
                continue
            # print(feature['properties'])
            if 'VTEC' in feature['properties']['parameters']:
                chunks = feature['properties']['parameters']['VTEC'][0].split('.')
                feature['properties']['myId'] = '.'.join([chunks[2], chunks[3], chunks[5]])
            else:
                feature['properties']['myId'] = '.'.join(feature['properties']['id'].split('.')[:6])
            alerts.append(feature)
        return alerts


    def get_forecast( self, lat, lon ):
        url = f"https://api.weather.gov/points/{round(lat,3)},{round(lon,3)}"
        response = requests.get( url, headers=self.get_headers() )
        # print(response.text)

        response = { 'raw': json.loads(response.text) }
        for what in ['forecast', 'forecastHourly']:  #, 'forecastZone'
            response[what] = self._call_api( response['raw']['properties'][what] )

        response['daily'] = []
        if response['forecast'] is not None and 'properties' in response['forecast'] and 'periods' in response['forecast']['properties']:
            for timestep in response['forecast']['properties']['periods']:
                # Adding 1 hour to align with AccuWeather
                dt_local = datetime.strptime( timestep['startTime'], '%Y-%m-%dT%H:%M:%S%z' ) + timedelta(hours=1)
                timestep['utcTime'] = dt_local.astimezone(pytz.UTC).strftime("%Y-%m-%d %H:%M")
                timestep['datetime'] = dt_local.astimezone(pytz.UTC)
                timestep['tmpC'] = self.f_to_c( timestep['temperature'] )
                timestep['icon'] = timestep['icon'].replace(',0?', '?')
                timestep['icon'] = timestep['icon'].replace('medium', 'small')

                # If you don't time it perfectly the first instance has a different timestep than our other sources
                if len(response['daily']) == 1:
                    response['daily'][0]['datetime'] = timestep['datetime'] - timedelta(hours=12)
                    response['daily'][0]['utcTime'] = response['daily'][0]['datetime'].strftime("%Y-%m-%d %H:%M")

                timestep['pop'] = timestep['probabilityOfPrecipitation']['value']
                if timestep['pop'] is None: timestep['pop'] = 0
                pop = re.findall(r'Chance of precipitation is (\d+)%.', timestep['detailedForecast'])
                if len(pop) > 0:
                    timestep['detailedForecast'] = timestep['detailedForecast'].replace(
                                            f'Chance of precipitation is {pop[0]}%.', '')
                precip_low = None
                precip_high = None
                pcp = re.findall(
                    r'New rainfall amounts between a (tenth|quarter|half) and (quarter of an inch|half of an inch) possible.',
                    timestep['detailedForecast'])
                if len(pcp) > 0:
                    precip_low = self.text_to_inches(pcp[0][0])
                    precip_high = self.text_to_inches(pcp[0][1])
                    if precip_low is not None and precip_high is not None:
                        timestep['detailedForecast'] = timestep[
                            'detailedForecast'].replace(
                                f'New rainfall amounts between a {pcp[0][0]} and {pcp[0][1]} possible.',
                                '')

                if precip_low is None and precip_high is None:
                    pcp = re.findall(
                        r'New rainfall amounts less than a (tenth|quarter|half) of an inch possible.',
                        timestep['detailedForecast'])
                    if len(pcp) > 0:
                        precip_high = self.text_to_inches(pcp[0])
                        if precip_high is not None:
                            precip_low = 0
                            timestep['detailedForecast'] = timestep[
                                'detailedForecast'].replace(
                                    f'New rainfall amounts less than a {pcp[0]} of an inch possible.',
                                    '')

                if precip_low is not None and precip_high is not None:
                    timestep['precip'] = f'{precip_low} - {precip_high}"'
                else:
                    timestep['precip'] = ''

                pcp = re.findall(
                    r'between (\d+am|noon|\d+pm) and (\d+am|noon|\d+pm)',
                    timestep['detailedForecast'])
                if len(pcp) > 0:
                    for k in range(0, len(pcp)):
                        timestep['detailedForecast'] = timestep[
                            'detailedForecast'].replace(
                                f'between {pcp[k][0]} and {pcp[k][1]}',
                                f'from {pcp[k][0]}-{pcp[k][1]}')

                pcp = re.findall(r'wind (\d+) to (\d+) mph', timestep['detailedForecast'])
                if len(pcp) > 0:
                    for k in range(0, len(pcp)):
                        timestep['detailedForecast'] = timestep[
                            'detailedForecast'].replace(
                                f'wind {pcp[k][0]} to {pcp[k][1]} mph',
                                f'wind {pcp[k][0]}-{pcp[k][1]} mph')

                # Abbreviating stuff for a more compact text to display
                for dir in ABBREVIATING:
                    timestep['detailedForecast'] = timestep[
                        'detailedForecast'].replace(dir, ABBREVIATING[dir])

                for attr in [
                        'isDaytime', 'temperatureTrend', 'dewpoint',
                        'relativeHumidity'
                ]:
                    del timestep[attr]
                response['daily'].append(timestep)
        del response['forecast']

        response['hourly'] = []
        if response['forecastHourly'] is not None:
            for item in response['forecastHourly']['properties']['periods']:
                ts = datetime.strptime( item['startTime'], '%Y-%m-%dT%H:%M:%S%z' )
                dt_utc = ts.astimezone(pytz.UTC).strftime("%Y-%m-%d %H:%M")
                dt_local = ts.strftime("%Y-%m-%d %H:%M")
                timestep = {
                    'localTime': dt_local,
                    'utcTime': dt_utc,
                    'datetime': ts.astimezone(pytz.UTC),
                    'tmpC': self.f_to_c(item['temperature']),
                    'shortForecast': item['shortForecast'],
                    'pop': item['probabilityOfPrecipitation']['value'],
                    'precip': None,  #self._check_rain(item['shortForecast']), # Doesn't provide amount :-(
                    'icon': item['icon'].replace(',0?', '?'),
                    'text': item['shortForecast'],
                }
                response['hourly'].append( timestep )

        return response


    def _call_api( self, url, retry = 0 ):
        try:
            response = requests.get( url, headers=self.get_headers() )
            return json.loads(response.text)
        except:
            if retry > 5:
                return None
            else:
                return self._call_api( url, retry+1 )

    @staticmethod
    def _check_rain(text):
        for check in ['thunderstorm']:
            if check in text.lower():
                return 2
        for check in ['rain', 'shower', 'snow', 'thunderstorm']:
            if check in text.lower():
                return 1
        return 0
