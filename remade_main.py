# general use modules
from time import time
import numpy as np

from engineio.payload import Payload

# flask modules
from flask import *
from flask_socketio import SocketIO, emit

# my modules / warppers
from get_query_results import find_places
from database_wrapper import smallest_free
from database_wrapper import my_db as database
from kmeans_wrapper import category_values, KMEANS

Payload.max_decode_packets = 50

chat_rooms = {"0": {"name": "Global", "history": [], "members": {}, "type": "global"}}
"""
chat_rooms[id] = {
                  "name": str,
                  "members": {name: confirmed(bool), name: confirmed(bool), ...},
                  "history" : [
                               {"author": name, "message": message},
                               ... 
                              ]
                }
"""

delete_chats_queue = {}
"""
delete_chats_queue = {
                        user: [chat_id, ...],
                        ...
                     }
"""

members = {}
"""
members[name] = {
                 "sid": // # the socket sid
                 "loc": [lat, lng],
                 "current_path": [path, index],
                 "party": name # (party owner's name),
                 "last ping": time_now(),
                 "chats": [chat_id, ...]
                }
When a user comes back online we can restore their data
from this dictionary, and update their socket SID
"""
# Subset of members that are online.
connected_members = {}

parties = {}
"""
parties[party_owner] = {
                        "members: [member, ...],
                        "destination": [lat, lng] | None
                        "vote_status": {"suggested_location": [lat, lng] | None,
                                        "during_vote": False, 
                                        "voted_yes": [member, ...],
                                        "voted_no":  [member, ...]
                                        }
                        "destination_status": "No Destination" | "Have Destination" | "Reached Destination",
                        "arrived": []
                       }
"""

party_suggestions = {}
"""
party_suggestions[party_owner] = {
                                  "members": [member, ...],                        
                                  }

"""


def filter_dict(d, f):
    """ Filters dictionary d by function f. """
    new_dict = dict()

    # Iterate over all (k,v) pairs in names
    for key, value in d.items():

        # Is condition satisfied?
        if f(key):
            new_dict[key] = value

    return new_dict.copy()


def get_all_user_chats(target):
    return [{"id": room, **chat_rooms[room]}
            for room in connected_members[target]["chats"]]


def suggest_party(users):
    print(f"suggesting party for {users}")
    party_suggestions[users[0]] = {"total": users, "accepted": [], "rejected": []}
    for u in users:
        u_list = users.copy()
        u_list.remove(u)
        base = "The system has invited you to join a party"
        addition = f"with {', '.join(u_list[:-1])}, and {u_list[-1]}" if len(u_list) > 1 else f"with {u_list[0]}"
        desc = f"{base} {addition}"
        database.send_message(title=f"Party suggestion! {addition}",
                              desc=desc,
                              sender="Admin", receiver=u, messagetype="group_suggestion",
                              action=f"accept_suggestion/{users[0]}")


def get_place_recommendation_location(tp, radius, limit):
    radius = float(radius) * 1000
    limit = int(limit)

    middle_lat, middle_lng = sum(
        [connected_members[member]["loc"][0] for member in get_party_members(session['user']) if
         member in connected_members]) / len(get_party_members(session['user'])), \
                             sum([connected_members[member]["loc"][1] for member in get_party_members(session['user'])
                                  if member in connected_members]) / len(get_party_members(session['user']))
    middle = middle_lat, middle_lng

    results_json = find_places(middle, radius, tp, limit)

    return results_json


def create_chat(*, name: str, party_members: list = None) -> str:
    smallest_free_chat_id = str(smallest_free(list(chat_rooms.keys())))

    parties[party_members[0]]["chat_id"] = smallest_free_chat_id
    chat_rooms[smallest_free_chat_id] = {"name": name,
                                         "members": {m: False for m in party_members},
                                         "history": []}

    for member in party_members:
        connected_members[member]["chats"].append(smallest_free_chat_id)

    return smallest_free_chat_id


def separate_into_colours(group_owners):
    colors = ['green', 'orange', 'fuchsia', 'magenta', 'olive', 'teal', 'violet',
             'skyblue', 'gray', 'darkorange', 'cyan', 'royal_blue']
    colors_amount = len(colors)
    ret = []
    for i, g in enumerate(sorted(group_owners)):
        ret.append((colors[i % colors_amount], parties[g]["members"]))
    return ret


