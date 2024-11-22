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

def parse_game_points(row):
    if row['game_result'] == 'draw': return 0
    elif row['game_result'] == 'win': return 1
    else: return -1

def load_file(filename: str, username: str) -> pd.DataFrame:
    games = filter_type(pd.read_json(filename))
    games['createdAt'] = pd.to_datetime(games['createdAt'], unit='ms')
    games['createdAt'] = games['createdAt'] + timedelta(hours=3) # timezone Moskow
    games['lastMoveAt'] = pd.to_datetime(games['lastMoveAt'], unit='ms')

    ppi = lambda x: pd.Series(parse_players_info(x, username))
    games[['rating', 'ratingDiff', 'opponent_rating', 'opponent_ratingDiff']] = games['players'].apply(ppi)

    games['game_result'] = games.apply(lambda x: parse_game_result(x, username), axis=1)

    return games

def filter_moves_count(games: pd.DataFrame, moves_count: int) -> pd.DataFrame:
    return games[games['moves'].map(lambda x: (len(x.split()) / 2) > moves_count)]

# standard rated blitz 3+2, more 5 moves
def filter_type(games: pd.DataFrame) -> pd.DataFrame:
    games = games.loc[(games['rated'] == True) & (games['variant'] == 'standard') & (games['speed'] == 'blitz')]
    games = games[games['clock'].map(lambda x: ('initial' in x) and (x['initial'] == 180))]
    games = games[games['clock'].map(lambda x: ('increment' in x) and (x['increment'] == 2))]
    games = filter_moves_count(games, 5)
    return games

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

    games['rating_delta'] = games['rating'] - games['opponent_rating']
    games['points'] = games.apply(lambda x: parse_game_points(x), axis=1)

    games = games.loc[abs(games['rating_delta']) < 300]

    min_delta, max_delta = games['rating_delta'].min(), games['rating_delta'].max()
    
    bins = [i for i in range(min_delta, max_delta, merge_value)]
    labels = [(i+(merge_value/2)) for i in range(min_delta, max_delta-merge_value, merge_value)]

    games['rating_delta_bins'] = pd.cut(games['rating_delta'], bins=bins, labels=labels)
    stats = games.groupby('rating_delta_bins', observed=False)['points'].sum()

    plt.plot(stats.index.tolist(), stats.values)
    plt.show()

def plot_winrate_by_game_time(games: pd.DataFrame, username):
    def parse_clock(row, username):
        result = {}
        (player_color, opponent_color) = ('white', 'black') if row['players']['white']['user']['name'] == username else ('black', 'white')
        white_clock = row['clocks'][::2]
        black_clock = row['clocks'][1::2]
        result['clock'] = white_clock if player_color == 'white' else black_clock
        result['opponent_clock'] = black_clock if player_color == 'white' else white_clock
        return result

    games['points'] = games.apply(lambda x: parse_game_points(x), axis=1)
    games[['clock', 'opponent_clock']] = games.apply(lambda x: pd.Series(parse_clock(x, username)), axis=1)
    games['think_time'] = games['clock'].apply(lambda x: int((x[0] - x[-1]) / 100))
    #games['opponent_think_time'] = games['opponent_clock'].apply(lambda x: int((x[0] - x[-1]) / 100))

    bins = [i for i in range(0, 181, 5)]
    labels = bins[1:]

    games['think_time_bins'] = pd.cut(games['think_time'], bins=bins, labels=labels)
    stats = games.groupby('think_time_bins', observed=False)['points'].sum()

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

    #plot_time(games, timedelta(hours=1))

    plot_winrate_by_game_time(games, c_username)

main()
