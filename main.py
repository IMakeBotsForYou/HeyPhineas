import os
import random
from time import time
import numpy as np
from engineio.payload import Payload
from flask import *
from flask_socketio import SocketIO, emit
from get_query_results import query
import database_wrapper
from KNN import get_color
# import pymongo

Payload.max_decode_packets = 1000
__author__ = 'Rock'
last_time_pings_checked = time()

connected_members = {

}
points_of_interest = {

}
user_data = {

}
party_locations = {

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
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True, async_handlers=True)


def random_location():
    return random.uniform(31.8884302, 31.9043486), random.uniform(34.8025995, 34.8146395)


def get_party_members(username):
    return db['ex'].get_party_members(
        owner=get_party_leader(username))


def create_party(user, members=None):
    if members is None:
        members = []

    db['ex'].create_party(user)
    print('123123123')
    for m in members:
        db['ex'].add_to_party(owner=user, user_to_add=m)
    print(f"created party for {user}")


def join_party(owner, username):
    db['ex'].add_to_party(owner=owner, user_to_add=username)


def disconnect_user_from_party(user):
    # first we update the local data
    current_leader = get_party_leader(user)
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


@app.route("/static/favicon.ico")  # 2 add get for favicon
def fav():
    print(os.path.join(app.root_path, 'static'))
    return send_from_directory(app.static_folder, 'static/favicon.ico')  # for sure return the file


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
        print(f"Sent to {user}: {event_name} {message} {namespace} ")
    except Exception as e:
        print(f'Error in emitting to user {user},', e)
        print(f'Tried to send: ', message, event_name)


@app.route("/", methods=["POST", "GET"])
def main_page():
    session["time"] = int(time())
    if "user" not in session:
        return redirect(url_for("login"))
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
    fr = db["ex"].get_friends(session["user"])

    visisble_uses = [x for x in connected_members if x != "Admin"]

    session["friend_data"] = {'online': [friend for friend in fr if friend in visisble_uses],
                              'offline': [friend for friend in fr if friend not in visisble_uses]}

    emit_to(session["user"], 'friend_data', message=session["friend_data"])
    [emit_to(us, 'user_diff',
             message={'amount': len(connected_members.keys()), 'names': [user for user in visisble_uses]}) for us in
     connected_members]
    print("Data:")
    print("\n".join([f"{name}, {int(time()) - connected_members[name]['last ping']}" for name in visisble_uses]))
    print({'amount': len(connected_members.keys()), 'names': [user for user in connected_members]})


@socketio.on('request_destination_update', namespace='/comms')
def destination_update_request(data):
    [emit_to(user=party_m, event_name='update_destination',
             message=data)
     for party_m in get_party_members(session['user']) if party_m in connected_members]


@socketio.on('place_form_data', namespace='/comms')
def place_form(data):
    tp, radius, rating_min, limit = data.split("|")
    radius = float(radius) * 1000
    lat, lng = db['ex'].get_user_location(session['user'])
    limit = int(limit)
    query_res = query((lat, lng), radius, rating_min, tp)
    query_res.get_all_pages(limit)

    results_json = query_res.results.get()

    middle_lat, middle_lng = sum(
        [connected_members[member]["loc"][0] for member in get_party_members(session['user']) if
         member in connected_members]) / len(get_party_members(session['user'])), \
                             sum([connected_members[member]["loc"][1] for member in get_party_members(session['user'])
                                  if member in connected_members]) / len(get_party_members(session['user']))
    middle = middle_lat, middle_lng

    data = [
        # a[0] = NAME: STR
        # a[1] = LAT, LNG: STR
        # a[2] = TYPE: STRs
        (a[0], [float(x) for x in a[1].split(", ")], a[2])
        for a in db['ex'].get_user_added_locations() if a[2] == tp
    ]

    for i in range(len(data)):
        dat = data[i]
        results_json[ord('a') + i] = {"name": dat[0], "location": dat[1]}

    places = list(results_json.keys())

    def get_distance(place):
        loc = results_json[place]["location"]
        return np.linalg.norm(np.array(middle) - np.array([loc]))

    places.sort(key=lambda x: get_distance(x))

    coords = list(results_json[places[0]]["location"])

    party_locations[get_party_leader(session['user'])] = coords

    [emit_to(user=party_m, event_name='update_destination',
             message=coords)
     for party_m in get_party_members(session['user']) if party_m in connected_members]


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

    send_path_to_party(session['user'])
    # if get_party_leader(session['user']) == session['user']:
    #     party_locations[session['user']] = db['ex'].get_user_location(session['user'])
    if session['user'] == "Admin":
        members = db['ex'].get_all_names(removeAdmin=True)
        for member in members:
            lat, lng = db['ex'].get_user_location(member)
            emit_to("Admin", 'my_location', message=[member, [lat, lng]])


