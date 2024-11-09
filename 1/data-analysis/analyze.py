import json
import configparser
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt


def timedelta_get_total_microseconds(td: timedelta) -> int:
    return int(td.total_seconds() * 10**6)


def parse_players_info(row, username):
    result = {}
    (player_color, opponent_color) = ('white', 'black') if row['white']['user']['name'] == username else ('black', 'white')
    result['rating'] = row[player_color]['rating']
    result['ratingDiff'] = row[player_color]['ratingDiff']
    result['opponent_rating'] = row[opponent_color]['rating']
    result['opponent_ratingDiff'] = row[opponent_color]['ratingDiff']
    return result

def parse_game_result(row, username):
    (player_color, opponent_color) = ('white', 'black') if row['players']['white']['user']['name'] == username else ('black', 'white')
    if row['status'] == 'draw':
        return 'draw'
    elif row['winner'] == player_color:
        return 'win'
    else:
        return 'lose'


def load_file(filename: str, username: str) -> pd.DataFrame:
    games = filter_type(pd.read_json(filename))
    games['createdAt'] = pd.to_datetime(games['createdAt'], unit='ms')
    games['createdAt'] = games['createdAt'] + timedelta(hours=3) # timezone Moskow
    games['lastMoveAt'] = pd.to_datetime(games['lastMoveAt'], unit='ms')

    ppi = lambda x: pd.Series(parse_players_info(x, username))
    games[['rating', 'ratingDiff', 'opponent_rating', 'opponent_ratingDiff']] = games['players'].apply(ppi)

    games['game_result'] = games.apply(lambda x: parse_game_result(x, username), axis=1)

    return games

def filter_type(games: pd.DataFrame) -> pd.DataFrame:
    return games.loc[(games['rated'] == True) & (games['variant'] == 'standard') & (games['speed'] == 'blitz')]

def filter_date(games: pd.DataFrame, begin: datetime, end: datetime) -> pd.DataFrame:
    return games.loc[(games['createdAt'] > begin) & (games['createdAt'] < end)]


def plot_time(games: pd.DataFrame, interval: timedelta):
    def get_time_from_midnight(dt) -> int:
        return timedelta_get_total_microseconds(dt - dt.replace(hour=0, minute=0, second=0, microsecond=0))

    games['createdAt_from_midnight'] = games['createdAt'].apply(lambda x: get_time_from_midnight(x))

    step = timedelta_get_total_microseconds(interval)
    end = timedelta_get_total_microseconds(timedelta(days=1))
    bins = [i for i in range(0, end+step, step)]
    labels = [f'{timedelta(microseconds=i)} ->' for i in range(0, end, step)]
    
    games['createdAt_from_midnight_bins'] = pd.cut(games['createdAt_from_midnight'], bins=bins, labels=labels)
    stats = games.groupby('createdAt_from_midnight_bins', observed=False)['id'].count()

    plt.bar(stats.index.tolist(), stats.values)
    plt.xticks(rotation=45, ha='right')
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

def plot_rating_diff(games: pd.DataFrame, merge_value: int):
    games = games.copy()

    def get_points(game_result):
        if game_result == 'draw': return 0
        elif game_result == 'win': return 1
        else: return -1

    games['rating_delta'] = games['rating'] - games['opponent_rating']
    games['points'] = games['game_result'].apply(lambda x: get_points(x))

    games = games.loc[abs(games['rating_delta']) < 300]

    min_delta, max_delta = games['rating_delta'].min(), games['rating_delta'].max()
    
    bins = [i for i in range(min_delta, max_delta, merge_value)]
    labels = [(i+(merge_value/2)) for i in range(min_delta, max_delta-merge_value, merge_value)]

    games['rating_delta_bins'] = pd.cut(games['rating_delta'], bins=bins, labels=labels)
    stats = games.groupby('rating_delta_bins', observed=False)['points'].sum()

    plt.plot(stats.index.tolist(), stats.values)
    plt.show()


def main():
    config_parser = configparser.ConfigParser()
    config_parser.read('config.ini')
    c_username = config_parser.get('default', 'username')

    c_filename = f'games-{c_username}.json'

    games = load_file(c_filename, c_username)
    games = filter_date(games, '2020-09-25', '2024-09-30')

    merge_value = 20 # 5 .. 25
    #plot_rating_diff(games, merge_value)

    plot_time(games, timedelta(hours=1))

main()
