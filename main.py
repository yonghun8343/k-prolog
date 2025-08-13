import io
import sys

from CONSOLE.repl import execute

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
except Exception:
    pass


def main() -> None:
    if len(sys.argv) == 1:
        execute([], "")
    else:
        kpl_file = sys.argv[1]
        execute([], kpl_file)


if __name__ == "__main__":
    main()
