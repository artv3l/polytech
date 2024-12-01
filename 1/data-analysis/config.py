import configparser

config_parser = configparser.ConfigParser()
config_parser.read('config.ini')

c_username = config_parser.get('default', 'username')
c_filename = f'data/games-{c_username}.json'
c_token = config_parser.get('default', 'token')
c_collname = f'games-{c_username}'
c_database = 'data-analysis'

game_speed: str = config_parser.get('game_filter', 'speed')
clock_initial: int = int(config_parser.get('game_filter', 'clock_initial'))
clock_increment: int = int(config_parser.get('game_filter', 'clock_increment'))
