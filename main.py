import os
import random
from time import time
import numpy as np
from engineio.payload import Payload
from flask import *
from flask_socketio import SocketIO, emit
import re
from get_query_results import query
import database_wrapper
from database_wrapper import smallest_free
from KNN import distance, category_values, get_color
import threading
# import pymongo

Payload.max_decode_packets = 1000
__author__ = 'Rock'
last_time_pings_checked = time()

# all parties
parties = {}

# delete chat queue
delete_chats = {}

# currently connected members and their data
connected_members = {}

# colors of online users
online_user_colors = {}

# lmao will probably be used at some point
points_of_interest = {}

# ??? probably not used
user_data = {}

# party location suggestion voting process
voting_status = {}

# everyone's color incase they disconnect or whatev
user_colors = {}

# keep track of notifications so we can
# notify the user properly
user_notification_tracking = {}

# party creation suggestions
party_suggestions = {}

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



def filter_dict(d, f):
    """ Filters dictionary d by function f. """
    new_dict = dict()

    # Iterate over all (k,v) pairs in names
    for key, value in d.items():

        # Is condition satisfied?
        if f(key):
            new_dict[key] = value

    return new_dict.copy()


def parse_chat_command(command):
    try:
        args = command[1:].split(" ")

        if len(args) > 1:
            cmd, arguments = args[0], args[1:]
        else:
            cmd, arguments = args[0], []

        if cmd == "vote":
            party_owner = get_party_leader(session['user'])
            vote_status = parties[party_owner]["votes"]
            decision = arguments[0].lower() in ["yes", "y"]
            vote_status[session["user"]] = decision
            votes_required = int(len(parties[party_owner]["members"])/2)+1
            send_message_to_party(party_owner, message=f'{session["user"]} has voted {"Yes" if decision else "No"}. '
                                                       f'({len(vote_status.keys())}/'
                                                       f'{votes_required})')

            # A majority has voted to some either go or not go
            voted_yes = [name for name in vote_status if vote_status[name]]
            voted_no = [name for name in vote_status if not vote_status[name]]

            # Vote has resulted in rejecting the sever's suggestion
            if votes_required == voted_no:
                send_message_to_party(session['user'],
                                      message=f"{votes_required} people have voted NO.")

            if votes_required == voted_yes:
                update_destination(parties[party_owner]["destination"], session['user'])
                send_message_to_party(session['user'],
                                      message=f"{votes_required} people have voted YES.<br>"
                                              f"Calculating route...")

        if cmd == "sug":
            # lat, lng = get_location_request(session['user'])
            location = {"name": "De-Shalit High-school", "lat": 31.89961596028198, "lng": 34.816320411774875}
            emit_to_party(session['user'], event_name='location_suggestion', message=[location])
            send_message_to_party(session['user'],
                                  message=f"How about < {location['name']} > ?  Vote now! (/vote y) ")

        if cmd == "leave_group":
            disconnect_user_from_party(session['user'])

        if cmd == "disband":
            if session['user'] == get_party_leader(session['user']):
                chat_id = get_party_chat_id(session['user'])
                # First disconnect everyone else
                emit_to_party(session['user'], event_name="update_party_members", namespace="/comms", message=[])
                # Get party members
                users_without_admin = get_party_members(session['user'])
                # Remove admin
                users_without_admin.remove(session['user'])
                # Disconnect everyone else
                [disconnect_user_from_party(u) for u in users_without_admin]
                # Then disconnect you
                disconnect_user_from_party(session['user'])
                # Not a trace ....
                del parties[session['user']]
                del chatrooms[chat_id]

    except Exception as e:
        return "Error", e
    else:
        return "Success"


def emit_to_everyone(**kwargs):
    [emit_to(user=m, **kwargs) for m in connected_members]


def emit_to_party(member, **kwargs):
    members = get_party_members(member)
    print(members, f"{kwargs}")
    [emit_to(user=m, **kwargs) for m in members]


