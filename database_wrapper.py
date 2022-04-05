import sqlite3
import json
import threading


def st2int(array):
    return [int(x) for x in array]


def int2st(array):
    return [str(x) for x in array]


def smallest_free(array):
    lowest = 1
    if not array:
        return 1
    m = min(array)
    if m != 1:
        return 1
    for i, value in enumerate(array[1:]):
        if value - lowest == 1:
            lowest = value
        else:
            return lowest + 1
    return lowest


def reformat(*args):
    """
    :param args: the variables we put into it
    :return: formated string (var1, var2, var
    3..) for SQL purposes
    """
    st = "("
    variables = [i for i in args]
    need_trim = True
    for var in variables:
        if isinstance(var, int):
            st += f'{var}, '
            need_trim = True
        elif isinstance(var, list):
            st += '"' + ", ".join([str(x) for x in var]) + '"'
            need_trim = False
        else:
            st += f'"{var}", '
            need_trim = True

    print(need_trim, st + ")")

    if need_trim:
        return st[:-2] + ")"
    else:
        return st + ")"


class Database:
    def __init__(self, path):
        self.lock = threading.Lock()
        # self.admin = "Admin"
        self.path = path.split(".")[0] + '.db'
        self.data = sqlite3.connect(self.path, check_same_thread=False)
        self.cursor = self.data.cursor()
        # self.parties = []
        # with open('static/users.js', 'w') as f:
        #     f.write(f'var users = {json.dumps(self.get("users", "username"))}')

    def get(self, table, column, condition=None, limit=None, first=True):
        """
        :param table: database table
        :param column: What column?
        :param condition: condition of search
        :param limit: Limit the search to X results
        :param first: Return first of every result
        :return: The results
        """

        s = f"SELECT {column} FROM {table}"
        if condition: s += f" WHERE {condition}"
        if limit: s += f" LIMIT {limit}"
        return [x[0] if first else x for x in self.execute(s)]

    def execute(self, line, fetch=None):
        """
        :param line: SQL command
        :param fetch: Number to of results to return
        :return: The results
        """
        ret = None
        try:
            self.lock.acquire(True)

            self.cursor.execute(line)
            if not fetch or fetch == -1:
                ret = self.cursor.fetchall()
                self.data.commit()

            else:
                ret = self.cursor.fetchmany(fetch)
                self.data.commit()
            # do something
        finally:
            self.lock.release()
            if ret is None:
                print(f"Returning None, {line}")
            return ret

    def fix_seq(self):
        # columns = ["users"]
        # for na in columns:
        #     a = self.get(na, "id")
        #     self.edit("sqlite_sequence", "seq", smallest_free(a) if a else 0, f'name="{na}"')
        pass

    def add(self, table, values):
        # try:
        self.fix_seq()
        print(F"INSERT INTO {table} VALUES {values}")
        self.execute(F"INSERT INTO {table} VALUES {values}")
        self.fix_seq()
        # except Exception as e:
        #     print(1, e)
        self.data.commit()

    def remove(self, table, condition=None):
        self.execute(f'DELETE FROM {table} WHERE {"1=1" if not condition else condition}')
        self.fix_seq()

    def edit(self, table, column, newvalue, condition=None):
        s = f'UPDATE {table} SET {column} = "{newvalue}"'
        s += f" WHERE {condition}" if condition else " WHERE 1=1"
        self.execute(s)


