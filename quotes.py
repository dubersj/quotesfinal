from flask import Flask, render_template, request, make_response, redirect
from mongita import MongitaClientDisk
from bson import ObjectId
from passwords import hash_password #(password), return hashed_password, salt
from passwords import check_password #(password, saved_hashed_password, salt)
from timeString import timeString

app = Flask(__name__)


# create a mongita client connection
client = MongitaClientDisk()

# open the databases
quotes_db = client.quotes_db
session_db = client.session_db
user_db = client.user_db
comment_db = client.comment_db

import uuid

#@app.route("/genusers", methods=["GET"])
#def genuser():
#    user_collection = user_db.user_collection
#    user_collection.delete_many({})

#    username = "Steve"
#    password = "MyPassword1234!"

#    result = hash_password(password)

#    user_data = {"username": username, "password": result[0], "salt": result[1]}
#    user_collection.insert_one(user_data)

#    response = redirect("/login")
#    response.delete_cookie("session_id")
#    return response

@app.route("/sessdump", methods=["GET"])
def get_dump():
    session_collection = session_db.session_collection
    session_collection.delete_many({})
    response = redirect("/login")
    response.delete_cookie("session_id")
    return response

@app.route("/", methods=["GET"])
@app.route("/quotes", methods=["GET"])
def get_quotes():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response

    # open the session collection
    session_collection = session_db.session_collection

    # get the data for this session
    session_data = list(session_collection.find({"session_id": session_id}))
    if len(session_data) == 0:
        response = redirect("/logout")
        return response
    assert len(session_data) == 1
    session_data = session_data[0]
    # get some information from the session
    user = session_data.get("user", "unknown user")
    # open the quotes collection
    quotes_collection = quotes_db.quotes_collection
    # load the data
    mydata = list(quotes_collection.find({"owner":user}))
    alldata = list(quotes_collection.find({"public":True}))
    for item in mydata:
        item["_id"] = str(item["_id"])
        item["object"] = str(ObjectId(item["_id"]))
    # display the data
    print(mydata)
    html = render_template(
        "quotes.html",
        data=mydata,
        alldata=alldata,
        user=user,
    )
    response = make_response(html)
    response.set_cookie("session_id", session_id)
    return response