def random_location():
    return random.uniform(31.8884302, 31.9043486), random.uniform(34.8025995, 34.8146395)


def get_party_members(username):
    owner = get_party_leader(username)
    if owner not in parties:
        return []
    return parties[owner]["members"].copy()
    # return db['ex'].get_party_members(
    #     owner=get_party_leader(username))


def create_party(user, members=None):
    if members is None:
        members = []
    members = [user]+members
    parties[user] = {"status": "Not Decided", "destination": None, "locations": {}, "votes": {}, "chat_id": None,
                     "members": members, "lock": threading.Lock()}
    voting_status[get_party_leader(user)] = {}
    for m in members:
        voting_status[get_party_leader(user)][m] = False
        # db['ex'].add_to_party(owner=user, user_to_add=m)
    chat_id = create_chat(name="Party", members=members)

    for m in members:
        chatrooms[chat_id]["members"][m] = False

    # db['ex'].create_party(user, chat_id=chat_id)
    print(f"created party for {members}")
    return chat_id


def join_party(owner, username):
    parties[owner]["members"].append(username)
    party_coords(owner, False)
    chatrooms[parties[owner]["chat_id"]]["members"][username] = False
    # db['ex'].add_to_party(owner=owner, user_to_add=username)


def disconnect_user_from_party(user, chat_is_disbanded=False):
    # Get current leader
    current_leader = get_party_leader(user)
    # Get party members
    all_members = get_party_members(current_leader)
    print('disconnecting', user, 'from', current_leader)

    # Send message to party, announcing the user that left
    send_message_to_party(current_leader, f"{user} left!")

    # If user leaving is the leader
    if current_leader == user:
        if len(all_members) == 1:
            # Disband party, kick last user
            chat_is_disbanded = True
        else:
            print("Not disbanded")
            # Remove user from members
            all_members.remove(user)
            # Pick new leader
            new_leader = all_members[0]
            # Copy over the party data to entry
            # On new leader's name
            parties[new_leader] = parties[user].copy()
            # Remove the user from the new party
            parties[new_leader].remove(user)
            print(parties[new_leader])
            # Send update message to party about the new leader
            send_message_to_party(new_leader, f"{new_leader} is now the party leader")
            # Change current_leader to the new leader
            current_leader = new_leader
            emit_to(user, event_name="update_party_members", namespace="/comms", message=[])

    # If the chat is disbanded
    if chat_is_disbanded:
        # Update leader's party members to an empty array
        emit_to(current_leader, event_name="update_party_members", namespace="/comms", message=[])

        # Add chat_id to delete queue
        if user not in delete_chats:
            delete_chats[user] = [get_party_chat_id(current_leader)]
        else:
            delete_chats[user].append(get_party_chat_id(current_leader))

        # delete chatroom
        del chatrooms[get_party_chat_id(current_leader)]
        # delete party entry
        del parties[current_leader]
    else:
        # Not disbanded, keep the chatroom and party entry
        # Add chat_id to delete chat queue
        if user not in delete_chats:
            delete_chats[user] = [get_party_chat_id(current_leader)]
        else:
            delete_chats[user].append(get_party_chat_id(current_leader))

        # Remove user from party members
        parties[current_leader]["members"].remove(user)
        # Send to remaining party to update member list
        members = get_party_members(current_leader)
        emit_to_party(current_leader, event_name="update_party_members", namespace="/comms", message=members)
        # Send path to delete the old one from the now-gone user
        send_path_to_party(current_leader)


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


