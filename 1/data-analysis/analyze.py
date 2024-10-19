import json
import configparser
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


def plot_rating(games, username):
    x, y = [], []
    for game in games:
        x.append(game['createdAt'])
        if game['players']['white']['user']['name'] == username:
            y.append(game['players']['white']['rating'])
        else:
            y.append(game['players']['black']['rating'])
    
    plt.plot(x, y)
    plt.show()

def main():
    games = load_filter_games(c_filename)
    plot_rating(games, c_username)

main()
