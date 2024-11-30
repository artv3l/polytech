import json
import pymongo

import config
import dbase

def main():
    with open(config.c_filename) as f:
        data = json.load(f)
    dbase.coll.insert_many(data)

if __name__ == '__main__':
    main()
