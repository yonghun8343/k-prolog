class DebugState:
    def __init__(self):
        self.trace_mode = False
        self.call_depth = 0
        self.seq = 0
        self.recorded_db = {}  # key:str -> list of (ref_id:int, term:Term)
        self.recorded_counter = 0


class DebugAbort(Exception):
    pass


def show_call_trace(goal, depth):
    print(f"   호출: ({depth}) {goal}  ? ", end="")


def show_exit_trace(goal, depth):
    print(f"   나가기: ({depth}) {goal}  ? ", end="")


def handle_trace_input(debug_state: DebugState):
    while True:
        try:
            cmd = input("").strip().lower()
            if cmd == "creep" or cmd == "c" or cmd == "" or cmd == "다음":
                return
            elif cmd == "abort" or cmd == "a" or cmd == "중단":
                raise DebugAbort()
            elif cmd == "notrace" or cmd == "n" or cmd == "추적중단":
                debug_state.trace_mode = False
                return
            elif cmd == "exit" or cmd == "e" or cmd == "나가기":
                debug_state.trace_mode = False
                return
            else:
                print(f"알 수 없는 명령: {cmd}")
                print("명령어들: 다음, 중단, 추적중단, 나가기")
                return
        except EOFError as e:
            raise DebugAbort() from e
