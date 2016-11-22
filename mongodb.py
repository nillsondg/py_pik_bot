import pymongo
import datetime


class MongoDB:
    client = pymongo.MongoClient()
    client_db = client.users

    # cache_db = client.cache

    def check_user_id_in_db(self, uid):
        return self.client_db.users.find_one(str(uid)) is not None

    def add_user_into_db(self, user):
        self.client_db.users.insert({
            "_id": str(user.id),
            "last_name": user.last_name,
            "first_name": user.first_name,
            "username": user.username,
            "added_date": datetime.datetime.utcnow(),
            "last_auth": datetime.datetime.utcnow()
        })

    def update_user_auth(self, user):
        self.client_db.users.update({'_id': str(user.id)}, {"$set": {'last_auth': datetime.datetime.utcnow()}})
