import pymongo
client = pymongo.MongoClient()
users_db = client["test-users"]
users = users_db.users.find()
file = open("UserDB.txt", "w")
header = "id\tusername\tlast_name\tfirst_name\n"
file.write(header)
print(header)
for user in users:
    user_str = str(user['_id']) + "\t"
    if user["username"] is not None:
        user_str += user["username"]
    else:
        user_str += "null"
    user_str += "\t"
    if user["last_name"] is not None:
        user_str += user["last_name"]
    else:
        user_str += "null"
    user_str += "\t"
    user_str += user["first_name"]
    file.write(user_str + "\n")
    print(user_str)

file.close()
