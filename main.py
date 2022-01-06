from flask_socketio import SocketIO, emit
from flask import *
import database_wrapper
from time import time
import os
from engineio.payload import Payload
import os
import random
from time import time, sleep

from engineio.payload import Payload
from flask import *
from flask_socketio import SocketIO, emit

import database_wrapper

# import pymongo

Payload.max_decode_packets = 1000
__author__ = 'Rock'
last_time_pings_checked = time()
connected_members = {

}
parties = {

}
points_of_interest = {

}
user_data = {

}

# client = pymongo.MongoClient(
#     "mongodb+srv://school_computer:school_computer123@cluster0.6igys.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
#
# db = client.HeyPhinis
# poi = db.points_of_interest

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# app.config['DEBUG'] = True

# turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)


def random_location():
    return random.uniform(31.866, 31.929), random.uniform(34.755, 34.842)


def get_party_members(user):
    return db['ex'].get_party_members(
            owner=db['ex'].get('users', 'current_party', f'username="{user}"')[0])


def create_party(user, members=None):
    if members is None:
        members = []

    # parties[user] = {
    #     "creator": {"name": user, "sid": connected_members[user]["sid"]},
    #     "members": [{"name": u, "sid": connected_members[u]["sid"]} for u in members]
    # }
    db['ex'].create_party(user)
    print('123123123')
    for m in members:
        db['ex'].add_to_party(owner=user, user_to_add=m)
    print(f"created party for {user}")


def join_party(owner, username):
    db['ex'].add_to_party(owner=owner, user_to_add=username)


def disconnect_user_from_party(user):
    # first we update the local data
    current_leader = db['ex'].get('users', 'current_party', condition=f'username="{user}"')
    print('disconnecting', user, 'from', current_leader)
    db['ex'].remove_from_party(owner=current_leader, user_to_remove=user)
    members = get_party_members(current_leader)
    [emit_to(user=usr, event_name="update_party_members", namespace="/comms", message=members)
     for usr in members]


@app.route("/")
def home():
    # If user is logged in
    if "user" not in session:
        return redirect(url_for("login"))
    for key in list(session.keys()):
        if key != "user":
            session.pop(key)

    return render_template("main.html")


@app.route("/static/favicon.ico")  # 2 add get for favicon
def fav():
    print(os.path.join(app.root_path, 'static'))
    return send_from_directory(app.static_folder, 'favicon.ico')  # for sure return the file


def parse_action(command):
    args = command.split("/")
    command_name = args[0]
    if command_name == "accept_friend_request":
        requester = args[1]
        db["ex"].make_friends(requester, session["user"])
        user_data[session['user']]["friends"].append(requester)
        db['ex'].send_message(title=f"You and {session['user']} are now friends!",
                              desc=f"{session['user']} has accepted your friend request.",
                              message_sender=session["user"], receiver=request, messagetype="ignore",
                              action="ignore")
        emit_to(requester, 'notif', '/comms', 'notification!')

    if command_name == "join_party":
        party_owner = args[1]
        join_party(party_owner, session['user'])
        [emit_to(user=party_member, event_name="update_party_members", namespace="/comms",
                 message=get_party_members(party_owner))
         for party_member in get_party_members(party_owner)]
        print("joined party", get_party_members(session['user']))