def weight_values(name, value):
    origin = db['knn'].origin
    mult = 1
    friends = db['ex'].get_friends(origin)
    if name in friends:
        mult += 0.3

    friends_of_name = db['ex'].get_friends(name)
    mutual_friends = [x for x in friends if x in friends_of_name]
    mult += 0.05 * len(mutual_friends)

    return value / mult


@socketio.on('location_recommendation_request', namespace='/comms')
def location_recommendation_request():
    pass
    # members = get_party_members(session['user'])
    # my_loc = connected_members[session['user']]['loc']
    # locations = [connected_members[m]['loc'] for m in members if m in connected_members]
    # middle_lat, middle_lng = sum([loc[0] for loc in locations]) / len(locations), sum(
    #     [loc[1] for loc in locations]) / len(locations)
    # farthest = max([connected_members[x]['loc'][0] for x in members]), \
    #            max([connected_members[x]['loc'][1] for x in members])
    # max_distance = 3963.0 * np.arccos[(np.sin(middle_lat) * np.sin(farthest[0]))
    #                   + np.sin(middle_lat) * np.sin(farthest[0]) * np.sin(farthest[1] - middle_lng)]
    # interest_values = {}
    #
    # for entry in db['knn'].values:
    #     if entry not in members and entry not in ["__ideal_restaurant", "__ideal_park"]:
    #         interest_values[entry] = db['knn'].values[:5]
    #
    # # db['knn'].sort_users("__ideal_restaurant", "__ideal_park")
    # # db['knn'].run(only_these_values=interest_values)
    #
    # query_res = query((middle_lat, middle_lng), max_distance, 0, place_type)
    # query_res.get_all_pages()
    #
    # session["results"] = query_res.results.get()
    # # print(1234, json.dumps(session['results'], indent=2))
    # place_locations = [session["results"][x]["location"] for x in session["results"]]
    # place_locations += [(middle_lat, middle_lng)]
    # [emit_to(member, 'suggestions', message=place_locations) for member in get_party_members(session["user"])]


def send_path_to_party(user_to_track):
    party_members = get_party_members(user_to_track)
    paths = []

    for member in party_members:
        if member not in user_to_track and member in connected_members:
            try:
                path, index = connected_members[member]['current_path']
                paths.append((member, [connected_members[member]['loc']] + path[index:]))
                print(f"Adding path from {member}[:{index}], sending to {user_to_track} ({party_members})")
            except Exception as e:
                print(f"Error in drawing path from {member} on {session['user']}'s screen | {e}")
    emit_to(session["user"], 'user_paths', message=paths)
    emit_to("Admin", 'user_paths', message=paths)


@socketio.on('send_current_path', namespace='/comms')
def return_path(data):
    # # # # # # # # # # # # # # # # # # # # # # # # # # #.data, step_index
    connected_members[session['user']]['current_path'] = [data, 0]
    print(f"Received path from {session['user']}")
    # send_path_to_party(user_to_track=session['user'])
    # print(json.dumps(connected_members[session['user']]))


@socketio.on('send_dest', namespace='/comms')
def return_path(data):
    # # # # # # # # # # # # # # # # # # # # # # # # # # #.data, step_index
    party_locations[get_party_leader(session['user'])] = data
    # send_path_to_party(user_to_track=session['user'])
    # print(json.dumps(connected_members[session['user']]))


def try_reset_first(user):
    route, lng = connected_members[user]['current_path']

    if lng >= len(route):
        emit_to(user, 'reset_first')


@socketio.on('step', namespace='/comms')
def step():
    connected_members[session['user']]['current_path'][1] += 1
    # try_reset_first(session['user'])


@socketio.on('knn_select', namespace='/comms')
def knn_select_user(selected_user):
    # db['knn'].set_origin(selected_user)
    # db['knn'].run(weigh_values=weight_values)
    # members = [name for name in connected_members]
    # names = [entry[0] for entry in db['knn'].run(n=int(math.sqrt(len(members)))) if entry[0] in members]
    # emit_to(session['user'], 'knn_results', message=names)
    pass


def party_coords(username, request_directions=False):
    members = get_party_members(username)
    data = []

    for member in members:
        try:
            data.append((member, connected_members[member]["loc"]))
        except KeyError:
            loc = db['ex'].get_user_location(member)
            data.append((member, loc))
            # connected_members[member]["loc"] = loc
        except Exception as e:
            print("get coords error", e)
    members.append("Admin")
    data = [request_directions, data]
    [emit_to(member, 'party_member_coords', '/comms',
             message=data) for member in members if member in connected_members]