def create_party(user, members_to_add=None):
    if members_to_add is None:
        members_to_add = []
    party_members = [user] + members_to_add
    """
parties[party_owner] = {
                        "members: [member, ...],
                        "destination": [lat, lng] | None
                        "vote_status": {"suggested_location": [lat, lng] | None,
                                        "during_vote": False, 
                                        "voted_yes": [member, ...],
                                        "voted_no":  [member, ...]
                                        }
                        "destination_status": "No Destination" | "Have Destination" | "Reached Destination",
                        "arrived": []
                       }
    """
    parties[user] = {
        "members": party_members,
        "destination": None,
        "vote_status": {
            "suggested_location": None,
            "during_vote": False,
            "voted_yes": [],
            "voted_no": []
        },
        "destination_status": "No Destination",
        "arrived": []
    }

    for m in party_members:
        connected_members[m]['party'] = user
        database.add_to_party(owner=user, user_to_add=m)

    chat_id = create_chat(name="Party", party_members=party_members)

    emit_to(user=session['user'], event_name="party_members_list_get",
            message=get_party_members(session['user']))
    print(f"created party for {party_members} ID:{chat_id}")
    return chat_id


def time_now():
    return int(time())


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True, async_handlers=True)


def get_party_leader(username):
    if username == "Admin":
        return "Admin"

    # a = [person for person in parties if username in parties[person]["members"]]
    return connected_members[username]["party"]


def get_messages(user):
    info = database.get_messages()
    if user in info:
        return [[message['id'], message['title'], message['content'], message['sender'], message['type']]
                for message in info['messages'][session['user']]]
    return []


def get_party_members(username):
    owner = get_party_leader(username)
    print("party members", owner, username)
    if owner not in parties:
        return []
    return parties[owner]["members"].copy()


def split_interests(input_str):
    return [float(x) for x in input_str.split("|")[1::2]]


def prepare_kmeans_values():
    users_and_interests = database.get(table="users",
                                       column="username,interests",
                                       first=False)

    vls = {username: split_interests(interests) for
           username, interests in users_and_interests}

    return vls


kmeans = KMEANS(vls=prepare_kmeans_values(), k=3)

"""
HELPER FUNCTIONS FOR EMITTING (SOCKET.IO) PURPOSES
"""


def emit_to(user: str, event_name: str, message=None, namespace: str = '/comms', verbose=True):
    try:
        emit(event_name, message, namespace=namespace, room=members[user]['sid'])
        if verbose:
            print(f"Sent to data: {user}: {event_name} {message} {namespace} ")
    except Exception as e:
        print(f'Error in emitting to user {user},', e)
        print(f'Tried to send: ', event_name, message)


def emit_to_everyone(**kwargs):
    [emit_to(user=m, **kwargs) for m in connected_members]


def emit_to_party(member, **kwargs):
    party_members = get_party_members(member)
    [emit_to(user=m, **kwargs) for m in party_members]


def send_user_added_locations(username):
    data = [(name, [float(value) for value in latlng.split(", ")], location_type)
            for name, latlng, location_type in database.get_user_added_locations()]
    emit_to(username, 'user_added_locations', message=data)


def party_coords(username):
    if username is None:
        return

    party_members = get_party_members(username)
    data = []

    for member in party_members:
        try:
            lat, lng = members[member]["loc"]
            data.append({"name": member,
                         "lat": lat, "lng": lng,
                         "is_online": member in connected_members})
        except Exception as e:
            print("get coords error", e, members)

    if data:
        emit_to_party(username, event_name='party_member_coords', namespace='/comms', message=data)


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
            parties[new_leader]['members'].remove(user)
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
        if user not in delete_chats_queue:
            delete_chats_queue[user] = [get_party_chat_id(current_leader)]
        else:
            delete_chats_queue[user].append(get_party_chat_id(current_leader))

        # delete chatroom
        del delete_chats_queue[get_party_chat_id(current_leader)]
        # delete party entry
        del parties[current_leader]
    else:
        # Not disbanded, keep the chatroom and party entry
        # Add chat_id to delete chat queue
        if user not in delete_chats_queue:
            delete_chats_queue[user] = [get_party_chat_id(current_leader)]
        else:
            delete_chats_queue[user].append(get_party_chat_id(current_leader))

        # Remove user from party members
        try:
            parties[current_leader]["members"].remove(user)
        except (ValueError, KeyError):
            print("already removed :)")
        # Send to remaining party to update member list
        members = get_party_members(current_leader)
        emit_to_party(current_leader, event_name="update_party_members", namespace="/comms", message=members)

    connected_members[user]["party"] = None
    emit_to(user, event_name="reset_markers")