@app.route("/inbox", methods=["POST", "GET"])
def inbox():
    if "user" not in session:
        return redirect(url_for("register"))

    # emit('reset_notifs', namespace="/comms", room=connected_members[session['user']]['sid'])
    try:
        emit_to(session['user'], "reset_notifs", "/comms")
    except KeyError:
        pass
    if request.method == "POST":
        # it has to be one, and ONLY one of these.
        message_id = request.form['accept'] + request.form['mark_as_read']
        reaction = 'accept' if request.form['accept'] != "" else 'mark_as_read'
        # first grab the message to see what we need to do with it
        _id, title, content, sender, receiver, msg_type, action = \
            db['ex'].get('messages', '*', f'id={message_id}', first=False)[0]
        print(f"{reaction}: {title} | {msg_type}")
        if reaction != "mark_as_read":
            parse_action(action)

        db['ex'].remove("messages", f'id={message_id}')
    session['inbox_messages'] = get_messages(session['user'])
    return render_template("inbox.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user = request.form['name']
        password = request.form['pass']
        # password = request.form['pass']
        # Is the password correct? Is the user valid?
        # If the user isn't valid, it throws an error.
        try:
            if str(db['ex'].get("users", "password", f'username="{user}"')[0]) != password:
                flash("Either the name, or the password are wrong.")
                return render_template("login.html")
            else:
                session['user'] = user
                # create the instance folder
                session['is_admin'] = user == db['ex'].admin

                return redirect("/")
        except Exception as e:
            flash(e)
            flash("Either the name, or the password are wrong.")
            return render_template("login.html")
    else:
        return render_template("login.html")


def get_messages(user):
    info = db['ex'].get_messages()
    if user in info['messages']:
        return [[message['id'], message['title'], message['content'], message['sender'], message['type']]
                for message in info['messages'][session['user']]]
    return []


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        # get info from form
        user = request.form['name']
        password = request.form['pass']
        confirm = request.form['confirm']
        all_names = db['ex'].get_all_names()
        if user in all_names:
            flash('This name is already taken.', category='error')
        elif len(user) < 2:
            flash('Name must be longer than 1 character.', category='error')
        elif password != confirm:
            flash('Passwords don\'t match.', category='error')
        # elif len(password) < 7:
        #     flash('Password must be at least 7 characters.', category='error')
        else:
            session['user'] = user
            db['ex'].add_user(user, password)
            return redirect("/")
        return render_template("register.html")
    else:
        return render_template("register.html")


def emit_to(user: str, event_name: str, namespace: str = '/comms', message=None):
    try:
        emit(event_name, message, namespace=namespace, room=connected_members[user]['sid'])
    except Exception as e:
        print(e)


@app.route("/", methods=["POST", "GET"])
def main_page():
    session["time"] = int(time())
    if "user" not in session:
        return redirect(url_for(f"login"))

    # if "search_place" in request.form:
    #     radius = float(request.form["radius"]) * 1000
    #     lat, lng = 31.9034937, 34.8131821
    #     rating_min = request.form["min_rating"]
    #     tp = request.form["type"]
    #     limit = int(request.form["limit"])
    #     print(radius, rating_min, tp)
    #     query_res = query((lat, lng), radius, rating_min, tp)
    #     query_res.get_all_pages(limit)
    #
    #     session["results"] = query_res.results.get()
    #     for result in session["results"]:
    #         if result not in points_of_interest:
    #             data = session["results"][result]
    #             data["interest"] = {session["user"]: 0}
    #             points_of_interest[result] = data
    #
    #     session["results_rating"] = query_res.results.sort_by_rating()
    #     session["results_name"] = query_res.results.sort_by_name()
    #
    #     return render_template("main.html", async_mode=socketio.async_mode)
    # else:
    #     session["results"] = []
    #     session["results_rating"] = []
    #     session["results_name"] = []

    return render_template("main.html")


@app.route('/friends')
def friends_func():
    return render_template("friends.html")


@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


def broadcast_userdiff():
    # update friends data
    print(session["user"])
    fr = db["ex"].get_friends(session["user"]).split(", ")
    session["friend_data"] = {'online': [friend for friend in fr if friend in connected_members],
                              'offline': [friend for friend in fr if friend not in connected_members]}

    emit_to(session["user"], 'friend_data', message=session["friend_data"])
    emit('user_diff', {'amount': len(connected_members.keys()), 'names': [user for user in connected_members]})
    print("Data:")
    print("\n".join([f"{name}, {int(time()) - connected_members[name]['last ping']}" for name in connected_members]))
    print({'amount': len(connected_members.keys()), 'names': [user for user in connected_members]})


@socketio.on('ping', namespace='/comms')
def check_ping(*args):
    global last_time_pings_checked
    user = None
    for member in connected_members:
        if connected_members[member]["sid"] == request.sid:
            user = member
    if not user:
        return
    print(f"ponged by {user}, {user} sees: {' '.join(args[0])}")
    connected_members[user]["last ping"] = int(time())
    # # # # #
    if time() - last_time_pings_checked > 2:
        for username in connected_members.copy():
            print(username, connected_members[username]["sid"])
            if int(time()) - connected_members[username]["last ping"] > 2:
                del connected_members[username]
                broadcast_userdiff()
        last_time_pings_checked = time()


@socketio.on('get_coords_of_party', namespace='/comms')
def get_coords_of_party():

    members = get_party_members(session['user'])
    data = []

    for member in members:
        try:

            lat, lng = random_location()
            connected_members[member]["loc"] = lat, lng

            data.append((member, connected_members[member]["loc"]))
        except Exception as e:
            print(connected_members)
            print('error', e)

    [emit_to(member, 'party_member_coords', '/comms',
            message=data) for member in get_party_members(session['user'])]


@socketio.on('connect', namespace='/comms')
def logged_on_users():
    # request.sid
    if 'user' not in session:
        return redirect(url_for("login"))
    connected_members[session['user']] = {
        "last ping": int(time()),
        "remote addr": request.remote_addr,
        "sid": request.sid
    }
    if session['user'] not in user_data:
        user_data[session['user']] = {
            "interests": {},
            "friends": {},
            "visited_locations": {}
        }
    lat, lng = random_location()
    connected_members[session['user']]["loc"] = lat, lng
    broadcast_userdiff()


@socketio.on('party_members_list_get', namespace='/comms')
def get_party_memb():
    emit_to(user=session['user'], event_name="party_members_list_get",
            message=get_party_members(session['user']))
    emit_to(user=session['user'], event_name="online_members_get",
            message=[x for x in connected_members])


@socketio.on('interested', namespace="/comms")
def interest(data):
    def sort_em(poi):
        # print(poi[0], points_of_interest[poi[1]]['interest'])
        location_interest = points_of_interest[poi[1]]['interest']
        return sum([location_interest[user] for user in location_interest])
    if data not in points_of_interest:
        return
    points_of_interest[data]["interest"][session["user"]] += 1
    places = [(points_of_interest[place]['name'], place) for place in points_of_interest]
    places.sort(key=sort_em, reverse=True)

    best_3 = ",   ".join([f"{ob[0]}" for ob in places][:3])

    [emit_to(user=user, event_name="best_3_locations", message=best_3)
     for user in connected_members]


@socketio.on('disconnect', namespace='/comms')
def logged_on_users():
    broadcast_userdiff()


@socketio.on('invite_user', namespace='/comms')
def invite_user(reciever):
    print("inviting", reciever)
    db['ex'].send_message(title=f"Party invite from {session['user']}!",
                          desc=f"{session['user']} has invited you to join their party, wanna hang out?",
                          sender=session["user"], receiver=reciever, messagetype="question",
                          action=f"join_party/{session['user']}")
    emit_to(reciever, 'notif','notification!')


@socketio.on('joined', namespace='/comms')
def party(data):
    if 'current party' not in session:
        session['current party'] = 0
    if data == "__self__":
        print("creating party for ",session['user'])
        create_party(session["user"])


@socketio.on('directionsData', namespace='/comms')
def directionsData(data):
    path_coords = []
    myroute = data["legs"][0]
    print(json.dumps(myroute, indent=4))
    for step in myroute["steps"]:
        for coords in step["path"]:
            path_coords.append((coords["lat"], coords["lng"]))

    sessionuser = session['user']
    leader = db['ex'].get('users', 'current_party', condition=f'username="{sessionuser}"')[0]

    for coords in path_coords:
        connected_members[leader]["loc"] = coords

        data = [False, [(member, connected_members[member]["loc"]) for member in get_party_members(sessionuser)]]

        [emit_to(member, 'party_member_coords', '/comms',
                 message=data) for member in get_party_members(session['user'])]

    #  path_coords = []
    # //        for (let i = 0; i < myRoute.steps.length; i++) {
    # //            step = myRoute.steps[i]
    # //            for (let j = 0; j < step.path.length; j++){
    # //                coords = step.path[j];
    # //                path_coords.push({lat: coords.lat(), lng: coords.lng()});
    # //            }
    # //        }
    # //          // First, remove any existing markers from the map.
    # //        for (let i = 0; i < markerArray.length; i++) {
    # //          markerArray[i].setMap(null);
    # //        }
    # //        name_start = secret_start;
    # //        var index =0
    # //        var mark = user_locations[name_start].marker
    # //        var move_interval = setInterval(function () {
    # //             mark.setPosition(path_coords[index]);
    # //             index += 1;
    # //        }, 50);


@socketio.on('left_party', namespace='/comms')
def party(data):
    if 'current party' not in session:
        session['current party'] = 0
    if data == "__self__":
        leader = db['ex'].get('users',
                              'current_party',
                              condition=f'username={session["user"]}')
        if leader == session['user']:
            for member in get_party_members(session['user']):
                db['ex'].remove_from_party(session["user"], member)
        else:
            db['ex'].remove_from_party(leader, session["user"])


if __name__ == '__main__':
    from KNN import KNN
    database_wrapper.main()
    # initialize database

    vls = {}

    db = {"ex": database_wrapper.my_db}
    print(db["ex"].get("users", "username, interests"))
    for user in db["ex"].get("users", "username"):
        interests = db["ex"].get("users", "interests", f'username="{user}"')[0].strip()
        vls[user] = interests.split("|")[1::2]
    knn = KNN(vls=vls)
    print(vls)
    db["knn"] = knn

    socketio.run(app, host="0.0.0.0", port=8080)