class UserData(Database):
    def __init__(self, path):
        super().__init__(path)
        self.admin = "Admin"
        self.parties = []
        with open('static/users.js', 'w') as f:
            f.write(f'var users = {json.dumps(self.get("users", "username"))}')

    def get_all_names(self, remove_admin=False):
        if remove_admin:
            return [name for name in self.get("users", "username") if name != "Admin"]

        return self.get("users", "username")

    def send_message(self, title, desc, sender, receiver, messagetype, action):
        print("added", title, desc)
        self.add("messages (title, content, sender, receiver, type, action)",
                 reformat(title, desc, sender, receiver, messagetype, action))

    def get_users(self, colum=None):
        return self.get("users", colum if colum else "*", first=colum)

    def fix_seq(self):
        columns = ["users"]
        for na in columns:
            a = self.get(na, "id")
            self.edit("sqlite_sequence", "seq", smallest_free(a) if a else 0, f'name="{na}"')

    def get_user_location(self, username):
        if username == "Admin":
            return None
        return [float(value) for value in self.get("users", "loc", condition=f'username="{username}"')[0].split(", ")]

    def set_user_location(self, username, newvalue):
        self.edit('users', 'loc', newvalue=newvalue, condition=f'username="{username}"')

    def create_party(self, user):
        if len(self.get('parties', 'creator', condition=f'creator="{user}"')) > 0:
            for member in self.get_party_members(user):
                print('removing', member)
                self.remove_from_party(user, member)
            self.remove('parties', condition=f'creator="{user}"')

        self.add('parties', reformat(user, "", "no current request"))
        self.add_to_party(user, user)

    def set_party_status(self, creator, newvalue):
        self.edit('parties', 'status', newvalue=newvalue, condition=f'creator="{creator}"')

    def get_party_status(self, creator):
        data = self.get('parties', 'status', condition=f'creator="{creator}"', first=False)
        if len(data) == 0:
            return "No Party"
        else:
            return data[0]

    def reset_notifs(self, user):
        return self.edit("users", "notifications", newvalue=0, condition=f'username="{user}"')

    def add_notif(self, user):
        num = self.get_notifs(user)
        return self.edit("users", "notifications", newvalue=num+1, condition=f'username="{user}"')

    def get_notifs(self, user):
        return int(self.get("users", "notifications", condition=f'username="{user}"')[0])

    def add_to_party(self, owner, user_to_add):
        members = self.get('parties', 'members', condition=f'creator="{owner}"')
        if len(members) == 0:
            members = []
        else:
            members = members[0].split(", ")
        members.append(user_to_add)
        members = list({x for x in [a for a in members if a != ""]})  # remove dupes
        self.edit('parties', 'members', newvalue=", ".join(members), condition=f'creator="{owner}"')
        self.edit('users', 'current_party', newvalue=owner, condition=f'username="{user_to_add}"')

    def remove_from_party(self, owner, user_to_remove):
        members = self.get('parties', 'members', condition=f'creator="{owner}"')[0].split(", ")
        members.remove(user_to_remove)
        self.edit('parties', 'members', newvalue=", ".join(members), condition=f'creator="{owner}"')
        self.edit('users', 'current_party', newvalue="", condition=f'username="{user_to_remove}"')

    def get_party_members(self, owner):
        a = self.get('parties', 'members', condition=f'creator="{owner}"')
        if len(a) == 0:
            return []
        else:
            a = a[0].split(", ")
            a.remove(owner)
            return [owner] + a

    def get_messages(self, user=None):
        mes = self.get('messages', '*', condition=f'receiver="{user}"' if user else None, first=False)
        ret = {"status": "empty", "messages": {}}
        for message in mes:
            xx, title, content, sender, receiver, m_type, action = message
            ret["status"] = "200"
            if receiver in ret['messages']:
                ret["messages"][receiver].append(
                    {"id": xx,
                     "title": title,
                     "content": content,
                     "sender": sender,
                     "type": m_type,
                     "action": action
                     })
            else:
                ret["messages"][receiver] = \
                    [{"id": xx,
                      "title": title,
                      "content": content,
                      "sender": sender,
                      "type": m_type,
                      "action": action
                      }]
        return ret

    def get_friends(self, user):
        f = self.get("users", "friends", condition=f'username="{user}"')
        print(f)
        if len(f) > 0 and f != [None]:
            return f[0].split(', ')
        else:
            return []

    def add_location(self, loc_name, lat, lng, loc_type):
        self.add('user_added_locations (name, latlng, type)', reformat(loc_name, f"{lat}, {lng}", loc_type))

    def add_user(self, username, password, friends="", interests="parks|0|restaurant|0|"):
        self.add("users (username, password, friends, interests)", reformat(username, password, friends, interests))

        # # # #  # # #  # # #  # # #  # # #  # # #  # # #
        with open('static/users.js', 'w') as f:
            f.write(f'var users = {json.dumps(self.get("users", "username"))}')
        # # # #  # # #  # # #  # # #  # # #  # # #  # # #

    def make_friends(self, user1, user2):
        current_friends1 = self.get("users", "friends", condition=f'name="{user1}"')[0].split(", ")
        current_friends2 = self.get("users", "friends", condition=f'name="{user2}"')[0].split(", ")
        current_friends1.append(user2)
        current_friends2.append(user1)
        self.edit("users", "friends", ", ".join(current_friends1), condition=f'name={user1}')
        self.edit("users", "friends", ", ".join(current_friends2), condition=f'name={user2}')

    def get_user_added_locations(self):
        return self.get('user_added_locations', 'name, latlng, type', first=False)

    def remove_user(self, name):
        try:
            # if password == self.execute(f'SELECT password FROM users WHERE username="{name}"', 1)[0][0]:
            self.execute(f'DELETE FROM users WHERE username="{name}"')
            # else:
            #     print("Wrong password, you can't do that.")
        except IndexError:
            print(f"User {name} isn't registered!")

        with open('static/users.js', 'w') as f:
            f.write(f'var users = {json.dumps(self.get("users", "username"))}')

    def close(self):
        print("Finished")
        self.data.close()



def reset_locations():
    for name in my_db.get_all_names():
        if name == "Admin":
            continue
        my_db.edit("users", "loc",
                   newvalue=def_locations.get("locations", "latlng", condition=f'username="{name}"')[0],
                   condition=f'username="{name}"')


def main():
    global my_db
    global def_locations
    my_db = UserData("database/data")
    def_locations = Database('database/def_locations')
    # for name in my_db.get_all_names():
    #     def_locations.add("locations", reformat(name, my_db.get_user_location(name)))


# my_db.remove_user("Guy", "123")
# print(my_db.get_users())


if __name__ == "__main__":
    main()

    # names = ["Mike", "Manor", "Liza", "Maya", "Yakov"]
    # import random
    # for name in names:
    #     my_db.add_user(name, "123", random.choice(names))
