class DebugState:
    def __init__(self):
        self.trace_mode = False
        self.call_depth = 0


class DebugAbort(Exception):
    pass


def show_call_trace(goal, depth):
    print(f"Call: ({depth}) {goal} ? ", end="")


def show_exit_trace(goal, depth):
    print(f"Exit: ({depth}) {goal} ? ", end="")


def handle_trace_input(debug_state: DebugState, last_goal):
    while True:
        try:
            cmd = input("").strip().lower()
            if cmd == "creep" or cmd == "c" or cmd == "":
                print("creep")  # Echo the command
                return
            elif cmd == "abort" or cmd == "a":
                print("abort")
                raise DebugAbort()
            elif cmd == "notrace" or cmd == "n":
                print("notrace")
                debug_state.trace_mode = False
                return
            elif cmd == "exit" or cmd == "e":
                print("exit")
                debug_state.trace_mode = False
                return
            else:
                print(f"Unknown command: {cmd}")
                print("Commands: creep, abort, notrace, exit")
                print(
                    f"Call: ({debug_state.call_depth}) {last_goal} ? ", end=""
                )
        except EOFError as e:
            raise DebugAbort() from e