def update_destination(data, user):
    leader = get_party_leader(user)
    if not leader:
        return
    parties[leader]["destination"] = data
    parties[leader]["destination_status"] = "Has Destination"
    parties[leader]["arrived"] = []
    lat, lng = data
    emit_to_party(user, event_name='update_destination',
                  message={"lat": lat, "lng": lng})


def start_vote_on_place(leader, location_data):
    parties[leader]["in_vote"] = True
    parties[leader]["votes"] = {}
    parties[leader]["destination"] = [location_data["lat"], location_data["lng"]]
    send_message_to_party(session['user'],
                          message=f"How about < {location_data['name']} > ?  Vote now! (/vote y) ")
    emit_to_party(leader, event_name='location_suggestion', message=location_data)


def parse_chat_command(command, chat_id):
    # try:
    args = command[1:].split(" ")

    in_party_chat = chat_id == get_party_chat_id(session['user'])
    print(2020, in_party_chat, args)
    if len(args) > 1:
        cmd, arguments = args[0], args[1:]
    else:
        cmd, arguments = args[0], []

    if cmd == "vote" and in_party_chat:

        party_owner = get_party_leader(session['user'])
        vote_status = parties[party_owner]["votes"]
        if session["user"] in vote_status or not parties[party_owner]["in_vote"]:
            # already voted
            return

        decision = arguments[0].lower() in ["yes", "y"]
        vote_status[session["user"]] = decision
        votes_required = int(len(parties[party_owner]["members"]) / 2) + 1
        # filter function, vote_status[x] == True -> voted yes
        have_voted_yes = lambda x: vote_status[x]
        send_message_to_party(party_owner, message=f'{session["user"]} has voted {"Yes" if decision else "No"}. '
                                                   f'({len(filter_dict(vote_status, have_voted_yes).keys())}/'
                                                   f'{votes_required})')

        # A majority has voted to some either go or not go
        voted_yes = [name for name in vote_status if vote_status[name]]
        voted_no = [name for name in vote_status if not vote_status[name]]

        # Vote has resulted in rejecting the sever's suggestion
        if len(voted_no) > len(parties[party_owner]["members"]) - votes_required:
            send_message_to_party(session['user'],
                                  message=f"{len(voted_no)} people have voted NO.<br>"
                                          f"Vote canceled. You can request another suggestion.")
            parties[party_owner]["in_vote"] = False

        if votes_required == len(voted_yes):
            update_destination(parties[party_owner]["destination"], session['user'])
            send_message_to_party(session['user'],
                                  message=f"{len(voted_yes)} people have voted YES.<br>"
                                          f"Calculating route...")
            parties[party_owner]["in_vote"] = False

    if cmd == "sug" and in_party_chat:
        # lat, lng = get_location_request(session['user'])
        # location = {"name": "De-Shalit High-school", "lat": 31.89961596028198, "lng": 34.816320411774875}
        leader = get_party_leader(session['user'])
        # reset votes and update status to during vote (in vote)
        parties[leader]["in_vote"] = True
        parties[leader]["votes"] = {}
        # radius is in KM(Kilometres)
        locations = get_place_recommendation_location(
            tp=parties[leader]["place_type"],
            radius=2,
            limit=10
        )
        index = np.random.randint(0, len(locations))
        location = locations[index]
        print(json.dumps(location, indent=2))
        start_vote_on_place(leader=leader,
                            # lat=loc_of_place["lat"],
                            # lng=loc_of_place["lng"],
                            # name=location['name'],
                            location_data=location)

    if cmd == "leave_group" and in_party_chat:
        disconnect_user_from_party(session['user'])

    if cmd == "disband" and in_party_chat:
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
            chat_rooms[chat_id] = {"members": []}



"""
====================================================
 
              WEBSITE ENDPOINTS 
"""


#  LANDING PAGE
@app.route("/", methods=["POST", "GET"])
def main_page():
    session["time"] = int(time())
    # If user is not logged in
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("main.html")