@socketio.on('get_coords_of_party', namespace='/comms')
def get_coords_of_party():
    if session['user'] == "Admin":
        members = db['ex'].get_all_names(removeAdmin=True)
        data = []
        for member in members:
            try:
                data.append((member, connected_members[member]["loc"]))
            except KeyError:
                loc = db['ex'].get_user_location(member)
                data.append((member, loc))
            except Exception as e:
                print("get coords error", e)

        data = [False, data]
        emit_to("Admin", 'party_member_coords', '/comms', message=data)

    else:
        # members = [p for p in get_party_members(session['user']) if p in connected_members]
        leader = get_party_leader(session['user'])

        if db['ex'].get_party_status(leader) == "in progress" and session['user'] == leader:
            db['ex'].set_party_status(leader, "halt")
            print("caught halt")

        party_coords(leader, True)


@socketio.on('connect', namespace='/comms')
def logged_on_users():
    # request.sid
    if 'user' not in session:
        return redirect(url_for("login"))

    # reconnecting = session['user'] in connected_members

    connected_members[session['user']] = {
        "last ping": int(time()),
        "remote addr": request.remote_addr,
        "sid": request.sid,
        "loc": [0, 0],
        "current_path": [None, None]
    }
    if session['user'] not in user_data:
        user_data[session['user']] = {
            "interests": {},
            "friends": {},
            "visited_locations": {}
        }
    if session['user'] != "Admin":
        connected_members[session['user']]["loc"] = db['ex'].get_user_location(session['user'])

    emit_to(session['user'], 'my_location', message=[session['user'], connected_members[session['user']]["loc"]])

    broadcast_userdiff()
    actually_users = [x for x in connected_members if x != "Admin"]
    if len(actually_users) > 1:
        clusters = knn.find_optimal_clusters(reps=20)
        user_colors = {}
        for centroid in clusters:
            for person in clusters[centroid]:
                user_colors[person[0]] = get_color(person[0], clusters)

        emit_to("Admin", event_name="user_colors", message=user_colors)

@socketio.on('party_members_list_get', namespace='/comms')
def get_party_memb():
    emit_to(user=session['user'], event_name="party_members_list_get",
            message=get_party_members(session['user']))


@socketio.on('online_members_get', namespace='/comms')
def get_online_memb():
    emit_to(user=session['user'], event_name="online_members_get",
            message=[x for x in connected_members])


@socketio.on('user_added_locations_get', namespace='/comms')
def get_user_added_loc():
    data = [
        # a[0] = NAME: STR
        # a[1] = LAT, LNG: STR
        # a[2] = TYPE: STR
        (a[0], [float(x) for x in a[1].split(", ")], a[2])
        for a in db['ex'].get_user_added_locations()
    ]
    emit_to(user=session['user'], event_name="user_added_locations",
            message=data)


def send_user_added_locations(username):
    data = [(name, [float(value) for value in latlng.split(", ")])
            for name, latlng, type in db['ex'].get_user_added_locations()]
    emit_to(username, 'user_added_locations', message=data)


@socketio.on('user_added_locations_get', namespace='/comms')
def get_user_added_loc():
    send_user_added_locations(session['user'])


@socketio.on('reset_locations', namespace='/comms')
def reset_locs():
    database_wrapper.reset_locations()

    party_data = {}

    for party_leader in db["ex"].get("parties", "creator"):
        party_data[party_leader] = [
            True,
            [
                [x, db['ex'].get_user_location(x)]
                for x in get_party_members(party_leader)
            ]
        ]
        [try_reset_first(user) for user in get_party_members(party_leader)]

    party_data["Admin"] = [
        False,
        [
            [x, db['ex'].get_user_location(x)]
            for x in db['ex'].get_all_names(removeAdmin=True)]
    ]

    try:
        for member in connected_members:
            if member != "Admin":
                emit_to(member, 'party_member_coords',
                        message=party_data[get_party_leader(member)])

    except KeyError:
        print("Error KEYERROR 594 reset locations")


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
    # broadcast_userdiff()
    pass


@socketio.on('invite_user', namespace='/comms')
def invite_user(receiver):
    print("inviting", receiver)
    db['ex'].send_message(title=f"Party invite from {session['user']}!",
                          desc=f"{session['user']} has invited you to join their party, wanna hang out?",
                          sender=session["user"], receiver=receiver, messagetype="question",
                          action=f"join_party/{session['user']}")

    emit_to(receiver, 'notif', namespace='/comms', message='notification!')