@app.route("/comments", methods=["GET"])
@app.route("/comments/<id>", methods=["GET"])
def get_comments(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response

    if id:
        # open the collections
        quotes_collection = quotes_db.quotes_collection
        session_collection = session_db.session_collection
        comment_collection = comment_db.comment_collection

        # make sure user currently has a real logged in session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response

        session_data = session_data[0]
        # get some information from the server side session
        user = session_data.get("user", "")

        # get some information about the quote
        quote_data = list(quotes_collection.find({"_id": ObjectId(id)}))
        assert len(quote_data) == 1
        quote_data = quote_data[0]
        quoteowner = quote_data.get("owner", "")

        # verify ownership of quote
        if quoteowner == user:
            owner = True
        else:
            owner = False

        # get the items
        data = quotes_collection.find_one({"_id": ObjectId(id)})
        data["id"] = str(data["_id"])

        cmtdata = list(comment_collection.find({"rel_id": data["id"]}))
        for item in cmtdata:
            item["_id"] = str(item["_id"])
            item["object"] = ObjectId(item["_id"])

        if data["public"]:
            if data["comments"]:
                return render_template("comments.html", data=data, cmtdata=cmtdata, owner=owner, user=user)
            return redirect("/quotes")
        else:
            if data["comments"] and owner:
                return render_template("comments.html", data=data, cmtdata=cmtdata, owner=owner, user=user)
            return redirect("/quotes")
    else:
        return redirect("/quotes")

@app.route("/comments/add", methods=["POST"])
def post_comment():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    _id = request.form.get("_id", None)
    newcomment = request.form.get("newcomment", "")
    if newcomment == "":
        return redirect("/comments/" + _id + "?comments_must_contain_characters")

    #make sure id isn't empty
    if _id:
        # open the collections
        quotes_collection = quotes_db.quotes_collection
        session_collection = session_db.session_collection
        comment_collection = comment_db.comment_collection

        # make sure user currently has a real logged in session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response

        session_data = session_data[0]
        # get some information from the server side session
        user = session_data.get("user", "")

        # get some information about the quote
        quote_data = list(quotes_collection.find({"_id": ObjectId(_id)}))
        assert len(quote_data) == 1
        quote_data = quote_data[0]
        quoteowner = quote_data.get("owner", "")
        quotecomments = quote_data.get("comments", False)
        quotepublic = quote_data.get("public", False)

        # verify quote can have comments posted
        if quotecomments:
            # only allow owner to post comment if quote is private
            if quotepublic:
                comment_data = {"rel_id": _id, "date": timeString(), "text": newcomment, "owner": user}
                comment_collection.insert_one(comment_data)
                return redirect("/comments/"+_id)
            else:
                if quoteowner == user:
                    comment_data = {"rel_id": _id, "date": timeString(), "text": newcomment, "owner": user}
                    comment_collection.insert_one(comment_data)
                    return redirect("/comments/"+_id)
                else:
                    return redirect("/logout")
        else:
            return redirect("/logout")
    else:
        return redirect("/logout")

@app.route("/comments/delete", methods=["POST"])
def post_delete_comment():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    _id = request.form.get("_id", None)
    #make sure id isn't empty
    if _id:
        # open the collections
        quotes_collection = quotes_db.quotes_collection
        session_collection = session_db.session_collection
        comment_collection = comment_db.comment_collection

        # make sure user currently has a real logged in session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response

        session_data = session_data[0]
        # get some information from the server side session
        user = session_data.get("user", "")

        # get some information about the comment
        comment_data = list(comment_collection.find({"_id": ObjectId(_id)}))
        assert len(comment_data) == 1
        comment_data = comment_data[0]
        commentowner = comment_data.get("owner", "")
        commentrel = comment_data.get("rel_id", "")

        if user == commentowner:
            # delete the item
            comment_collection.delete_one({"_id": ObjectId(_id)})
            print("Deleted as comment owner")
            # return to the comments page
            return redirect("/comments/" + commentrel)
        else:
            # get some information about the quote if comment doesn't belong to user so quote owner can delete
            quotes_data = list(quotes_collection.find({"_id": ObjectId(commentrel)}))
            assert len(quotes_data) == 1
            quotes_data = quotes_data[0]
            quoteowner = quotes_data.get("owner", "")
            if user == quoteowner:
                comment_collection.delete_one({"_id": ObjectId(_id)})
                print("Deleted as quote owner")
                return redirect("/comments/" + commentrel)
            else:
                return redirect("/logout")
    else:
        return redirect("/logout")

@app.route("/login", methods=["GET"])
def get_login():
    session_id = request.cookies.get("session_id", None)
    print("Pre-login session id = ", session_id)
    if session_id:
        return redirect("/quotes")
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def post_login():
    user = request.form.get("user", "")
    password = request.form.get("pass", "")

    # open the user collection
    user_collection = user_db.user_collection
    user_data = list(user_collection.find({"username": user}))

    if len(user_data) == 0:
        html = render_template(
            "login.html",
            errCode=1,
        )
        response = make_response(html)
        response.delete_cookie("session_id")
        return response

    if len(user_data) == 1:
        user_data = user_data[0]
        saved_hashed_password = user_data.get("password", "")
        salt = user_data.get("salt", "")
        if check_password(password, saved_hashed_password, salt):
            session_id = str(uuid.uuid4())
            # open the session collection
            session_collection = session_db.session_collection
            # insert the user
            session_collection.delete_one({"session_id": session_id})
            session_data = {"session_id": session_id, "user": user}
            session_collection.insert_one(session_data)
            response = redirect("/quotes")
            response.set_cookie("session_id", session_id)
            return response
        else:
            html = render_template(
                "login.html",
                errCode=3,
            )
            response = make_response(html)
            response.delete_cookie("session_id")
            return response

    html = render_template(
        "login.html",
        errCode=2,
    )
    response = make_response(html)
    response.delete_cookie("session_id")
    return response

@app.route("/register", methods=["GET"])
def get_register():
    session_id = request.cookies.get("session_id", None)
    if session_id:
        return redirect("/quotes")
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def post_register():
    user = request.form.get("user", "")
    password = request.form.get("pass", "")
    password2 = request.form.get("pass2", "")

    # open the user collection
    user_collection = user_db.user_collection
    user_data = list(user_collection.find({"username": user}))

    if len(user_data) != 0:
        html = render_template(
            "register.html",
            errCode=1,
        )
        response = make_response(html)
        response.delete_cookie("session_id")
        return response

    if password != password2:
        html = render_template(
            "register.html",
            errCode=2,
        )
        response = make_response(html)
        response.delete_cookie("session_id")
        return response

    result = hash_password(password)

    new_user = {"username": user, "password": result[0], "salt": result[1]}
    user_collection.insert_one(new_user)

    html = render_template(
        "login.html",
        errCode=0,
    )
    response = make_response(html)
    response.delete_cookie("session_id")
    return response

@app.route("/logout", methods=["GET"])
def get_logout():
    # get the session id
    session_id = request.cookies.get("session_id", None)
    if session_id:
        # open the session collection
        session_collection = session_db.session_collection
        # delete the session
        session_collection.delete_one({"session_id": session_id})
    response = redirect("/login")
    response.delete_cookie("session_id")
    return response


@app.route("/add", methods=["GET"])
def get_add():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    return render_template("add_quote.html")


@app.route("/add", methods=["POST"])
def post_add():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    # open the session collection
    session_collection = session_db.session_collection
    # get the data for this session
    session_data = list(session_collection.find({"session_id": session_id}))
    if len(session_data) == 0:
        response = redirect("/logout")
        return response
    assert len(session_data) == 1
    session_data = session_data[0]
    # get some information from the session
    user = session_data.get("user", "unknown user")
    text = request.form.get("text", "")
    author = request.form.get("author", "")
    if text != "" and author != "":
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # insert the quote
        quote_data = {"date": timeString(), "owner": user, "text": text, "author": author, "public":False, "comments":False}
        quotes_collection.insert_one(quote_data)
    # usually do a redirect('....')
    return redirect("/quotes")


@app.route("/edit/<id>", methods=["GET"])
def get_edit(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        # get the item
        data = quotes_collection.find_one({"_id": ObjectId(id)})
        data["id"] = str(data["_id"])
        return render_template("edit_quote.html", data=data)
    # return to the quotes page
    return redirect("/quotes")


@app.route("/edit", methods=["POST"])
def post_edit():
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    _id = request.form.get("_id", None)
    text = request.form.get("text", "")
    author = request.form.get("author", "")

    if _id:
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        session_collection = session_db.session_collection

        # make sure swapping user currently has a real logged in session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response

        session_data = session_data[0]
        # get some information from the server side session
        user = session_data.get("user", "")

        # get some information about the quote
        quote_data = list(quotes_collection.find({"_id": ObjectId(_id)}))
        assert len(quote_data) == 1
        quote_data = quote_data[0]
        quoteowner = quote_data.get("owner", "")

        # verify ownership of quote
        if quoteowner == user:
            # update the values in this particular record
            values = {"$set": {"text": text, "author": author}}
            quotes_collection.update_one({"_id": ObjectId(_id)}, values) # in dr. d's repot this had "data ="
            return redirect("/quotes")
        else:
            return redirect("/logout")
    # do a redirect('....')
    else:
        return redirect("/quotes")

@app.route("/swapp/<id>", methods=["GET"])
def get_swapp(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        session_collection = session_db.session_collection

        # make sure swapping user currently has a real logged in session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response

        session_data = session_data[0]
        # get some information from the server side session
        user = session_data.get("user", "")

        # get some information about the quote
        quote_data = list(quotes_collection.find({"_id": ObjectId(id)}))
        assert len(quote_data) == 1
        quote_data = quote_data[0]
        quoteowner = quote_data.get("owner", "")

        # verify ownership of quote
        if quoteowner == user:
            # get the item
            data = quotes_collection.find_one({"_id": ObjectId(id)})
            quotevis = data["public"]
            if quotevis == True:
                values = {"$set": {"public": False}}
            else:
                values = {"$set": {"public": True}}
            quotes_collection.update_one({"_id": ObjectId(id)}, values)
            return redirect("/edit/" + id)
    else:
        return redirect("/logout")

# This is essentially the same as the function above, and this authentication
# method is used elsewhere. This can be condensed in the future.
# This also probably doesn't need to be a route but it works.
@app.route("/swapc/<id>", methods=["GET"])
def get_swapc(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open the quotes collection
        quotes_collection = quotes_db.quotes_collection
        session_collection = session_db.session_collection

        # make sure swapping user currently has a real logged in session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response

        session_data = session_data[0]
        # get some information from the server side session
        user = session_data.get("user", "")

        # get some information about the quote
        quote_data = list(quotes_collection.find({"_id": ObjectId(id)}))
        assert len(quote_data) == 1
        quote_data = quote_data[0]
        quoteowner = quote_data.get("owner", "")

        # verify ownership of quote
        if quoteowner == user:
            # get the item
            data = quotes_collection.find_one({"_id": ObjectId(id)})
            comallow = data["comments"]
            if comallow == True:
                values = {"$set": {"comments": False}}
            else:
                values = {"$set": {"comments": True}}
            quotes_collection.update_one({"_id": ObjectId(id)}, values)
            return redirect("/edit/" + id)
    else:
        return redirect("/logout")


@app.route("/delete", methods=["GET"])
@app.route("/delete/<id>", methods=["GET"])
def get_delete(id=None):
    session_id = request.cookies.get("session_id", None)
    if not session_id:
        response = redirect("/login")
        return response
    if id:
        # open collections
        quotes_collection = quotes_db.quotes_collection
        session_collection = session_db.session_collection

        # make sure deleting user currently has a real logged in session
        session_data = list(session_collection.find({"session_id": session_id}))
        if len(session_data) == 0:
            response = redirect("/logout")
            return response

        session_data = session_data[0]
        # get some information from the server side session
        user = session_data.get("user", "")

        # get some information about the quote
        quote_data = list(quotes_collection.find({"_id": ObjectId(id)}))
        assert len(quote_data) == 1
        quote_data = quote_data[0]
        quoteowner = quote_data.get("owner", "")


        # verify ownership of quote
        if quoteowner == user:
            # delete the item
            quotes_collection.delete_one({"_id": ObjectId(id)})
            # return to the quotes page
            return redirect("/quotes")

    # or logout
    return redirect("/logout")

if __name__=="__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)