#  REGISTER PAGE
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        # get info from form
        user = request.form['name']
        password = request.form['pass']
        confirm = request.form['confirm']
        all_names = database.get_all_names()
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
            database.add_user(user, password)
            return redirect("/")
        return render_template("register.html")
    else:
        return render_template("register.html")


#  LOGIN PAGE
@app.route("/login", methods=["POST", "GET"])
def login():
    # Submitted the login form
    if request.method == "POST":
        # Get user/password from the form
        user = request.form['name']
        password = request.form['pass']
        # Is the password correct? Is the user valid?
        # If the user isn't valid, it throws an error.
        try:
            if str(database.get("users", "password", f'username="{user}"')[0]) != password:
                flash("Either the name, or the password are wrong.")
                return render_template("login.html")
            else:
                session['user'] = user
                session['is_admin'] = user == database.admin
                # Login successful, redirect to /
                return redirect("/")
        except Exception as e:
            print(e)
            flash("Either the name, or the password are wrong.")
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


"""
====================================================
"""


def get_party_chat_id(user):
    if get_party_leader(user):
        return parties[get_party_leader(user)]["chat_id"]
    else:
        return -1


def send_message_to_party(member, message, author="(System)"):
    chat_id = get_party_chat_id(member)
    emit_to_party(member, event_name="message",
                  message={"id": chat_id, "message": message, "author": author})


def parse_action(command):
    args = command.split("/")
    command_name = args[0]
    if command_name == "accept_friend_request":
        requester = args[1]
        database.make_friends(requester, session["user"])
        # user_data[session['user']]["friends"].append(requester)
        database.send_message(title=f"You and {session['user']} are now friends!",
                              desc=f"{session['user']} has accepted your friend request.",
                              message_sender=session["user"], receiver=request, messagetype="ignore",
                              action="ignore")
        # db['ex'].add_notif(requester)

        # emit_to(requester, 'notif', '/comms', 'notification!')

    if command_name == "join_party":
        party_owner = args[1]
        if party_owner not in connected_members:
            return

        # they have no party
        if connected_members[party_owner]["party"] is None:
            return

        if session['user'] in parties[party_owner]["members"]:
            print(session['user'], "already in party", party_owner)
            return

        join_party(party_owner, session['user'])

        emit_to_party(party_owner, event_name="update_party_members", message=get_party_members(party_owner))
        send_message_to_party(party_owner, message=f'{session["user"]} joined!')

    if command_name == "accept_suggestion":
        try:
            party_owner = \
                [owner for owner in party_suggestions if session['user'] in party_suggestions[owner]["total"]][0]
            if len(get_party_members(party_owner)) == 0:
                create_party(session['user'])
                if party_owner != session['user']:
                    # copy over the data
                    party_suggestions[session['user']] = party_suggestions[party_owner].copy()
                    # delete old data
                    del party_suggestions[party_owner]
                    party_owner = session['user']

                # make session user the first user in the list
                members = party_suggestions[session['user']]["total"]
                # remove user
                members.remove(session['user'])
                # add user in the beginning
                members = [session['user']] + members
                # update dictionary
                party_suggestions[session['user']]["total"] = members

            else:
                # just join the party lol
                join_party(party_owner, session['user'])

            # append you to the people who accepted the suggestion
            PSP = party_suggestions[party_owner]
            PSP["accepted"].append(session['user'])
            emit_to_party(party_owner, event_name="update_party_members", message=get_party_members(party_owner))
            # if everyone reacted to it we don't need it anymore woooo
            if len(PSP["accepted"]) + len(PSP["rejected"]) == len(PSP["total"]):
                del party_suggestions[party_owner]

            send_message_to_party(party_owner, message=f'{session["user"]} joined!')

        except IndexError:
            print('lol sucks for u')


def send_path_to_party(user_to_track):
    party_members = get_party_members(user_to_track)
    party_leader = get_party_leader(user_to_track)
    if len(party_members) == 0:
        return