@socketio.on('add_location', namespace='/comms')
def invite_user(data):
    name, lat, lngm, loc_type = data.split(", ")
    db['ex'].add_location(name, lat, lng, loc_type)
    [send_user_added_locations(online_user) for online_user in connected_members]


@socketio.on('invite_user', namespace='/comms')
def invite_user(receiver):
    print("inviting", receiver)
    db['ex'].send_message(title=f"Party invite from {session['user']}!",
                          desc=f"{session['user']} has invited you to join their party, wanna hang out?",
                          sender=session["user"], receiver=receiver, messagetype="question",
                          action=f"join_party/{session['user']}")
    emit_to(receiver, 'notif', namespace='/comms', message='notification!')


@socketio.on('get_destination', namespace='/comms')
def get_destination():
    if session['user'] == "Admin":
        return
    try:
        emit_to(session['user'], event_name='update_destination',
                message=party_locations[get_party_leader(session['user'])])
    except:
        pass


@socketio.on('joined', namespace='/comms')
def party(data):
    if 'current party' not in session:
        session['current party'] = 0
    if data == "__self__":
        print("creating party for ", session['user'])
        create_party(session["user"])


def get_party_leader(username):
    if username == "Admin":
        return "Admin"
    a = db['ex'].get('users', 'current_party', condition=f'username="{username}"')
    if a and a not in ["" " "]:
        return a[0]
    else:
        return None


def set_user_location(username, lat, lng):
    if username == "Admin":
        return
    connected_members[username]["loc"] = (lat, lng)
    db['ex'].set_user_location(username, f"{lat}, {lng}")


@socketio.on('my_location', namespace='/comms')
def my_location(data):
    set_user_location(session['user'], data[0], data[1])
    if connected_members[session['user']]['current_path'][1]:
        connected_members[session['user']]['current_path'][1] = data[2]

    recipients = get_party_members(session['user']) + ["Admin"]
    [emit_to(member, 'my_location', message=[session['user'], [data[0], data[1]]]) for member in
     recipients]

    send_path_to_party(session['user'])

    # emit_to("Admin", 'my_location', message=[session['user'], data[0], data[1]])


@socketio.on('in_progress', namespace='/comms')
def in_progress():
    # path_coords = []
    # myroute = data["legs"][0]
    # for step in myroute["steps"]:
    #     for coords in step["path"]:
    #         path_coords.append((coords["lat"], coords["lng"]))

    sessionuser = session['user']
    leader = get_party_leader(sessionuser)
    if db['ex'].get_party_status(leader) == "no current request":
        db['ex'].set_party_status(leader, "in progress")
        print('starting new request')

    # # simulation
    # for coords in path_coords:
    #     if db['ex'].get_party_status(leader) == "halt":
    #         print('halting')
    #         break
    #
    #     lat, lng = coords
    #     # set_user_location(leader, lat, lng)
    #     connected_members[leader]["loc"] = (lat, lng)
    #
    #     data = [False, [(member, connected_members[member]["loc"]) for member in get_party_members(sessionuser)]]
    #
    #     [emit_to(member, 'party_member_coords', '/comms',
    #              message=data) for member in get_party_members(session['user'])]
    #
    #     sleep(0.1)
    #
    # lat, lng = connected_members[leader]["loc"]
    # set_user_location(leader, lat, lng)
    # db['ex'].set_party_status(leader, "no current request")


@socketio.on('left_party', namespace='/comms')
def party(data):
    if 'current party' not in session:
        session['current party'] = 0
    if data == "__self__":
        leader = get_party_leader(session['user'])
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
    for user in db["ex"].get("users", "username"):
        if user == "Admin":
            continue
        # interests = db["ex"].get("users", "interests", f'username="{user}"')[0].strip()
        lat, lng = [float(x) for x in db["ex"].get("users", "loc", f'username="{user}"')[0].split(", ")]
        db['ex'].set_user_location(user, f"{lat}, {lng}")
        interests_list = ["sport", "theater", "computer", "park", "restaurant"]
        interests_dict = {}
        for i in interests_list:
            interests_dict[i] = np.random.random_sample() * 5

        interests = "|".join([f"{i}|{interests_dict[i]}" for i in interests_list])
        db['ex'].edit("users", "interests", newvalue=interests, condition=f'username="{user}"')
        vls[user] = [float(x) for x in interests.split("|")[1::2]] + [lat / 30, lng / 30]

    # vls["__ideal_restaurant"] = np.array([3, 4, 2, 3, 5, None, None])
    # vls["__ideal_park"] = np.array([4, 2, 1, 5, 2, None, None])

    knn = KNN(vls=vls, k=3)
    db["knn"] = knn

    socketio.run(app, host="0.0.0.0", port=8080)
