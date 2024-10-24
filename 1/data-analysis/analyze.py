import json
import configparser
from datetime import datetime

import matplotlib.pyplot as plt

config_parser = configparser.ConfigParser()
config_parser.read('config.ini')
c_username = config_parser.get('default', 'username')

c_filename = f'games-{c_username}.json'


def load_filter_games(filename):
    games_filter = lambda game: game['rated'] and (game['variant'] == 'standard') and (game['speed'] == 'blitz')

    with open(filename, 'r') as file:
        games = json.load(file)
    return list(filter(games_filter, games))


def plot_time(games):
    time_of_day_counts = {
        'night': 0,
        'morning': 0,
        'day': 0,
        'evening': 0
    }

    for game in games:
        t = int(game['createdAt']) / 1000
        time = datetime.utcfromtimestamp(t)

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


def plot_rating(games, username, firstDate='2020-01-01', lastDate=datetime.now().strftime('%Y-%m-%d')):
    x, y_user, y_opponent = [], [], []

    for game in reversed(games):
        t = int(game['createdAt']) / 1000
        time = datetime.utcfromtimestamp(t).strftime('%Y-%m-%d')
        # date = str(time.year)+ "/" +str(time.month)
        if (firstDate > time or lastDate < time):
            continue
        x.append(t)

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
    games = load_filter_games(c_filename)
    plot_time(games)
    plot_rating(games, c_username, '2024-09-25', '2024-09-30')

main()