# "destination_status": "No Destination" | "Have Destination" | "Reached Destination"
    paths = []
    if parties[party_leader]["destination_status"] in ["No Destination"]:
        return

    print(f"tracc {user_to_track}, {party_members}")
    done = False

    if len(parties[party_leader]["arrived"]) == len(party_members):
        done = True

    """ done = True
    # meters = 5"""
    for member in party_members:
        if member in connected_members:
            try:
                a = connected_members[member]['current_path']
                path, index = a["path"], a["index"]

                # this still doesn't work

                current_lat, current_lng = connected_members[member]['loc']
                path_and_current_loc = [[current_lat, current_lng]] + path[index:]
                print(f"123, {len(path_and_current_loc)}", index, f"{len(path[index:])}")
                # this works
                # path_and_current_loc = path[index:]

                current_user_path = [{'lat': x[0], 'lng': x[1]} for x in path_and_current_loc]
                paths.append((member, current_user_path))
                """ min_distance = meters * 0.0000089  # convert to lng/lat scale
                 if distance(connected_members[member]['loc'], path[index]) < min_distance:
                     done = False"""

                print(f"Adding path from {member}[:{index}], sending to {user_to_track} ({party_members})")
            except Exception as e:
                print(f"Error in drawing path from {member} on {session['user']}'s screen | {e}")
    emit_to(session["user"], 'user_paths', message=paths)
    emit_to("Admin", 'user_paths', message=paths)

    # all the paths are dones
    if done and len(party_members) > 1 and parties[party_leader]["destination_status"] != "Reached Destination":
        parties[party_leader]["destination_status"] = "Reached Destination"
        # online party members in order
        list_of_priorities = [x for x in party_members if x in connected_members]
        database.send_message(title=f"Party Reached Destination",
                              desc=f"{party_leader}'s party has reached their destination.",
                              sender="[System]", receiver="Admin", messagetype="ignore",
                              action=None)


def join_party(owner, username):
    if username in parties[owner]["members"]:
        return
    connected_members[username]["party"] = owner
    parties[owner]["members"].append(username)

    party_chat_id = parties[owner]["chat_id"]
    chat_rooms[party_chat_id]["members"][username] = False

    parties[owner]["place_type"] = kmeans.find_best_category(parties[owner]["members"], category_values)
    party_coords(owner)

    connected_members[username]["chats"].append(party_chat_id)

    room = {"id": party_chat_id, **chat_rooms[party_chat_id]}
    emit_to(session['user'], event_name="create_chat", message=room)

    members = parties[owner]["members"]
    for member in members:
        if member in connected_members:
            lat, lng = connected_members[member]["loc"]
            emit_to("Admin", 'my_location_from_server', message={
                "name": member,
                "lat": lat, "lng": lng
            })


def broadcast_user_difference():
    friends = database.get_friends(session["user"])
    visible_users = [x for x in connected_members if x != "Admin"]
    online_friends, offline_friends = [], []

    def filter_online(username):
        if username in visible_users:
            online_friends.append(username)
        else:
            offline_friends.append(username)

    for user in friends:
        filter_online(user)

    session["friend_data"] = {'online': online_friends,
                              'offline': offline_friends}

    emit_to(session["user"], 'friend_data', message=session["friend_data"])
    emit_to_everyone(event_name='user_diff', message=visible_users)

    emit_to("Admin", "all_users", message={u: u in connected_members for u in database.get_all_names()})

    print("Last ping data:")
    print("\n".join([f"{name}, {int(time()) - connected_members[name]['last ping']}" for name in visible_users]))
    print({'amount': len(connected_members.keys()), 'names': [user for user in connected_members]})


"""
           SOCKETIO   ENDPOINTS
"""


@socketio.on('connect', namespace='/comms')
def logged_on_users():

    if session['user'] not in members:
        members[session['user']] = {
            "sid": request.sid,  # the socket sid
            "loc": database.get_user_location(session['user']),  # [0, 0],
            "current_path": {"path": [], "index": 0},
            "party": None,  # (party owner's name | None) ,
            "last ping": time_now(),
            "chats": ["0"]  # 0 is the global chat
        }
    else:
        print("RECONNECTED", session['user'], session['user'] in connected_members)
        # Reconnecting
        members[session['user']]["sid"] = request.sid
        members[session['user']]["last ping"]: time_now()

    # put userdata in the connected member dictionary
    # will be deleted when user is disconnected
    connected_members[session['user']] = members[session['user']]

    # chat ids that the user can see
    chat_ids = [room["id"] for room
                in get_all_user_chats(session['user'])]

    for chat_id in chat_ids:
        # The user needs to create all of his channels again
        # Make it so all the user's channels aren't confirmed
        chat_rooms[chat_id]["members"][session['user']] = False


