import configparser

config_parser = configparser.ConfigParser()
config_parser.read('config.ini')

c_username = config_parser.get('default', 'username')
c_filename = f'data/games-{c_username}.json'
c_token = config_parser.get('default', 'token')
c_collname = f'games-{c_username}'
c_database = 'data-analysis'
