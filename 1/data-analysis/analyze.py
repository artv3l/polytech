import json
from datetime import datetime, timedelta
from typing import Callable, List, Any, Tuple
import functools
from collections import Counter
from pathlib import Path

import configparser
import matplotlib.axes
import matplotlib.figure
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyspark.sql import SparkSession
 
import config
import dbase


PltFigure = matplotlib.figure.Figure
CalcFunc = Callable[[pd.DataFrame], Any] # Подготавливает данные для построения графика
PlotFunc = Callable[[Any], List[PltFigure]] # Строит график по подготовленным данным
OutFunc = Callable[[PltFigure], None] # Обработка графика: вывод на экран, сохранение в файл
bind = functools.partial


def timedelta_get_total_microseconds(td: timedelta) -> int:
    return int(td.total_seconds() * 10**6)
def print_exec_time(func, title):
    start_time = datetime.now()
    return_value = func()
    print(f'{title} - {datetime.now() - start_time}')
    return return_value

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
    if row['status'] in ['draw', 'stalemate']:
        return 'draw'
    elif row['winner'] == player_color:
        return 'win'
    elif row['winner'] == opponent_color:
        return 'lose'
    else:
        return 'draw'
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

def load_from_db() -> pd.DataFrame:
    return pd.DataFrame(list(dbase.coll.find()))
def prepare_dataframe(games: pd.DataFrame, username: str) -> pd.DataFrame:
    games['createdAt'] = pd.to_datetime(games['createdAt'], unit='ms')
    games['createdAt'] = games['createdAt'] + timedelta(hours=3) # timezone Moskow
    games['lastMoveAt'] = pd.to_datetime(games['lastMoveAt'], unit='ms')
    ppi = lambda x: pd.Series(parse_players_info(x, username))
    games[['rating', 'ratingDiff', 'opponent_rating', 'opponent_ratingDiff']] = games['players'].apply(ppi)
    games['game_result'] = games.apply(lambda x: parse_game_result(x, username), axis=1)
    games[['clock', 'opponent_clock']] = games.apply(lambda x: pd.Series(parse_clock(x, username)), axis=1)
    return games

def filter_moves_count(games: pd.DataFrame, moves_count: int) -> pd.DataFrame:
    return games[games['moves'].map(lambda x: (len(x.split()) / 2) > moves_count)]
def filter_date(games: pd.DataFrame, begin: datetime, end: datetime) -> pd.DataFrame:
    return games.loc[(games['createdAt'] > begin) & (games['createdAt'] < end)]

def calc_time(games: pd.DataFrame, interval: timedelta) -> pd.Series:
    def get_time_from_midnight(dt) -> int:
        return timedelta_get_total_microseconds(dt - dt.replace(hour=0, minute=0, second=0, microsecond=0))

    games['createdAt_from_midnight'] = games['createdAt'].apply(lambda x: get_time_from_midnight(x))

    step = timedelta_get_total_microseconds(interval)
    end = timedelta_get_total_microseconds(timedelta(days=1))
    bins = [i for i in range(0, end+step, step)]
    labels = [f'{timedelta(microseconds=i)} ->' for i in range(0, end, step)]
    
    games['createdAt_from_midnight_bins'] = pd.cut(games['createdAt_from_midnight'], bins=bins, labels=labels)
    stats = games.groupby('createdAt_from_midnight_bins', observed=False)['id'].count()
    return stats
def plot_time(stats: pd.Series) -> PltFigure:
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.bar(stats.index.tolist(), stats.values)
    ax.set_xlabel('Время суток'); ax.set_ylabel('Кол-во игр')
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    return fig

def plot_rating(games: pd.DataFrame) -> PltFigure:
    fig, ax = plt.subplots(nrows=1, ncols=1)
    games.plot(x='createdAt', y='rating', ax=ax, xlabel='Дата', ylabel='Рейтинг', legend=False)
    return fig

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

def plot_wl_rates(stats: pd.Series, xlabel: str) -> PltFigure:
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(stats.index.tolist(), stats['winrate'], label='Winrate')
    ax.plot(stats.index.tolist(), stats['loserate'], label='Loserate')
    ax.set_xlabel(xlabel); ax.set_ylabel('Процент побед / поражений'); plt.legend()
    ax.axhline(y=0.5, color='r', linestyle='--')
    #ax.axvline(x=0.0, color='b', linestyle='--')
    return fig
def plot_drawrate(stats: pd.Series, xlabel: str) -> PltFigure:
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(stats.index.tolist(), stats['drawrate'], label='Drawrate')
    #ax.axvline(x=0.0, color='b', linestyle='--')
    ax.set_xlabel(xlabel); ax.set_ylabel('Процент ничьих'); plt.legend()
    return fig

def calc_rating_diff(games: pd.DataFrame, merge_value: int) -> pd.Series:
    c_min_games_count = 20

    games = games.copy()

    games['rating_delta'] = games['rating'] - games['opponent_rating']
    games = games.loc[abs(games['rating_delta']) < 300]

    min_delta, max_delta = games['rating_delta'].min(), games['rating_delta'].max()
    
    bins = [i for i in range(min_delta, max_delta, merge_value)]
    labels = [(i+(merge_value/2)) for i in range(min_delta, max_delta-merge_value, merge_value)]
    games['rating_delta_bins'] = pd.cut(games['rating_delta'], bins=bins, labels=labels)

    stats = calc_winrate_in_bin(games, c_min_games_count, 'rating_delta_bins')
    return stats

