import os
import pymongo
import logging
from collections import namedtuple

import config
from helpers import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Get environment variables
USER = os.getenv('DB_USER')
PASSWORD = os.environ.get('DB_PASSWORD')

client = pymongo.MongoClient(f"mongodb+srv://{USER}:{PASSWORD}@cluster0-dioya.mongodb.net/test?retryWrites=true&w=majority")
db = client.sidapp
users = db.users

u = []

#print(users.find_one({ 'name' : { 'title' : 'Mr' or 'Ms', 'first' : 'Leah', 'last' : 'Flan' }, 'type' : 2 }))


# for doc in users.find():
#   print('Name: ' + doc['name']['first'] + ' ' + doc['name']['last'])

#print(u)

user = Dict2Obj(users.find_one({ 'name' : { 'title' : 'Mr' or 'Ms', 'first' : 'Leah', 'last' : 'Flan' }, 'type' : 2 }))
print(user.name)