def get_party_chat_id(user):
    return parties[get_party_leader(user)]["chat_id"]


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
        # db['ex'].add_notif(requester)

        # emit_to(requester, 'notif', '/comms', 'notification!')

    if command_name == "join_party":
        party_owner = args[1]
        if len(get_party_members(party_owner)) == 0:
            create_party(party_owner, members=[session['user']])
        else:
            join_party(party_owner, session['user'])

        # [emit_to(user=party_member, event_name="party_members_list_get",
        #          message=get_party_members(party_owner))
        #  for party_member in get_party_members(party_owner)]
        emit_to_party(party_owner, event_name="party_members_list_get", message=get_party_members(party_owner))
        # print("joined party", get_party_members(session['user']))

    if command_name == "accept_suggestion":
        try:
            party_owner = \
                [owner for owner in party_suggestions if session['user'] in party_suggestions[owner]["total"]][0]
            if len(get_party_members(party_owner)) == 0:
                create_party(party_owner, members=[session['user']])
            else:
                get_party_chat_id(party_owner)
                join_party(party_owner, session['user'])

            PSP = party_suggestions[party_owner]
            PSP["accepted"].append(session['user'])
            emit_to(party_owner, event_name='can_start_vote')
            # if len(PSP["accepted"]) + len(PSP["rejected"]) == len(PSP["total"]):
            #     emit_to(party_owner, event_name='can_start_vote')
        except IndexError:
            print('lol sucks for u')

    if command_name == "reject_suggestion":
        party_owner = [owner for owner in party_suggestions if session['user'] in party_suggestions[owner]["total"]][0]
        PSP = party_suggestions[party_owner]
        PSP["accepted"].append(session['user'])


@app.route("/inbox", methods=["POST", "GET"])
def inbox():
    if "user" not in session:
        return redirect(url_for("register"))

    try:
        db['ex'].reset_notifs(session['user'])
    except KeyError:
        pass

    if request.method == "POST":
        message_id = request.form['message_id']
        reaction = request.form['action']
        # first grab the message to see what we need to do with it
        _id, title, content, sender, receiver, msg_type, action = \
            db['ex'].get('messages', '*', f'id={message_id}', first=False)[0]
        print(f"{reaction}: {title} | {msg_type}")
        if reaction != "ignore":
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


def emit_to(user: str, event_name: str, namespace: str = '/comms', message=None, verbose=True):
    try:
        # a = 'chat_socket' if chat else 'sid'
        emit(event_name, message, namespace=namespace, room=connected_members[user]['sid'])
        if verbose:
            print(f"Sent to {user}: {event_name} {message} {namespace} ")
    except Exception as e:
        print(f'Error in emitting to user {user},', e)
        print(f'Tried to send: ', message, event_name)


@app.route("/", methods=["POST", "GET"])
def main_page():
    session["time"] = int(time())
    # If user is not logged in
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

    visible_users = [x for x in connected_members if x != "Admin"]

    session["friend_data"] = {'online': [friend for friend in fr if friend in visible_users],
                              'offline': [friend for friend in fr if friend not in visible_users]}

    emit_to(session["user"], 'friend_data', message=session["friend_data"])
    # [emit_to(us, 'user_diff',
    #          message=visisble_uses) for us in
    #  connected_members]
    emit_to_everyone(event_name='user_diff', message=visible_users)
    emit_to("Admin", "all_users", message={u: u in connected_members for u in db["ex"].get_all_names()})
    print("Data:")
    print("\n".join([f"{name}, {int(time()) - connected_members[name]['last ping']}" for name in visible_users]))
    print({'amount': len(connected_members.keys()), 'names': [user for user in connected_members]})


def update_destination(data, user):
    leader = get_party_leader(user)
    parties[leader]["destination"] = data
    parties[leader]["status"] = "Has Destination"
    emit_to_party(session['user'], event_name='update_destination', message=data)


@socketio.on('request_destination_update', namespace='/comms')
def destination_update_request(data):
    update_destination(data, session['user'])


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

    parties[get_party_leader(session['user'])]["destination"] = coords

    # [emit_to(user=party_m, event_name='update_destination',
    #          message=coords)
    #  for party_m in get_party_members(session['user']) if party_m in connected_members]
    emit_to_party(session['user'], event_name='update_destination', message=coords)


