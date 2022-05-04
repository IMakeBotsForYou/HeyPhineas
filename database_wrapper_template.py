import sqlite3
import threading


def st2int(array):
    """
    :param array: An array of objects(strings) that can be converted to ints
    :return: An array of ints
    """
    return [int(x) for x in array]


def int2st(array):
    """
    :param array: An array of ints
    :return: The array but converted into strings
    """
    return [str(x) for x in array]


def smallest_free(array):
    """
    :param array: An array of integers
    :return: The lowest "free" integer.
    E.g:
    <- [1, 3, 4]
    -> 2

    <- [1, 2, 3]
    -> 4

    <- [2, 3]
    -> 1
    """
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
    :param args: The variables that we want to convert into an SQL-usable string
    :return: formated string (var1, var2, var3...) for SQL purposes
    """
    st = "("
    variables = [i for i in args]
    need_trim = True
    for var in variables:
        # Loop over variables
        # Convert int
        if isinstance(var, int):
            st += f'{var}, '
            need_trim = True
        # Convert list by adding " " and ,
        elif isinstance(var, list):
            st += '"' + ", ".join([str(x) for x in var]) + '"'
            need_trim = False
        else:
            # Neither an int nor an array, need trimming
            st += f'"{var}", '
            need_trim = True

    if need_trim:
        return st[:-2] + ")"
    else:
        return st + ")"


class Database:
    """
    A class to interact with an SQL database
    """

    def __init__(self, path):
        """
        param path: path to the database
        """
        # Lock for multithreading purposes
        self.lock = threading.Lock()
        # Path to the .db file
        self.path = ".".join(path.split(".")[:-1]) + '.db'
        print(self.path)
        # Connection to the database
        self.data = sqlite3.connect(self.path, check_same_thread=False)
        # Cursor to execute commands
        self.cursor = self.data.cursor()

    def get(self, table, column, condition=None, limit=None, first=True):
        """
        :param table: database table
        :param column: What column?
        :param condition: condition of search
        :param limit: Limit the search to X results
        :param first: Return first of every result
        :return: The results
        """
        # Generate command based on parameters
        s = f"SELECT {column} FROM {table}"
        # Add condition if needed
        if condition: s += f" WHERE {condition}"
        # Add limit if needed
        if limit: s += f" LIMIT {limit}"
        # Execute the command
        a = self.execute(s)
        """ Return result
        # NOTE: Result is always in an array, even if only a single item
        # Single item/result behavior
        # first=False -> [(item, )]
        # first=True ->  [item]
        # Multiple items/result behavior
        # first=False -> [(item1, item2), (item3, item4)]
        # first=True  -> [item1, item3]
        """
        return [x[0] if first else x for x in a]

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
        """
        :param table: Table in the SQL
        :param values: Values to add (if multiple, then as a tuple)
        :return: None
        """
        self.fix_seq()
        print(F"INSERT INTO {table} VALUES {values}")
        self.execute(F"INSERT INTO {table} VALUES {values}")
        self.fix_seq()
        # except Exception as e:
        #     print(1, e)
        self.data.commit()

    def remove(self, table, condition=None):
        """
        :param table: Table in SQL
        :param condition: Condition for the item (E.g. 'name="foo"')
        :return:
        """
        self.execute(f'DELETE FROM {table} WHERE {"1=1" if not condition else condition}')
        self.fix_seq()

    def edit(self, table, column, newvalue, condition=None):
        s = f'UPDATE {table} SET {column} = "{newvalue}"'
        s += f" WHERE {condition}" if condition else " WHERE 1=1"
        self.execute(s)


class UserData(Database):
    """
        Database of users
    """

    def __init__(self, path):
        super().__init__(path)

    def get_all_names(self):
        """
        :return: Array of str
        """
        return self.get("users", "username")

    def get_user_data(self, colum=None):
        """
        :param colum: Specify a column in the SQL to get, if left empty will return all columns
        :return: All the user data
        """
        return self.get("users", colum if colum else "*", first=colum is not None)

    def add_user(self, username_password):
        """
        Add new user to the database
        :param username_password:
        :return: None
        """
        self.add("users (username, password, friends, interests)", username_password)

    def remove_user(self, name):
        """
        :param name: User to delete from the database
        :return: None
        """
        try:
            # if password == self.execute(f'SELECT password FROM users WHERE username="{name}"', 1)[0][0]:
            self.execute(f'DELETE FROM users WHERE username="{name}"')
            # else:
            #     print("Wrong password, you can't do that.")
        except IndexError:
            print(f"User {name} isn't registered!")

    def close(self):
        """
        Closes connection with the database
        :return: None
        """
        print("Finished")
        self.data.close()


def main():
    global user_db
    # The path to your database
    # ./database/data.db -> adding .db is optional.
    user_db = UserData("database/data")


if __name__ == "__main__":
    main()
    # import database_wrapper_danlvov as db_wrapper
    # from   database_wrapper_danlvov import main, user_db
    # db_wrapper.main()
    # user_db -> now is your database