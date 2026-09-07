"""Apply an optional address-space limit, then replace this process with a stage command."""

from __future__ import annotations

import argparse
import os
import resource
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory-gb", type=float, default=0.0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required")

    if args.memory_gb > 0:
        limit = int(args.memory_gb * 1024**3)
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        print(f"OpenReef RAM ceiling: {args.memory_gb:g} GB", flush=True)
    else:
        print("OpenReef RAM ceiling: unlimited", flush=True)

    os.execvpe(args.command[0], args.command, os.environ)
    return 127


if __name__ == "__main__":
    sys.exit(main())
