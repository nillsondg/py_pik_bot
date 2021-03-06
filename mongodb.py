import pymongo
import datetime
import logging
from config import MONGODB_USERS, MONGODB_CACHE


class MongoDB:
    client = pymongo.MongoClient()
    user_db = client[MONGODB_USERS]
    cache_db = client[MONGODB_CACHE]

    def check_user_id_in_db(self, user_id):
        return self.user_db.users.find_one(user_id) is not None

    def add_user_into_db(self, user):
        self.user_db.users.insert({
            "_id": user.id,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "username": user.username,
            "group": user.group.value,
            "added_date": datetime.datetime.now(),
            "last_auth": datetime.datetime.now()
        })

    def get_user_from_db(self, user_id):
        return self.user_db.users.find_one(user_id)

    def get_user_for_group_from_db(self, group_name):
        return self.user_db.users.find({"group": group_name})

    def get_users(self):
        return self.user_db.users.find()

    def update_user_auth(self, user):
        self.user_db.users.update({'_id': user.id}, {"$set": {'last_auth': datetime.datetime.now()}})

    def update_user_group(self, user):
        self.user_db.users.update({'_id': user.id}, {"$set": {'group': user.group.value}})

    def get_last_cached_time(self, state):
        result = self.cache_db[state.type.value].find_one({"_id": state.description})
        if result is None:
            return None
        return result["cached_at"]

    def cache(self, data, state):
        self._cache(data, state.type.value, state.description)

    def _cache(self, data, cache_type, cache_name):
        self.cache_db[cache_type].update_one({
            "_id": cache_name
        }, {"$set": {
            "txt": data,
            "cached_at": datetime.datetime.now(),
            "requested_at": datetime.datetime.now()
        }}, upsert=True)
        logging.info(datetime.datetime.now().strftime("%d-%m %H:%M:%S") + " cached " + cache_name)

    def cache_file_info(self, file_name, state):
        cache_name = state.description
        cache_type = state.type.value
        self.cache_db[cache_type].update_one({
            "_id": cache_name
        }, {"$set": {
            "file_name": file_name,
            "file_id": None,
            "cached_at": datetime.datetime.now(),
            "requested_at": datetime.datetime.now()
        }}, upsert=True)
        logging.info(datetime.datetime.now().strftime("%d-%m %H:%M:%S") + " cached " + cache_name)

    def update_file_id(self, file_id, state):
        cache_name = state.description
        cache_type = state.type.value
        self.cache_db[cache_type].update({'_id': cache_name}, {"$set": {'file_id': file_id}})

    def update_file_name(self, file_name, state):
        cache_name = state.description
        cache_type = state.type.value
        self.cache_db[cache_type].update({'_id': cache_name}, {"$set": {'file_name': file_name}})

    def get_cache(self, cache_type, state):
        return self._get_cache(cache_type.value, state.description)

    def _get_cache(self, cache_type, cache_name):
        return self.cache_db[cache_type].find_one_and_update({"_id": cache_name},
                                                             {'$set': {'requested_at': datetime.datetime.now()}})
