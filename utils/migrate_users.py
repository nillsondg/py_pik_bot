import pymongo

client = pymongo.MongoClient()
users_db = client["users"]
users_prod_db = client["users_prod"]

users = users_db.users.find()

i = 1
for user in users:
    print("doing: " + str(i) + "/" + str(users.count()))
    users_prod_db.users.update_one({
        "_id": int(user["_id"])
    }, {"$set": {
        "last_name": user["last_name"],
        "first_name": user["first_name"],
        "username": user["username"],
        "group": "sms_only",
        "added_date": user["added_date"],
        "last_auth": user["last_auth"]
    }}, upsert=True)

    i += 1

print("done")
