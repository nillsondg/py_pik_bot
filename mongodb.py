import pymongo
import datetime
from states import Type


class MongoDB:
    client = pymongo.MongoClient()
    client_db = client.users
    cache_db = client.cache

    def check_user_id_in_db(self, uid):
        return self.client_db.users.find_one(str(uid)) is not None

    def add_user_into_db(self, user):
        self.client_db.users.insert({
            "_id": str(user.id),
            "last_name": user.last_name,
            "first_name": user.first_name,
            "username": user.username,
            "added_date": datetime.datetime.now(),
            "last_auth": datetime.datetime.now()
        })

    def update_user_auth(self, user):
        self.client_db.users.update({'_id': str(user.id)}, {"$set": {'last_auth': datetime.datetime.now()}})

    def get_last_cached_time(self, cache_type, state):
        result = self.cache_db[cache_type.value].find_one({"_id": state.description})
        if result is None:
            return None
        return result["cached_at"]

    def cache(self, data, cache_type, state):
        if cache_type == Type.sms:
            self.__cache_sms(data, cache_type.value, state.description)

    def __cache_sms(self, data, cache_type, cache_name):
        self.cache_db[cache_type].update_one({
            "_id": cache_name
        }, {"$set": {
            "txt": data,
            "cached_at": datetime.datetime.now(),
            "requested_at": datetime.datetime.now()
        }}, upsert=True)

    def get_cache(self, cache_type, state):
        if cache_type == Type.sms:
            return self.__get_sms_cache(cache_type.value, state.description)

    def __get_sms_cache(self, cache_type, cache_name):
        return self.cache_db[cache_type].find_one_and_update({"_id": cache_name},
                                                             {'$set': {'requested_at': datetime.datetime.now()}})
