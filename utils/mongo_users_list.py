import pymongo
client = pymongo.MongoClient()
users_db = client.users
users_db.users.find()
users = users_db.users.find()
for user in users:
    user_str = ""
    if user["username"] is not None:
        user_str += user["username"] + " "
    else:
        user_str += "_ "
    user_str += user["last_name"] + " " + user["first_name"]
    print(user_str)
