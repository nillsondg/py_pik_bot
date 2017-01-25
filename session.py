import mongodb
import datetime
import json
from collections import OrderedDict
from enum import Enum
from states import State

mongo = mongodb.MongoDB()

with open('rights.json') as f:
    rights = json.load(f, object_pairs_hook=OrderedDict)


class Group(Enum):
    users = "users"
    admins = "admins"
    owners = "owners"


class Broadcast:
    def __init__(self, group, text):
        self.group = group
        self.text = text


class User:
    state = State.none
    last_state = State.none
    last_request_time = None
    group = None

    @staticmethod
    def create_user_from_telegram(tg_user):
        user = User()
        user.id = tg_user.id
        user.last_name = tg_user.last_name
        user.first_name = tg_user.first_name
        user.username = tg_user.username
        return user

    @staticmethod
    def create_user_from_mongo(mongo_user):
        user = User()
        user.id = mongo_user["_id"]
        user.last_name = mongo_user["last_name"]
        user.first_name = mongo_user["first_name"]
        user.username = mongo_user["username"]
        user.group = Group(mongo_user["group"])
        return user


# todo name problem
class Session:
    _users = dict()
    _bcasts = dict()

    def get_user(self, uid, user_id):
        if uid not in self._users:
            if not mongo.check_user_id_in_db(user_id):
                self._users[uid] = User()
            else:
                mongo_user = mongo.get_user_from_db(user_id)
                self._users[uid] = User.create_user_from_mongo(mongo_user)
        return self._users[uid]

    def get_user_with_msg(self, msg):
        uid = msg.chat.id
        tg_user = msg.from_user
        if uid not in self._users:
            if not mongo.check_user_id_in_db(tg_user.id):
                self._users[uid] = User.create_user_from_telegram(tg_user)
            else:
                mongo_user = mongo.get_user_from_db(tg_user.id)
                self._users[uid] = User.create_user_from_mongo(mongo_user)
        return self._users[uid]

    def add_user(self, uid, user):
        mongo.add_user_into_db(user)
        self._users[uid] = user

    def update_user_group(self, user):
        mongo.update_user_group(user)

    def update_user_auth(self, user):
        mongo.update_user_auth(user)

    def get_current_state(self, uid, user_id):
        return self.get_user(uid, user_id).state

    def set_current_state(self, uid, user_id, state):
        self.get_user(uid, user_id).state = state

    def get_user_last_state(self, uid, user_id):
        return self.get_user(uid, user_id).last_state

    def set_user_last_state(self, uid, user_id, state):
        self.get_user(uid, user_id).last_state = state

    def get_last_request_time(self, uid, user_id):
        return self.get_user(uid, user_id).last_request_time

    def set_last_request_time_now(self, uid, user_id):
        self.get_user(uid, user_id).last_request_time = datetime.datetime.now()

    def check_user_id_in_db(self, user_id):
        return mongo.check_user_id_in_db(user_id)

    def is_user_in_admins_group(self, uid, user_id):
        return self.get_user(uid, user_id).group == Group.admins

    def is_user_in_users_group(self, uid, user_id):
        return self.get_user(uid, user_id).group == Group.users

    def get_users_for_group(self, group_name):
        raw_users = mongo.get_user_for_group_from_db(group_name)
        users = []
        for raw_user in raw_users:
            users.append(User.create_user_from_mongo(raw_user))
        return users

    def check_group_exist(self, group_name):
        return group_name in [e.value for e in Group]

    def add_bcast_msg(self, uid, group_name, text):
        self._bcasts[uid] = Broadcast(group_name, text)

    def pop_bcast_msg(self, uid):
        return self._bcasts.pop(uid)

    def check_rights(self, user, cmd):
        cmd_list = Session._get_cmd_list(user.group)
        return cmd in cmd_list

    @staticmethod
    def _get_cmd_list(user_group):
        return rights[user_group.value]