@socketio.on('ping', namespace='/comms')
def check_ping(*args):
    global last_time_pings_checked
    user = None
    for member in connected_members:
        if connected_members[member]["sid"] == request.sid:
            user = member
    if not user:
        return
    # print(f"ponged by {user}, {user} sees: {' '.join(args[0])}")
    connected_members[user]["last ping"] = int(time())
    # # # # #
    if time() - last_time_pings_checked > 2:
        for username in connected_members.copy():
            if int(time()) - connected_members[username]["last ping"] > 2:
                del connected_members[username]
                broadcast_userdiff()
        last_time_pings_checked = time()

    send_path_to_party(session['user'])

    if session['user'] == "Admin":
        members = connected_members
        for member in members:
            if member == "Admin":
                continue

            lat, lng = db['ex'].get_user_location(member)
            emit_to("Admin", 'my_location', message=[member, [lat, lng]])

        online_user_colors = {v: k for (v, k) in user_colors.items() if v in connected_members}
        if online_user_colors:
            emit_to("Admin", event_name="user_colors", message=online_user_colors)

    # notif_amount = db['ex'].get_notifs(session['user'])
    # emit_to(session['user'], event_name="notifications",
    #         message=notif_amount)

    messages = db['ex'].get_messages(user=session['user'])["messages"]
    message_amount = len(messages)
    # emit_to(session['user'], event_name="inbox_update", message=[message_amount, messages])
    if session['user'] not in user_notification_tracking:
        user_notification_tracking[session['user']] = message_amount
        emit_to(session['user'], event_name="inbox_update", message=[message_amount, messages])
    else:
        if message_amount != user_notification_tracking[session['user']]:
            emit_to(session['user'], event_name="inbox_update", message=[message_amount, messages])
            user_notification_tracking[session['user']] = message_amount

    if session['user'] != "Admin":

        # CREATE CHATS that have not yet been confirmed by the client
        # run over all chats user should have, and check if they've been
        # confirmed.
        [emit_to(session['user'], "create_chat", message=room)
         for room
         in get_all_user_chats(session['user'])
         if not chatrooms[room["id"]]["members"][session['user']]]

        # DELETE CHATS that need to be deleted, them remove them from
        # the deletion queue. repeats until confirmed by user.
        if session['user'] in delete_chats:
            [emit_to(session['user'], event_name="del_chat", message=chat_id)
             for chat_id
             in delete_chats[session['user']]]


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


def send_message_to_party(member, message, author="(System)"):
    chat_id = get_party_chat_id(member)
    emit_to_party(member, event_name="message",
                  message={"id": chat_id, "message": message, "author": author})


def send_path_to_party(user_to_track):
    party_members = get_party_members(user_to_track)
    party_leader = get_party_leader(user_to_track)
    if len(party_members) == 0:
        return
    paths = []
    if parties[party_leader]["status"] == "Reached Destination":
        return
    done = True
    for member in party_members:
        if member != user_to_track and member in connected_members:
            try:
                path, index = connected_members[member]['current_path']
                paths.append((member, [connected_members[member]['loc']] + path[index:]))
                destination = path[-1]
                meters = 5
                min_distance = meters * 0.0000089  # convert to lng/lat scale
                print(min_distance, distance(destination, path[index]))
                if distance(destination, path[index]) > min_distance:
                    done = False
                print(f"Adding path from {member}[:{index}], sending to {user_to_track} ({party_members})")
            except Exception as e:
                print(f"Error in drawing path from {member} on {session['user']}'s screen | {e}")
    emit_to(session["user"], 'user_paths', message=paths)
    emit_to("Admin", 'user_paths', message=paths)

    # all the paths are dones
    if done and len(party_members) > 1 and parties[party_leader]["status"] != "Reached Destination":
        parties[party_leader]["status"] = "Reached Destination"
        # online party members in order
        list_of_priorities = [x for x in party_members if x in connected_members]
        if session['user'] == list_of_priorities[0]:
            db['ex'].send_message(title=f"Party Reached Destination",
                                  desc=f"{party_leader}'s party has reached their destination.",
                                  sender="[System]", receiver="Admin", messagetype="ignore",
                                  action=None)