@socketio.on('path_from_user', namespace='/comms')
def return_path(data):
    # # # # # # # # # # # # # # # # # # # # # # # # # # #.data, step_index
    connected_members[session['user']]['current_path'] = {"path": data, "index": 0}
    print(f"Received path from {session['user']}")
    send_path_to_party(user_to_track=session['user'])


@socketio.on('suggest_location', namespace='/comms')
def check_ping(data):
    start_vote_on_place(leader=get_party_leader(session['user']),
                        location_data=data)


@socketio.on('ping', namespace='/comms')
def check_ping(online_users):
    # update last pinged time for user

    # idfk is going on here. this shouldn't ever happen
    # but it does
    if session['user'] not in connected_members:
        print("Logged in in ping event")
        logged_on_users()

    members[session['user']] = connected_members[session['user']].copy()

    connected_members[session['user']]["last ping"] = time_now()

    # if we have users we need to update the online list
    # delete members that haven't pinged in 2 seconds

    for username in connected_members.copy():
        if time_now() - connected_members[username]["last ping"] > 2:
            print(f"DELETING {username}")
            del connected_members[username]
            broadcast_user_difference()

    # If user has a party, send them the party coords.
    # Even if the party is currently running a simulation,
    # this shouldn't disturb it.
    if get_party_leader(session['user']) is not None:
        party_coords(session['user'])

    """ The user will filter what notifications they already have by
        the message ID. That way the user won't need to constantly update
        all of the messages, but rather only the messages that are new.
        
        Also, the user will have to delete messages that are not in 
        this message, but are displayed on the user's screen.              """

    messages = database.get_messages(user=session['user'])

    emit_to(session['user'], event_name="inbox_update", message=messages)
    if len(connected_members.keys()) != len(online_users):
        broadcast_user_difference()

    # The ADMIN client doesn't need to see chats
    send_path_to_party(session['user'])

    def client_has_confirmed(chat_id):
        try:
            return chat_rooms[chat_id]["members"][session['user']]
        except KeyError:
            return True

    if session['user'] != "Admin":

        # CREATE CHATS that have not yet been confirmed by the client
        # run over all chats user should have, and check if they've been
        # confirmed.
        [emit_to(session['user'], "create_chat", message=room)
         for room in get_all_user_chats(session['user'])
         if not client_has_confirmed(room["id"])]

        # DELETE CHATS that need to be deleted, them remove them from
        # the deletion queue. repeats until confirmed by user.
        if session['user'] in delete_chats_queue:
            [emit_to(session['user'], event_name="del_chat", message=chat_id)
             for chat_id
             in delete_chats_queue[session['user']]]

        lat, lng = connected_members[session['user']]["loc"]
        emit_to("Admin", 'my_location_from_server', message={
            "name": session['user'],
            "lat": lat, "lng": lng
        })

    data = separate_into_colours(parties.keys())
    emit_to("Admin", event_name="user_colors", message=data)


@socketio.on('invite_user', namespace='/comms')
def invite_user(receiver):
    print("inviting", receiver)
    if receiver == session['user']:
        return

    database.send_message(title=f"Party invite from {session['user']}!",
                          desc=f"{session['user']} has invited you to join their party, wanna hang out?",
                          sender=session["user"], receiver=receiver, messagetype="question",
                          action=f"join_party/{session['user']}")


@socketio.on('add_location', namespace='/comms')
def add_location_func(data):
    name, lat, lng, loc_type = data.split(", ")
    database.add_location(name, lat, lng, loc_type)
    [send_user_added_locations(online_user) for online_user in connected_members]


@socketio.on('chat_message', namespace='/comms')
def chat_message(data):
    """
    Multicast message from user to
    appropriate chat
    """
    room, message, author = data["room"], data["message"], session['user']
    chat_rooms[room]["history"].append({"message": message, "author": author})
    room_members = list(chat_rooms[room]["members"].keys())

    for member in room_members:
        emit_to(member, 'message', message={
            "id": room,
            "author": author,
            "message": message
        })
    if message[0] == "/":
        # pass
        parse_chat_command(message, room)


