from CONSOLE.repl import execute
import sys


def main() -> None:
    if len(sys.argv) == 1:
        execute([], "")
    else:
        kpl_file = sys.argv[1]
        execute([], kpl_file)


if __name__ == "__main__":
    main()
