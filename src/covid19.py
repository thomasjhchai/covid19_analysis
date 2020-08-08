import sys
import os.path
import requests
import json
from datetime import datetime
import pandas as pd
import urllib.request


class CovidDataFrame:

    _categories = ['confirmed', 'deaths', 'recovered']
    _df_list = ['df_confirmed', 'df_deaths', 'df_recovered']

    def __init__(self, country):

        with open('config.json') as f:
            config_data = json.load(f)

        df = dict(zip(CovidDataFrame._categories, CovidDataFrame._df_list))

        # inserting all the dataframes into a dictionary
        # (ie: {'confirmed': df_confirmed})
        df_dict = {}
        for index, item in enumerate(self.__init_dataframe(config_data, **df)):
            df_dict.update(
                {CovidDataFrame._categories[index]: item})

        # self.__calc_world(*CovidDataFrame._categories)
        df_country = self.__load_country(country, df_dict)

        # <REFACTOR> into function perhaps
        df_c = []
        for df_generator in df_country:
            df_c.append(df_generator)

        df_combined = pd.DataFrame(df_c)
        df_combined = df_combined.transpose()
        df_combined.columns = CovidDataFrame._categories
        df_combined['active'] = df_combined['confirmed'] \
            - df_combined['deaths'] \
            - df_combined['recovered']
        print(df_combined)
        # </REFACTOR> into function perhaps

        # grab the start date
        self.start_date = df_dict['confirmed'].index[0]

        self.__download_data(config_data)

    def __download_data(self, config):
        """ download copies of remote data for use if
            network connection error
        """

        csv_url = [config['confirmed'], config['deaths'], config['recovered']]
        filenames = [config['c_file'], config['d_file'], config['r_file']]

        for file in filenames:
            print('debug checking filename', file)
            for item in csv_url:
                #   print('debug csv_url', item)

                try:
                    request = requests.get(item, timeout=5)
                    self.__check_file(request, file, config)
                except requests.exceptions.RequestException:
                    print('Timeout JH Data')

    def __check_file(self, request, file, config):

        # for file in filenames:
        if os.path.isfile(file):
            t = os.path.getmtime(file)
            file_date = (str(datetime.fromtimestamp(t)))[: 10]

            # check if file is up to date
            if file_date < str(datetime.today())[: 10]:
                if request.ok:
                    print('Outdated File: Pulling data from web....')
                    self.__write_file(file, request)
                    # return True
                else:
                    print('Error: ', request.status_code)
                    print('Loading existing file....')
                    # return False
            else:
                #    self.__write_file(file, request)
                print('file current....')
                # return True
        else:
            if request.ok:
                print('No file found: Pulling data from web....')
                self.__write_file(file, request)
                # return True
            else:
                print('Error: ', request.status_code)
                print('No Data File exist and server error: Exiting....')
                sys.exit(0)

    def __write_file(self, file, request):
        with open(file, "wb") as f:
            f.write(request.content)

    def __load_country(self, country, df_dict):
        for item in CovidDataFrame._categories:
            yield df_dict[item][country]

    def __init_dataframe(self, config_data, **kwargs):

        for key in kwargs:
            try:
                kwargs[key] = pd.read_csv(config_data[key])
            except urllib.error.URLError as e:
                # TODO: instead of exist, pull from file (if file exist else exit)
                print(e)
                sys.exit(0)

            # restructure dataframes
            kwargs[key].drop(columns=['Lat', 'Long'], inplace=True)
            kwargs[key] = kwargs[key].groupby(
                'Country/Region').sum().transpose()

            # change date format '2/3/20' to '2020-03-02'
            for date_item in kwargs[key].index:
                date_obj = datetime.strptime(date_item, '%m/%d/%y')
                date_str = datetime.strftime(date_obj, '%Y-%m-%d')
                kwargs[key].rename(
                    index={date_item: date_str}, inplace=True)

            yield kwargs[key]

    def __calc_world(self, *args):

        for item in args:
            print('__calc_world', item)


test = CovidDataFrame('China')


# %%

list_1 = ['confirmed', 'death', 'recovered']
list_2 = ['df_confirmed', 'df_death', 'df_recovered']

dict_test = zip(list_1, list_2)
print(dict(dict_test))


# %%