def calc_rates_by_game_time(games: pd.DataFrame, merge_value: int) -> pd.Series:
    c_min_games_count = 10
    initial_time = 180

    games['points'] = games.apply(lambda x: parse_game_points(x), axis=1)
    games['think_time'] = games['clock'].apply(lambda x: int((x[0] - x[-1]) / 100))

    bins = [i for i in range(0, initial_time, merge_value)] + [initial_time, initial_time+1]
    labels = bins[1:]
    games['think_time_bins'] = pd.cut(games['think_time'], bins=bins, labels=labels, right=False)

    stats = calc_winrate_in_bin(games, c_min_games_count, 'think_time_bins')
    return stats

def calc_game_status(games: pd.DataFrame) -> pd.Series:
    stats = games.groupby('status', observed=False)['id'].count()
    return stats
def plot_game_status(stats: pd.Series) -> PltFigure:
    stats['draw'] += stats['stalemate']
    stats = stats[stats.index != 'stalemate']
    labels = [f'{title}: {count}' for title, count in zip(stats.index.tolist(), stats.values)]
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.pie(stats.values, labels=labels)
    ax.title.set_text(f'Total games: {sum(stats.values)}')
    return fig

def calc_game_result_by_status(games: pd.DataFrame) -> pd.Series:
    stats = games.groupby(['status', 'game_result'], observed=False)['id'].count()
    return stats
def plot_game_result_by_status(stats: pd.Series) -> PltFigure:
    types = ['mate', 'outoftime', 'resign']
    stats = stats[stats.index.isin(['mate', 'outoftime', 'resign'], level=0)]

    fig, axs = plt.subplots(nrows=1, ncols=3)

    for t, ax in zip(types, axs):
        s = stats[t]
        labels = [f'{title}: {count}' for title, count in zip(s.index.tolist(), s.values)]
        ax.pie(s.values, labels=labels)
        ax.title.set_text(t)
    return fig



def process_data(games: pd.DataFrame, calc_func: CalcFunc, plot_funcs: List[Tuple[PlotFunc, OutFunc]]):
    calc_result = calc_func(games) if (calc_func is not None) else games
    for plot_func, out_func in plot_funcs:
        figure = plot_func(calc_result)
        out_func(figure)
        plt.close(figure)

def save_to_file(figure: PltFigure, title: str):
    figure.tight_layout()
    path = f'plots/{config.c_username}/{config.game_speed}_{config.clock_initial}+{config.clock_increment}'
    Path(path).mkdir(parents=True, exist_ok=True)
    figure.savefig(f'{path}/{title}.png', dpi=300)
def binded_save(title: str):
    return functools.partial(save_to_file, title=title)
def show(figure: PltFigure):
    figure.show()
    plt.show()

def filter_games(games: pd.DataFrame) -> pd.DataFrame:
    games = games.loc[games['rated'] & (games['variant'] == 'standard') & (games['speed'] == config.game_speed)]

    # Не очень понятно, почему ratingDiff может не быть. Возможно когда рейтинг слишком сильно отличается
    games = games[games['players'].map(lambda x: ('ratingDiff' in x['white']) and ('ratingDiff' in x['black']))]
    
    games = games[games['clock'].map(lambda x: ('initial' in x) and (x['initial'] == config.clock_initial))]
    games = games[games['clock'].map(lambda x: ('increment' in x) and (x['increment'] == config.clock_increment))]
    games = filter_moves_count(games, 5)
    return games

def calc_popular_moves(games: pd.DataFrame) -> pd.Series:
    def generate_variable_windows(move_list, min_size=2, max_size=6):
        move_list = move_list.split()
        windows = []
        for window_size in range(min_size, max_size + 1):
            windows.extend([' '.join(move_list[i:i+window_size]) for i in range(len(move_list) - window_size + 1)])
        return windows

    games['moves_list'] = games['moves'].apply(generate_variable_windows)
    
    all_windows = sum(games['moves_list'], [])
    sequence_counts = Counter(all_windows)

    most_common_sequences = sequence_counts.most_common(10)
    print(most_common_sequences)


def main():

    games = print_exec_time(load_from_db, 'Load from database')
    games = filter_games(games)
    games = print_exec_time(bind(prepare_dataframe, games, config.c_username), 'Prepare dataframe')
    games = filter_date(games, '2020-09-25', '2024-09-30')

    print(f'Games count: {len(games.index)}')
    
    #print_exec_time(bind(calc_popular_moves, games), 'Calc popular moves')

    process_data(games, bind(calc_time, interval=timedelta(hours=1)),
                 [ (plot_time, binded_save('time')) ])

    process_data(games, None,
                 [ (plot_rating, binded_save('rating')) ])

    rating_mv = 10
    process_data(games, bind(calc_rating_diff, merge_value=rating_mv),
                 [
                     (bind(plot_wl_rates, xlabel='Разница в рейтинге'), binded_save(f'wl_rates_by_rating_diff_mv{rating_mv}')),
                     (bind(plot_drawrate, xlabel='Разница в рейтинге'), binded_save(f'drawrate_by_rating_diff_mv{rating_mv}')),
                 ])

    game_time_mv = 5 if config.game_speed == 'blitz' else 1
    process_data(games, bind(calc_rates_by_game_time, merge_value=game_time_mv),
                 [
                     (bind(plot_wl_rates, xlabel='Время на игру'), binded_save(f'wl_rates_by_think_time_mv{game_time_mv}')),
                     (bind(plot_drawrate, xlabel='Время на игру'), binded_save(f'drawrate_by_think_time_mv{game_time_mv}'))
                 ])

    process_data(games, calc_game_status,
                 [ (plot_game_status, binded_save('game_status')) ])
    process_data(games, calc_game_result_by_status,
                 [ (plot_game_result_by_status, binded_save('game_result_by_status')) ])

if __name__ == '__main__':
    main()