@socketio.on('inbox_notification_react', namespace='/comms')
def notification_parse(data):
    message_id, reaction = data["message_id"], data["reaction"]

    # first grab the message to see what we need to do with it
    _id, title, content, sender, receiver, msg_type, action = \
        database.get('messages', '*', f'id={message_id}', first=False)[0]
    print(f"{reaction}: {title} | {msg_type}")
    if reaction != "mark_as_read":
        parse_action(action)
    database.remove("messages", f'id={message_id}')

    session['inbox_messages'] = get_messages(session['user'])


@socketio.on('user_added_locations_get', namespace='/comms')
def get_user_added_loc():
    data = [(name, [float(value) for value in latlng.split(", ")])
            for name, latlng, type in database.get_user_added_locations()]
    emit_to(user=session["user"], event_name='user_added_locations', message=data)


@socketio.on('party_members_list_get', namespace='/comms')
def emit_party_members():
    emit_to(user=session['user'], event_name="party_members_list_get",
            message=get_party_members(session['user']))


@socketio.on('online_members_get', namespace='/comms')
def get_online_memb():
    emit_to(user=session['user'], event_name="online_members_get",
            message=[x for x in connected_members if x != "Admin"])


@socketio.on('get_destination', namespace='/comms')
def get_destination():
    if session['user'] == "Admin":
        return
    if connected_members[session['user']]["party"] is None:
        return
    if parties[get_party_leader(session['user'])]["destination"] is None:
        return

    lat, lng = parties[get_party_leader(session['user'])]["destination"]
    emit_to(session['user'], event_name='update_destination',
            message={"lat": lat, "lng": lng})


@socketio.on('get_coords_of_party', namespace='/comms')
def get_coords_of_party():
    leader = get_party_leader(session['user'])
    party_coords(leader)


@socketio.on('confirm_chat', namespace='/comms')
def confirm_chat(chat_id):
    chat_rooms[chat_id]["members"][session['user']] = True


@socketio.on('confirm_del_chat', namespace='/comms')
def confirm_delete_chat(chat_id):
    try:
        delete_chats_queue[session['user']].remove(chat_id)
    except KeyError:
        pass


@socketio.on('my_location_from_user', namespace='/comms')
def my_location(data):
    # set_user_location(session['user'], data[0], data[1])

    connected_members[session['user']]['current_path']["index"] = data["index"]
    connected_members[session['user']]['loc'] = data["lat"], data["lng"]
    lat, lng = data["lat"], data["lng"]
    location_obj = {
        "name": session['user'],
        "lat": lat, "lng": lng
    }

    emit_to("Admin", event_name='my_location_from_server', message=location_obj)
    emit_to_party(session['user'], event_name='my_location_from_server', message=location_obj)
    send_path_to_party(session['user'])


@socketio.on('arrived', namespace='/comms')
def arrived():
    leader = get_party_leader(session['user'])
    if session['user'] not in parties[leader]["arrived"]:
        parties[leader]["arrived"].append(session['user'])
        send_path_to_party(session['user'])


@socketio.on('start_grouping_users', namespace="/comms")
def suggest_admin_event():
    """
        ============================= K MEANS =============================
         Get all users that are online,
         not in a group, and have not
         received a suggestion from the server
         (have an active suggestion)"""

    def group_suggestion_filter(u):
        # Check if user is in a suggestion list
        for leader in party_suggestions:
            if u in party_suggestions[leader]["total"]:
                return False
        # If user has a party return false
        leader = get_party_leader(u)
        if leader is not None or leader == "Admin":
            return False
        # Return true, user fits qualifications
        return True

    dont_have_suggestions = filter_dict(d=connected_members, f=group_suggestion_filter)
    if len(dont_have_suggestions) > 1:

        suggestion_groups = kmeans.find_optimal_clusters(
            only_these_values=filter_dict(kmeans.values, lambda x: x in dont_have_suggestions),
            verbose=False
        )
        for center in suggestion_groups:
            names = [person[0] for person in suggestion_groups[center]]

            suggest_party(names)


@socketio.on('request_destination_update', namespace='/comms')
def destination_update_request(data):
    update_destination(data, session['user'])


@socketio.on('disconnect', namespace='/comms')
def disconnect_event():
    broadcast_user_difference()
    pass


socketio.run(app, host="0.0.0.0", port=8080)
