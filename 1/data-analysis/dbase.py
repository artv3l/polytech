import pymongo

import config

client = pymongo.MongoClient('mongodb://root:root@localhost:27017/')
dbase = client[config.c_database]
coll = dbase[config.c_collname]
