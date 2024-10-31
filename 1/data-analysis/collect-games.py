import requests
import configparser
import json
import time
import datetime
import os
from typing import Tuple, Callable
import tqdm


c_urls = {
    'exportGames': 'https://lichess.org/api/games/user/{}',
    'getUserPublicData': 'https://lichess.org/api/user/{}'
}


def get_auth_headers(token: str):
    return {'Authorization': f'Bearer {token}'}

def get_user_games_count(username: str, token: str):
    headers = get_auth_headers(token)
    responce = requests.get(c_urls['getUserPublicData'].format(username), headers=headers)
    return responce.json()['count']['all']

def export_games(username: str, token: str, callback:Callable[[], None]=None, count: int=None):
    headers = get_auth_headers(token) | {
        'Accept': 'application/x-ndjson'
    }
    params = {
        'clocks': True,
        'opening': True,
        'division': True,
    }

    if count is not None: params['max'] = count
    
    result = []
    responce = requests.get(c_urls['exportGames'].format(username), headers=headers, params=params, stream=True)
    for chunk in responce.iter_lines():
        result.append(json.loads(chunk))
        if callback is not None: callback()
    return result

def export_games_to_file(filename: str, username: str, token: str, count: int=None) -> Tuple[int, datetime.timedelta]:
    games_count = get_user_games_count(username, token)
    
    with tqdm.tqdm(total=games_count) as pbar:
        def callback():
            pbar.update(1)
        export_start_time = time.time()
        games = export_games(username, token, count=count, callback=callback)
        export_time = datetime.timedelta(seconds=(time.time() - export_start_time))

    with open(filename, 'w') as file:
        json.dump(games, file, indent=4)

    return (len(games), export_time)


def main():
    config_parser = configparser.ConfigParser()
    config_parser.read('config.ini')
    c_token = config_parser.get('default', 'token')
    c_username = config_parser.get('default', 'username')

    c_filename = f'games-{c_username}.json'

    if os.path.exists(c_filename):
        print(f'File \"{c_filename}\" already exists. Rewrite.')
        os.remove(c_filename)

    (exported_games_count, export_time) = export_games_to_file(c_filename, c_username, c_token)

main()