@socketio.on('send_current_path', namespace='/comms')
def return_path(data):
    # # # # # # # # # # # # # # # # # # # # # # # # # # #.data, step_index
    connected_members[session['user']]['current_path'] = [data, 0]
    print(f"Received path from {session['user']}")
    # send_path_to_party(user_to_track=session['user'])
    # print(json.dumps(connected_members[session['user']]))


@socketio.on('send_dest', namespace='/comms')
def return_path(data):
    # # # # # # # # # # # # # # # # # # # # # # # # # # #
    parties[get_party_leader(session['user'])]["location"] = data
    # send_path_to_party(user_to_track=session['user'])
    # print(json.dumps(connected_members[session['user']]))


def try_reset_first(user):
    try:
        route, lng = connected_members[user]['current_path']
        if route is None:
            emit_to(user, 'reset_first')
            return
        if lng >= len(route):
            emit_to(user, 'reset_first')
    except KeyError:
        pass


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
    data = [request_directions, data]
    # [emit_to(member, event_name='party_member_coords', namespace= '/comms',
    #          message=data) for member in members if member in connected_members]
    emit_to("Admin", event_name='party_member_coords', namespace='/comms', message=data)
    emit_to_party(username, event_name='party_member_coords', namespace='/comms', message=data)


@socketio.on('get_coords_of_party', namespace='/comms')
def get_coords_of_party():
    if session['user'] == "Admin":
        members = db['ex'].get_all_names(remove_admin=True)
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


chatrooms = {"0": {"name": "Global", "history": [], "members": {}, "type": "global"}}


def get_all_user_chats(target):
    return [{"id": room, **chatrooms[room]} for room in chatrooms if target in list(chatrooms[room]["members"].keys())]


@socketio.on('inbox_notification_react', namespace='/comms')
def notification_parse(data):
    message_id, reaction = data["message_id"], data["reaction"]

    # first grab the message to see what we need to do with it
    _id, title, content, sender, receiver, msg_type, action = \
        db['ex'].get('messages', '*', f'id={message_id}', first=False)[0]
    print(f"{reaction}: {title} | {msg_type}")
    if reaction != "mark_as_read":
        parse_action(action)
        db['ex'].remove("messages", f'id={message_id}')
    session['inbox_messages'] = get_messages(session['user'])


def create_chat(*, name, members=None, chat_type="party"):
    if members is None:
        members = []
    smallest_free_chat_id = str(smallest_free(list(chatrooms.keys())))
    if members:
        parties[members[0]]["chat_id"] = smallest_free_chat_id
    chatrooms[smallest_free_chat_id] = {"name": name, "members": {m: False for m in members}, "history": [], "type": chat_type}
    return smallest_free_chat_id


@socketio.on('confirm_chat', namespace='/comms')
def confirm_chat(chat_id):
    chatrooms[chat_id]["members"][session['user']] = True


@socketio.on('confirm_del_chat', namespace='/comms')
def confirm_delete_chat(chat_id):
    try:
        delete_chats[session['user']].remove(chat_id)
    except KeyError:
        pass


