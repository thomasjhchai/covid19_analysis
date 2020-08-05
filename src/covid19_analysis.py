import sys
import os.path
import requests
import json
from datetime import datetime
import pandas as pd


class CovidAPIData:
    """ Setting up Covid 19 data retrieval """
    # TODO: write multiple covid json data based on country

    filename = ''

    def __init__(self, country):
        # self.api_url = api_url
        # self.api_param = api_params

        with open('config.json') as f:
            data = json.load(f)
        self.api_url = data['api_url'] + country
        self.api_param = {
            'from': data['start_date'], 'to': str(datetime.today())[:10]}

    def request_resource(self):

        try:
            r = requests.get(
                self.api_url, params=self.api_param, timeout=5)
            return {'resp_code': r.status_code, 'resp_ok': r.ok}

        except requests.exceptions.RequestException as e:
            return {'resp_code': e, 'resp_ok': False}

    def __open_covid_local_data(self):
        pass


my_covid = CovidAPIData('malaysia')
us_covid = CovidAPIData('united-states')


print(my_covid.request_resource()['resp_code'], my_covid.api_url)
print(us_covid.request_resource()['resp_code'], us_covid.api_url)


"""

try:
    api_request = requests.get(API_URL, params=url_param, timeout=30)

    if os.path.isfile(COVID_LOCAL):
        print('Exist')
        t = os.path.getmtime(COVID_LOCAL)
        file_date = (str(datetime.fromtimestamp(t)))[:10]

        if file_date < str(today_date)[:10]:
            if api_request.ok:
                print('Outdated File. Updating new data from web.....')
                with open(COVID_LOCAL, "wb") as file:
                    file.write(api_request.content)
                df = pd.read_json(COVID_LOCAL)
                df.set_index('Date', inplace=True)
            else:
                print('Error: ', api_request.status_code)
                print('Use existing file.....')
                df = pd.read_json(COVID_LOCAL)
                df.set_index('Date', inplace=True)
        else:
            print('Retrieving from current file....')
            df = pd.read_json(COVID_LOCAL)
            df.set_index('Date', inplace=True)
    else:
        if api_request.ok:
            print('Pulling data from web to new file....')
            with open(COVID_LOCAL, "wb") as file:
                file.write(api_request.content)
            df = pd.read_json(COVID_LOCAL)
            df.set_index('Date', inplace=True)
        else:
            print('Error: ', api_request.status_code)
            print('No Data File exist....quiting')
            sys.exit(0)

except requests.exceptions.RequestException as e:
    print('Server Request Failed :', e)
    print('using existing file ....')
    df = pd.read_json(COVID_LOCAL)
    df.set_index('Date', inplace=True)

"""
