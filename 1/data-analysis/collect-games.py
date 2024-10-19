import requests
import configparser
import ndjson
import json
import time
import datetime

config_parser = configparser.ConfigParser()
config_parser.read('config.ini')
c_token = config_parser.get('default', 'token')
c_username = config_parser.get('default', 'username')

c_urls = {
    'exportGames': 'https://lichess.org/api/games/user/{}'
}

def export_games(username: str, token: str, count: int=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/x-ndjson'
    }
    params = {
        'clocks': True,
        'opening': True,
        'division': True,
    }

    if count is not None: params['max'] = count
    
    responce = requests.get(c_urls['exportGames'].format(username), headers=headers, params=params)
    return responce.json(cls=ndjson.Decoder)

def export_games_to_file(filename: str, username: str, token: str, count: int=None) -> int:
    games = export_games(username, token, count=count)
    with open(filename, 'w') as file:
        json.dump(games, file, cls=ndjson.Encoder, indent=4)
    return len(games)

export_start_time = time.time()
games_count = export_games_to_file('games.json', c_username, c_token)
export_time = datetime.timedelta(seconds=(time.time() - export_start_time))

print(f'Export {games_count} games in {export_time}')
