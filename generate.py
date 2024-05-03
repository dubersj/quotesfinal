# Create a Mongita database with quotes and session information
import json
from datetime import datetime
from mongita import MongitaClientDisk
from passwords import hash_password #(password), return hashed_password, salt

# create a mongita client connection
client = MongitaClientDisk()

# open the databases
quotes_db = client.quotes_db
session_db = client.session_db
user_db = client.user_db
comment_db = client.comment_db

# create/open the collections
quotes_collection = quotes_db.quotes_collection
session_collection = session_db.session_collection
user_collection = user_db.user_collection
comment_collection = comment_db.comment_collection

# preset data

current_time = datetime.now()
saved_date = str(current_time.month) + '/' + str(current_time.day) + '/' + str(current_time.year)
saved_time = str(current_time.hour) + ':' + str(current_time.minute) + "UTC"
saved_datetime_string = saved_date + ' ' + saved_time

print(saved_datetime_string)

#quotes
quotes_data = [
    {"date": saved_datetime_string, "text":"Default Quote One.", "author":"Administrator", "owner":"Steve", "public":True, "comments":True},
    {"date": saved_datetime_string, "text":"Default Quote Two.", "author":"Administrator", "owner":"Steve", "public":True, "comments":False},
    {"date": saved_datetime_string, "text":"Default Quote Three.", "author":"Administrator", "owner":"Steve", "public":False, "comments":False},
]

# default logins
username = "Steve"
password = "MyPassword1234!"

username2 = "User"
#same password

result = hash_password(password)

user_data = {"username": username, "password": result[0], "salt": result[1]}
user2_data = {"username": username2, "password": result[0], "salt": result[1]}


# empty the collections
quotes_collection.delete_many({})
session_collection.delete_many({})
user_collection.delete_many({})
comment_collection.delete_many({})

# put stuff in the databases
quotes_collection.insert_many(quotes_data)
user_collection.insert_one(user_data)
user_collection.insert_one(user2_data)

# getting ID of first default quote (will break if another quote is added to default data with comments true)
mydata = list(quotes_collection.find({"comments":True}))
for item in mydata:
        item["_id"] = str(item["_id"])
        comment_data = {"rel_id": item["_id"], "date": saved_datetime_string, "text": "Wow, what an insightfully generated quote! Thanks for that", "owner": "User"}
        comment_collection.insert_one(comment_data)
        comment_data = {"rel_id": item["_id"], "date": saved_datetime_string, "text": "I have added a comment to my own quote!", "owner": "Steve"}
        comment_collection.insert_one(comment_data)

# make sure things are/aren't there
print("Quotes")
print(quotes_collection.count_documents({}))

print("Sessions")
print(session_collection.count_documents({}))

print("Users")
print(user_collection.count_documents({}))

print("Comments")
print(comment_collection.count_documents({}))