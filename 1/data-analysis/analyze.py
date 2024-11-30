import json
from datetime import datetime, timedelta
from typing import Callable, List
import functools

import configparser
import matplotlib.axes
import matplotlib.figure
import pandas as pd
import matplotlib.pyplot as plt

import config
import dbase

PlotFunc = Callable[[pd.DataFrame], List[matplotlib.figure.Figure]]


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

def parse_clock(row, username):
    result = {}
    (player_color, opponent_color) = ('white', 'black') if row['players']['white']['user']['name'] == username else ('black', 'white')
    white_clock = row['clocks'][::2]
    black_clock = row['clocks'][1::2]
    result['clock'] = white_clock if player_color == 'white' else black_clock
    result['opponent_clock'] = black_clock if player_color == 'white' else white_clock
    return result


def load_data(filename: str, username: str) -> pd.DataFrame:
    start_time = datetime.now()
    games = pd.DataFrame(list(dbase.coll.find()))
    print(f'Load data - {datetime.now() - start_time}')

    start_time = datetime.now()
    games = filter_type(games)
    games['createdAt'] = pd.to_datetime(games['createdAt'], unit='ms')
    games['createdAt'] = games['createdAt'] + timedelta(hours=3) # timezone Moskow
    games['lastMoveAt'] = pd.to_datetime(games['lastMoveAt'], unit='ms')
    ppi = lambda x: pd.Series(parse_players_info(x, username))
    games[['rating', 'ratingDiff', 'opponent_rating', 'opponent_ratingDiff']] = games['players'].apply(ppi)
    games['game_result'] = games.apply(lambda x: parse_game_result(x, username), axis=1)
    games[['clock', 'opponent_clock']] = games.apply(lambda x: pd.Series(parse_clock(x, username)), axis=1)
    print(f'Prepare data - {datetime.now() - start_time}')

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


def save_plot(games: pd.DataFrame, plot_func: PlotFunc, filenames: List[str]):
    start_time = datetime.now()
    figures = plot_func(games)
    calc_time = datetime.now() - start_time
    print(f'{filenames} - {calc_time}')
    for fig, filename in zip(figures, filenames):
        fig.tight_layout()
        fig.savefig(filename, dpi=300)
        plt.close(fig)


def plot_time(games: pd.DataFrame, interval: timedelta) -> List[matplotlib.figure.Figure]:
    def get_time_from_midnight(dt) -> int:
        return timedelta_get_total_microseconds(dt - dt.replace(hour=0, minute=0, second=0, microsecond=0))

    games['createdAt_from_midnight'] = games['createdAt'].apply(lambda x: get_time_from_midnight(x))

    step = timedelta_get_total_microseconds(interval)
    end = timedelta_get_total_microseconds(timedelta(days=1))
    bins = [i for i in range(0, end+step, step)]
    labels = [f'{timedelta(microseconds=i)} ->' for i in range(0, end, step)]
    
    games['createdAt_from_midnight_bins'] = pd.cut(games['createdAt_from_midnight'], bins=bins, labels=labels)
    stats = games.groupby('createdAt_from_midnight_bins', observed=False)['id'].count()

    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.bar(stats.index.tolist(), stats.values)
    ax.set_xlabel('Время суток'); ax.set_ylabel('Кол-во игр')
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    return [fig]
   
def plot_rating(games: pd.DataFrame) -> List[matplotlib.figure.Figure]:
    fig, ax = plt.subplots(nrows=1, ncols=1)
    games.plot(x='createdAt', y='rating', ax=ax, xlabel='Дата', ylabel='Рейтинг', legend=False)
    return [fig]

def calc_winrate_in_bin(games: pd.DataFrame, min_games_count: int, bin_name: str):
    agg_dict = {
        'game_result': ['count',
                        lambda val: (val == 'win').sum(),
                        lambda val: (val == 'lose').sum(),
                        lambda val: (val == 'draw').sum(),]
        }
    axis = ['count', 'win_count', 'lose_count', 'draw_count']
    stats = games.groupby(bin_name, observed=False).agg(agg_dict).set_axis(axis, axis=1)
    stats = stats[stats['count'] > min_games_count]
    stats['winrate'] = stats['win_count'] / stats['count']
    stats['loserate'] = stats['lose_count'] / stats['count']
    stats['drawrate'] = stats['draw_count'] / stats['count']
    return stats

def plot_rating_diff(games: pd.DataFrame, merge_value: int) -> List[matplotlib.figure.Figure]:
    c_min_games_count = 20

    games = games.copy()

    games['rating_delta'] = games['rating'] - games['opponent_rating']
    games = games.loc[abs(games['rating_delta']) < 300]

    min_delta, max_delta = games['rating_delta'].min(), games['rating_delta'].max()
    
    bins = [i for i in range(min_delta, max_delta, merge_value)]
    labels = [(i+(merge_value/2)) for i in range(min_delta, max_delta-merge_value, merge_value)]
    games['rating_delta_bins'] = pd.cut(games['rating_delta'], bins=bins, labels=labels)

    stats = calc_winrate_in_bin(games, c_min_games_count, 'rating_delta_bins')

    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(stats.index.tolist(), stats['winrate'], label='Winrate')
    ax.plot(stats.index.tolist(), stats['loserate'], label='Loserate')
    ax.set_xlabel('Разница в рейтинге'); ax.set_ylabel('Процент побед / поражений'); plt.legend()
    ax.axhline(y=0.5, color='r', linestyle='--')
    return [fig]

def calc_winrate_by_game_time(games: pd.DataFrame, merge_value: int):
    c_min_games_count = 10

    games['points'] = games.apply(lambda x: parse_game_points(x), axis=1)
    games['think_time'] = games['clock'].apply(lambda x: int((x[0] - x[-1]) / 100))

    bins = [i for i in range(0, 181, merge_value)]
    labels = bins[1:]
    games['think_time_bins'] = pd.cut(games['think_time'], bins=bins, labels=labels)

    stats = calc_winrate_in_bin(games, c_min_games_count, 'think_time_bins')
    return stats

def plot_winrate_by_game_time(games: pd.DataFrame, merge_value: int) -> List[matplotlib.figure.Figure]:
    stats = calc_winrate_by_game_time(games, merge_value)

    fig1, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(stats.index.tolist(), stats['winrate'], label='Winrate')
    ax.plot(stats.index.tolist(), stats['loserate'], label='Loserate')
    ax.set_xlabel('Время на игру'); ax.set_ylabel('Процент побед / поражений'); plt.legend()
    ax.axhline(y=0.5, color='r', linestyle='--')

    fig2, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(stats.index.tolist(), stats['drawrate'], label='Drawrate')
    ax.set_xlabel('Время на игру'); ax.set_ylabel('Процент ничьих'); plt.legend()

    return [fig1, fig2]

    
def main():
    games = load_data(config.c_filename, config.c_username)
    games = filter_date(games, '2020-09-25', '2024-09-30')

    save_plot(games, plot_rating, ['plots/rating.png'])
    save_plot(games, functools.partial(plot_time, interval=timedelta(hours=1)), ['plots/time.png'])
    save_plot(games, functools.partial(plot_rating_diff, merge_value=10), ['plots/rating_diff.png'])
    save_plot(games, functools.partial(plot_winrate_by_game_time, merge_value=10), ['plots/winrate_by_think_time.png', 'plots/drawrate_by_think_time.png'])

if __name__ == '__main__':
    main()
