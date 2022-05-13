import re


get_func_name = re.compile(r'def ([a-zA-Z_]+)')

# ) -> type:
get_return_type = re.compile(r'-> (\w+):')

# param type
# \w+: \w+
get_params = re.compile(r'(\w+): (\w+)')

#
get_socket_event = re.compile(r"^@socketio\.on\((.[a-zA-Z_ ]+.)")

with open("main.py") as f:
    lines = [line.strip() for line in f.readlines()
             if line.startswith("def ")
             or line.startswith("@socket")]
    for i, line in enumerate(lines):

        return_type = get_return_type.search(line)
        params = get_params.findall(line)
        func_name = get_func_name.search(line)

        socket_event = None
        if i > 1:
            previous_line = lines[i - 1]
            if not return_type:
                socket_event = get_socket_event.search(previous_line)

        if return_type:  # function we care about
            if params:
                print(func_name.groups()[0], f'({" ".join([f"{a[0]}: {a[1]}" for a in params])})', return_type.group())
            else:
                print(func_name.groups()[0], "(No Params)", return_type.group())
        elif socket_event:
            func_name = func_name.groups()[0]
            previous_line = lines[i-1]
            print(func_name, f"(Socket Event: {socket_event.groups()[0]})")