@socketio.on('connect', namespace='/comms')
def logged_on_users():
    # request.sid
    if 'user' not in session:
        return redirect(url_for("login"))
    # reconnecting = session['user'] in connected_members
    chatrooms["0"]["members"][session['user']] = False
    for chat_id in get_all_user_chats(session['user']):
        chatrooms[chat_id["id"]]["members"][session['user']] = False

    connected_members[session['user']] = {
        "last ping": int(time()),
        "remote addr": request.remote_addr,
        "sid": request.sid,
        "loc": [0, 0],
        "current_path": [None, None],
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

    user_notification_tracking[session['user']] = 0

    if session['user'] != "Admin":
        [emit_to(session['user'], "create_chat", message=room) for room in get_all_user_chats(session['user'])]
        emit_to(session['user'], "message",
                message={"id": "0", "message": "Welcome!", "author": "(System)"})
    else:
        members = db['ex'].get_all_names(remove_admin=True)
        for member in members:
            lat, lng = db['ex'].get_user_location(member)
            emit_to("Admin", 'my_location', message=[member, [lat, lng]])

    # Get all users that are online,
    # not in a group, and have not
    # received a suggestion from the server
    # (have an active suggestion)
    def group_suggestion_filter(u):
        # Check if user is in a suggestion list
        for leader in party_suggestions:
            if u in party_suggestions[leader]["total"]:
                return False
        # If user has a party return false
        if get_party_leader(u):
            return False
        # Return true, user fits qualifications
        return True

    dont_have_suggestions = filter_dict(d=connected_members, f=group_suggestion_filter)
    if len(dont_have_suggestions) > 1:
        suggestion_groups = knn.find_optimal_clusters(
            only_these_values=filter_dict(db["knn"].values, lambda x: x in dont_have_suggestions),
            verbose=False
        )
        for center in suggestion_groups:
            names = [person[0] for person in suggestion_groups[center]]
            for name in names:
                user_colors[name] = get_color(name, suggestion_groups)
            suggest_party(names, knn.find_best_category(names, category_values))
        online_user_colors = {v: k for (v, k) in user_colors.items() if v in connected_members}


@socketio.on('party_members_list_get', namespace='/comms')
def get_party_memb():
    emit_to(user=session['user'], event_name="party_members_list_get",
            message=get_party_members(session['user']))


@socketio.on('online_members_get', namespace='/comms')
def get_online_memb():
    emit_to(user=session['user'], event_name="online_members_get",
            message=[x for x in connected_members if x != "Admin"])


# @socketio.on('user_added_locations_get', namespace='/comms')
# def get_user_added_loc():
#     data = [
#         # a[0] = NAME: STR
#         # a[1] = LAT, LNG: STR
#         # a[2] = TYPE: STR
#         (a[0], [float(x) for x in a[1].split(", ")], a[2])
#         for a in db['ex'].get_user_added_locations()
#     ]
#     emit_to(user=session['user'], event_name="user_added_locations",
#             message=data)


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

    for party_leader in parties:
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
            for x in db['ex'].get_all_names(remove_admin=True)]
    ]

    try:
        for member in connected_members:
            if member != "Admin":
                emit_to(member, 'party_member_coords',
                        message=party_data[get_party_leader(member)])

    except KeyError:
        print("Error KEYERROR 788 reset locations")


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

    # [emit_to(user=user, event_name="best_3_locations", message=best_3)
    #  for user in connected_members]

    emit_to_everyone(event_name="best_3_locations", message=best_3)


@socketio.on('disconnect', namespace='/comms')
def disconnect_event():
    # broadcast_userdiff()
    pass


@socketio.on('invite_user', namespace='/comms')
def invite_user(receiver):
    print("inviting", receiver)
    if receiver == session['user']:
        return
    # user has no party, this creates it.
    # print(123, get_party_members(session['user']))
    db['ex'].send_message(title=f"Party invite from {session['user']}!",
                          desc=f"{session['user']} has invited you to join their party, wanna hang out?",
                          sender=session["user"], receiver=receiver, messagetype="question",
                          action=f"join_party/{session['user']}")
    # db['ex'].add_notif(receiver)
    # emit_to(receiver, 'notif', namespace='/comms', message='notification!')


