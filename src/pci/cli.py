from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (ContractError, get_entry, init_store, load_store, parse_impacts,
                   present, propose, save_store, transition)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pci")
    root.add_argument("--store", type=Path, default=Path("data/pci.json"))
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init")

    create = commands.add_parser("propose")
    create.add_argument("--seed", required=True)
    create.add_argument("--hook", required=True)
    create.add_argument("--ruler", required=True)
    create.add_argument("--bridge", required=True)
    create.add_argument("--unexpected", action="store_true")
    create.add_argument("--relevant", action="store_true")
    create.add_argument("--joy", action="store_true")
    create.add_argument("--must", action="store_true")
    create.add_argument("--expected", action="append", default=[])

    confirm = commands.add_parser("confirm")
    confirm.add_argument("id")
    observe = commands.add_parser("observe")
    observe.add_argument("id")
    observe.add_argument("--experience", required=True)
    observe.add_argument("--impact", action="append", default=[], required=True)
    show = commands.add_parser("show")
    show.add_argument("id")
    commands.add_parser("list")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            init_store(args.store)
            print(json.dumps({"store": str(args.store), "initialized": True}))
            return 0
        store = load_store(args.store)
        if args.command == "propose":
            entry = propose(
                store, seed=args.seed, hook=args.hook, ruler=args.ruler,
                bridge=args.bridge, unexpected=args.unexpected,
                relevant=args.relevant, joy=args.joy, must=args.must,
                expected_impact=parse_impacts(args.expected),
            )
            save_store(args.store, store)
            output = present(entry)
        elif args.command == "confirm":
            output = present(transition(store, args.id, "USER_CONFIRMED"))
            save_store(args.store, store)
        elif args.command == "observe":
            output = present(transition(
                store, args.id, "OBSERVED", experience=args.experience,
                observed_impact=parse_impacts(args.impact),
            ))
            save_store(args.store, store)
        elif args.command == "show":
            output = present(get_entry(store, args.id))
        else:
            output = [present(entry) for entry in store["entries"]]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ContractError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

