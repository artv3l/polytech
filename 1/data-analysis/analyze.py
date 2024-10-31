import json
import configparser
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt


def load_file(filename: str) -> pd.DataFrame:
    games = pd.read_json(filename)
    games['createdAt'] = pd.to_datetime(games['createdAt'], unit='ms')
    games['lastMoveAt'] = pd.to_datetime(games['lastMoveAt'], unit='ms')
    return games

def filter_type(games: pd.DataFrame) -> pd.DataFrame:
    return games.loc[(games['rated'] == True) & (games['variant'] == 'standard') & (games['speed'] == 'blitz')]

def filter_date(games: pd.DataFrame, begin: datetime, end: datetime) -> pd.DataFrame:
    return games.loc[(games['createdAt'] > begin) & (games['createdAt'] < end)]


def plot_time(games: pd.DataFrame):
    time_of_day_counts = {
        'night': 0,
        'morning': 0,
        'day': 0,
        'evening': 0
    }

    for index, game in games.iterrows():
        time = game['createdAt']

        if time.hour >= 2 and time.hour < 8:
            time_of_day_counts['night'] += 1
        elif time.hour >= 8 and time.hour < 14:
            time_of_day_counts['morning'] += 1
        elif time.hour >= 14 and time.hour < 20:
            time_of_day_counts['day'] += 1
        else:
            time_of_day_counts['evening'] += 1

    labels = list(time_of_day_counts.keys())
    counts = list(time_of_day_counts.values())

    plt.bar(labels, counts, color=['blue', 'orange', 'green', 'red'])
    plt.xlabel('time')
    plt.ylabel('games count')
    plt.show()

def plot_rating(games, username):
    x, y_user, y_opponent = [], [], []

    for index, game in games.iterrows():
        x.append(game['createdAt'])

        if game['players']['white']['user']['name'] == username:
            y_user.append(game['players']['white']['rating'])
            y_opponent.append(game['players']['black']['rating'])
        else:
            y_user.append(game['players']['black']['rating'])
            y_opponent.append(game['players']['white']['rating'])

    plt.plot(x, y_opponent)
    plt.plot(x, y_user)

    plt.xticks([])
    plt.xlabel('time')
    plt.ylabel('rate')
    plt.legend()
    plt.grid()
    plt.show()


def main():
    config_parser = configparser.ConfigParser()
    config_parser.read('config.ini')
    c_username = config_parser.get('default', 'username')

    c_filename = f'games-{c_username}.json'

    games = filter_type(load_file(c_filename))

    games = filter_date(games, '2020-09-25', '2024-09-30')

    plot_time(games)
    plot_rating(games, c_username)

main()