def suggest_party(users, place_type):
    print(f"creating party for {users}")
    party_suggestions[users[0]] = {"total": users, "accepted": [], "rejected": [], "place_type": place_type}
    for u in users:
        u_list = users.copy()
        u_list.remove(u)
        desc = f"The system has invited you to join a party with {', '.join(u_list[:-1])}, and {u_list[-1]}" if len(
            u_list) > 1 else \
            f"The system has invited you to join a party with {u_list[0]}"
        db['ex'].send_message(title=f"Party suggestion!",
                              desc=desc,
                              sender="Admin", receiver=u, messagetype="group_suggestion",
                              action=f"accept_suggestion/{users[0]}")

        # emit_to(u, 'notif', namespace='/comms', message='notification!')


@socketio.on('add_location', namespace='/comms')
def add_location_func(data):
    name, lat, lngm, loc_type = data.split(", ")
    db['ex'].add_location(name, lat, lng, loc_type)
    [send_user_added_locations(online_user) for online_user in connected_members]


@socketio.on('get_destination', namespace='/comms')
def get_destination():
    if session['user'] == "Admin":
        return
    try:
        if parties[get_party_leader(session['user'])]["destination"] is None:
            raise ValueError
        emit_to(session['user'], event_name='update_destination',
                message=parties[get_party_leader(session['user'])]["destination"])
    except:
        pass


def get_party_leader(username):
    if username == "Admin":
        return "Admin"

    a = [person for person in parties if username in parties[person]["members"]]
    if a:
        return a[0]
    else:
        return None
    # a = db['ex'].get('users', 'current_party', condition=f'username="{username}"')
    # if a and a not in ["" " "]:
    #     return a[0]
    # else:
    #     return None


def set_user_location(username, lat, lng):
    if username == "Admin":
        return
    connected_members[username]["loc"] = (lat, lng)
    db['ex'].set_user_location(username, f"{lat}, {lng}")


@socketio.on('chat_message', namespace='/comms')
def chat_message(data):
    """
    Multicast message from user to
    appropriate chat
    """
    room, message, author = data["room"], data["message"], session['user']
    chatrooms[room]["history"].append(message)
    room_members = list(chatrooms[room]["members"].keys())

    for member in room_members:
        emit_to(member, 'message', message={
            "id": room,
            "author": author,
            "message": message
        })
    if message[0] == "/":
        parse_chat_command(message)

@socketio.on('my_location', namespace='/comms')
def my_location(data):
    set_user_location(session['user'], data[0], data[1])
    if connected_members[session['user']]['current_path'][1]:
        connected_members[session['user']]['current_path'][1] = data[2]

    # recipients = get_party_members(session['user']) + ["Admin"]
    # [emit_to(member, event_name='my_location', message=[session['user'], [data[0], data[1]]]) for member in
    #  recipients]
    emit_to("Admin", event_name='my_location', message=[session['user'], [data[0], data[1]]])
    emit_to_party(session['user'], event_name='my_location', message=[session['user'], [data[0], data[1]]])
    send_path_to_party(session['user'])


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
        # interests_list = ["sport", "theater", "computer", "park", "restaurant"]
        # interests_dict = {}
        # for i in interests_list:
        #     interests_dict[i] = np.random.random_sample() * 5
        #
        interests = db['ex'].get("users", "interests", condition=f'username="{user}"')[0]
        # db['ex'].edit("users", "interests", newvalue=interests, condition=f'username="{user}"')
        # vls[user] = [lat, lng]
        # + [lat / 25, lng / 25]
        vls[user] = [float(x) for x in interests.split("|")[1::2]]

    # vls["__ideal_restaurant"] = np.array([3, 4, 2, 3, 5, None, None])
    # vls["__ideal_park"] = np.array([4, 2, 1, 5, 2, None, None])

    knn = KNN(vls=vls, k=3)
    db["knn"] = knn

    socketio.run(app, host="0.0.0.0", port=8080)
