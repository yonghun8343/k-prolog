class DebugState:
    def __init__(self):
        self.trace_mode = False
        self.call_depth = 0


class DebugAbort(Exception):
    pass


def show_call_trace(goal, depth):
    print(f"   Call: ({depth}) {goal}  ? ", end="")


def show_exit_trace(goal, depth):
    print(f"   Exit: ({depth}) {goal}  ? ", end="")


def handle_trace_input(debug_state: DebugState):
    while True:
        try:
            cmd = input("").strip().lower()
            if cmd == "creep" or cmd == "c" or cmd == "":
                return
            elif cmd == "abort" or cmd == "a":
                raise DebugAbort()
            elif cmd == "notrace" or cmd == "n":
                debug_state.trace_mode = False
                return
            elif cmd == "exit" or cmd == "e":
                debug_state.trace_mode = False
                return
            else:
                print(f"Unknown command: {cmd}")
                print("Commands: creep, abort, notrace, exit")
                return
        except EOFError as e:
            raise DebugAbort() from e
