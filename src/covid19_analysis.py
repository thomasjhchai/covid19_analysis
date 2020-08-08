import sys
import os.path
import requests
import json
from datetime import datetime
import pandas as pd


class CovidDataFrame:

    num_countries = 0

    def __init__(self, country):

        self.country = country

        with open('config_a.json') as f:
            config_data = json.load(f)
            api_url = config_data['country_api_url'] + country
            api_param = {'from': config_data['start_date'],
                         'to': str(datetime.today())[:10]}

        self.file = config_data['local_dir'] + \
            'covid_19_' + country.lower() + '.json'

        # track number of countries connections
        CovidDataFrame.num_countries += 1

        try:
            self.request = requests.get(
                api_url, params=api_param, timeout=5)
        # return {'resp_code': request.status_code,
        # 'resp_ok': request.ok}

        except requests.exceptions.RequestException:
            print('Timeout')
        # return {'resp_code': 'Timeout...',
        # 'resp_ok': False}

        ## status = self.request_resource()
        # if status['resp_ok']:

    def init_dataframe(self):
        if(self.__check_file(self.file, self.request)):
            df = pd.read_json(self.file)

            # set Date column as index
            df.set_index('Date', inplace=True)
            # strip index date of time info
            for item in df.index:
                df.rename(index={item: str(item)[:10]}, inplace=True)

            # remove unwanted Columns
            df.drop(columns=['Country', 'CountryCode', 'Province',
                             'City', 'CityCode', 'Lat', "Lon"], inplace=True)

            df = self.__new_datasets(df)

        return df

    def __new_datasets(self, df):
        """ add new calculated dataset into DataFrame """

        # Population by Country data pulled from UN
        # [source: https://population.un.org/wpp/Download/Standard/Population/] edited to conform to country's name
        pop_df = pd.read_csv('../data/population.csv')
        pop_df['Country'] = pop_df['Country'].str.replace(' ', '-')
        pop_df['Pop.(\'000)'] = pop_df['Pop.(\'000)'].str.replace(' ', '') \
            .astype(int) * 1000
        pop_df.set_index('Country', inplace=True)

        daily_cases = []
        daily_deaths = []
        daily_recovered = []

        for index, item in enumerate(df.index):
            if item == df.index[0]:
                new_case, new_death, new_recovered = df.loc[df.index[0], [
                    'Confirmed', 'Deaths', 'Recovered']]
                daily_cases.append(new_case)
                daily_deaths.append(new_death)
                daily_recovered.append(new_recovered)

            else:
                new_case, new_death, new_recovered = df.loc[df.index[index], ['Confirmed', 'Deaths', 'Recovered']] \
                    - df.loc[df.index[index - 1],
                             ['Confirmed', 'Deaths', 'Recovered']]
                daily_cases.append(new_case)
                daily_deaths.append(new_death)
                daily_recovered.append(new_recovered)

            df.loc[item, ['Daily Cases', 'Daily Deaths', 'Daily Recovered']] \
                = daily_cases[index], daily_deaths[index], daily_recovered[index]

        # release unwanted objects from memory
        del daily_cases, daily_deaths, daily_recovered

        df['Mortality Rates'] = round(df['Deaths'].divide(
            df['Confirmed']).fillna(0.0), 4) * 100
        df['Recovered Rates'] = round(df['Recovered'].divide(
            df['Confirmed']).fillna(0.0), 4) * 100
        df['Active Rates'] = round(df['Active'].divide(
            df['Confirmed']).fillna(0.0), 4) * 100
        df['Cases per 1mil pop'] = (
            (df['Confirmed'] / pop_df.loc[self.country, 'Pop.(\'000)']) * 1000000).astype(int)
        df[['Daily Cases', 'Daily Deaths', 'Daily Recovered']] = df[[
            'Daily Cases', 'Daily Deaths', 'Daily Recovered']].astype(int)

        return df

    def past_month(self):
        pass

    def max_daily_record(self, df):
        # Max Daily Record
        result = df[['Daily Cases', 'Daily Deaths', 'Daily Recovered']].max()
        return dict(result)

    def average_record(self, df):
        # Average Record
        result = round(
            df[['Daily Cases', 'Daily Deaths', 'Daily Recovered']].mean(), 2)
        return dict(result)

    def __check_file(self, file, request):
        """
        Check File Condition
            - if exist
            - if outdated
        """
        if os.path.isfile(file):
            t = os.path.getmtime(file)
            file_date = (str(datetime.fromtimestamp(t)))[:10]

            # check if file is up to date
            if file_date < str(datetime.today())[:10]:
                if request.ok:
                    print('Outdated File: Pulling data from web....')
                    self.__open_file(file, request)
                    return True
                else:
                    print('Error: ', request.status_code)
                    print('Loading existing file....')
                    return False
            else:
                print('Loading existing file....')
                return True
        else:
            if request.ok:
                print('No file found: Pulling data from web....')
                self.__open_file(file, request)
                return True
            else:
                print('Error: ', request.status_code)
                print('No Data File exist and server error: Exiting....')
                sys.exit(0)

    def __open_file(self, file, request):
        with open(file, "wb") as f:
            f.write(request.content)


# TODO: figure a way to return dataframe when create instance. use __new__()
my_covid = CovidDataFrame('Malaysia')
us_covid = CovidDataFrame('Singapore')

my_df = my_covid.init_dataframe()
print('Malaysia (Avg Daily):', my_covid.average_record(my_df))
us_df = us_covid.init_dataframe()
print('Singapore (Avg Daily):', us_covid.average_record(us_df))
