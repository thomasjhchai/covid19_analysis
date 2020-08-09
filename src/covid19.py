import sys
import os.path
import requests
import json
from datetime import datetime
import pandas as pd
# import matplotlib.pyplot as plt
import urllib.request


class CovidDataFrame:

    _categories = ['Confirmed', 'Deaths', 'Recovered']
    _df_list = ['df_confirmed', 'df_deaths', 'df_recovered']

    def __init__(self, country):

        with open('config.json') as f:
            config_data = json.load(f)

        # download data to be used when connection error
        self.__download_data(config_data)

        df = dict(zip(CovidDataFrame._categories, CovidDataFrame._df_list))

        # inserting all the dataframes into a dictionary
        # (ie: {'confirmed': df_confirmed})
        df_dict = {}
        for index, item in enumerate(self.__init_dataframe(config_data, **df)):
            df_dict.update(
                {CovidDataFrame._categories[index]: item})

        df_country = self.__load_country(country, df_dict)

        # <REFACTOR> into function perhaps
        # combining 'Confirmed', 'Deaths' Recovered' dataframe
        # into a single dataframe based on country (df_country)
        df_c = []
        for df_generator in df_country:
            df_c.append(df_generator)

        df_combined = pd.DataFrame(df_c)
        df_combined = df_combined.transpose()
        df_combined.columns = CovidDataFrame._categories
        df_combined['Active'] = df_combined['Confirmed'] \
            - df_combined['Deaths'] \
            - df_combined['Recovered']

        self.dataframe = self.__calc_daily(country, df_combined)
        # </REFACTOR> into function perhaps

        # grab the start date and end date
        self.start_date = df_dict['Confirmed'].index[0]
        self.end_date = df_dict['Confirmed'].index[-1]

    def __download_data(self, config):
        """ download copies of remote data for use if
            network connection error
        """

        csv_url = [config['Confirmed'], config['Deaths'], config['Recovered']]
        filenames = [config['c_file'], config['d_file'], config['r_file']]

        file_dict = dict(zip(csv_url, filenames))

        for url in file_dict:
            try:
                request = requests.get(url, timeout=5)
                self.__check_file(request, file_dict[url])
            except requests.exceptions.RequestException:
                print(f'Timeout: [{url}]')

    def __check_file(self, request, file):
        """ check if file exist or up to date before pulling from web
        """

        if os.path.isfile(file):
            t = os.path.getmtime(file)
            file_date = (str(datetime.fromtimestamp(t)))[: 10]

            # check if file is up to date
            if file_date < str(datetime.today())[: 10]:
                if request.ok:
                    print(
                        f'Outdated File: [{file}]. Pull from: [{request.url}]')
                    self.__write_file(file, request)
                else:
                    print('Error: ', request.status_code)
                    print(f'Loading local file: [{file}]')
        else:
            if request.ok:
                print(f'File: [{file}] not found. Pull from: [{request.url}]')
                self.__write_file(file, request)
            else:
                print('Error: ', request.status_code)
                print('No Data File exist and server error: Exiting....')
                sys.exit(0)

    def __write_file(self, file, request):
        with open(file, "wb") as f:
            f.write(request.content)

    def __load_country(self, country, df_dict):
        """ loading all the frames ['Confirmed', 'Deaths. 'Recovered']
            that belong to the specified country
        """
        for item in CovidDataFrame._categories:
            yield df_dict[item][country]

    def __init_dataframe(self, config_data, **kwargs):
        """ setting up initial dataframe
        """
        # TODO: write a better function description above

        local_files = dict(zip(CovidDataFrame._categories,
                               [config_data['c_file'], config_data['d_file'],
                                config_data['r_file']]))

        for key, df_value in kwargs.items():
            try:
                df_value = pd.read_csv(config_data[key])
            except urllib.error.URLError:
                df_value = pd.read_csv(local_files[key])
                print(
                    f'Server error. Retrieving local files: [{local_files[key]}]')

            # restructure dataframes
            df_value.drop(columns=['Lat', 'Long'], inplace=True)
            df_value = df_value.groupby(
                'Country/Region').sum().transpose()

            # change date format  from str '2/3/20' to date object
            for date_item in df_value.index:
                date_obj = datetime.strptime(date_item, '%m/%d/%y')
                # date_str = datetime.strftime(date_obj, '%Y-%m-%d')
                df_value.rename(
                    index={date_item: date_obj}, inplace=True)

            # assigned total 'World' value based on dates
            for idx in df_value.index:
                df_value.loc[idx, 'World'] = df_value.loc[idx].sum()

            # Force World numbers to be int instead of float.
            # It seems sum() returns float64
            # Is there a better way to do it?
            df_value['World'] = df_value['World'].astype(int)

            yield df_value

    # TODO: change function name to better reflect the code
    def __calc_daily(self, country, df):
        """ Calculate Daily Cases, Deaths and Recoveries from
            given dataset

            - Daily Cases = Total Cases[Today] - Total Cases[Previous Day]
            - Daily Deaths = Total Deaths[Today] - Total Deaths[Previous Day]
            - Daily Recoveries = Total Recovered[Today] - Total Recovered[Previous Day]
        """
        daily_cases = []
        daily_deaths = []
        daily_recovered = []

        for index, item in enumerate(df.index):
            if item == df.index[0]:
                new_case = df.loc[df.index[0], 'Confirmed']
                new_death = df.loc[df.index[0], 'Deaths']
                new_recovered = df.loc[df.index[0], 'Recovered']

                daily_cases.append(new_case)
                daily_deaths.append(new_death)
                daily_recovered.append(new_recovered)

            else:
                new_case = df.loc[df.index[index], 'Confirmed'] - \
                    df.loc[df.index[index-1], 'Confirmed']
                new_death = df.loc[df.index[index], 'Deaths'] - \
                    df.loc[df.index[index-1], 'Deaths']
                new_recovered = df.loc[df.index[index], 'Recovered'] - \
                    df.loc[df.index[index-1], 'Recovered']

                daily_cases.append(new_case)
                daily_deaths.append(new_death)
                daily_recovered.append(new_recovered)

            df.loc[item, ['Daily Cases', 'Daily Deaths', 'Daily Recovered']] \
                = daily_cases[index], daily_deaths[index], daily_recovered[index]

        # Population by Country data pulled from UN
        # [source: https://population.un.org/wpp/Download/Standard/Population/]
        # edited to conform to country's name
        pop_df = pd.read_csv('../data/population.csv')
        pop_df['Country'] = pop_df['Country'].str.replace(
            ' ', '-')
        pop_df['Pop.(\'000)'] = pop_df['Pop.(\'000)'].str.replace(' ', '').astype(int) \
            * 1000
        pop_df.set_index('Country', inplace=True)

        # adding 'Rates' columns to dataframe
        df['Mortality Rates'] = round(df['Deaths'].divide(
            df['Confirmed']).fillna(0.0), 4) * 100
        df['Recovered Rates'] = round(df['Recovered'].divide(
            df['Confirmed']).fillna(0.0), 4) * 100
        df['Active Rates'] = round(df['Active'].divide(
            df['Confirmed']).fillna(0.0), 4) * 100
        df['Cases per 1mil pop'] = (
            (df['Confirmed'] / pop_df.loc[country, 'Pop.(\'000)']) * 1000000).astype(int)

        # converting float to integer as these columns should
        # not have decimals
        df[['Daily Cases', 'Daily Deaths', 'Daily Recovered']] = df[[
            'Daily Cases', 'Daily Deaths', 'Daily Recovered']].astype(int)

        return df


esp = CovidDataFrame('Australia')
print('Australia:\n ', esp.dataframe.tail(100))
print(f'start date = {esp.start_date}, end date = {esp.end_date}')
print(
    f'info: \n{esp.dataframe.loc[esp.end_date]} \n{esp.dataframe.loc[esp.start_date]}')
print(esp.dataframe.loc['2020-07'])
