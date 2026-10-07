from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (ContractError, audit_store, confirm, get_entry, init_store,
                   load_store, observe, parse_impacts, present, propose, reject,
                   save_store)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pci")
    root.add_argument("--store", type=Path, default=Path("data/pci.json"))
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    create = commands.add_parser("propose")
    for name in ("seed", "hook", "ruler", "bridge"):
        create.add_argument(f"--{name}", required=True)
    create.add_argument("--unexpected", action="store_true")
    create.add_argument("--relevant", action="store_true")
    create.add_argument("--expected", action="append", default=[])
    accept = commands.add_parser("confirm")
    accept.add_argument("id")
    accept.add_argument("--joy", action="store_true")
    accept.add_argument("--must", action="store_true")
    accept.add_argument("--note")
    decline = commands.add_parser("reject")
    decline.add_argument("id")
    decline.add_argument("--note")
    observed = commands.add_parser("observe")
    observed.add_argument("id")
    observed.add_argument("--experience", required=True)
    observed.add_argument("--impact", action="append", default=[], required=True)
    show = commands.add_parser("show")
    show.add_argument("id")
    commands.add_parser("list")
    commands.add_parser("audit")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            init_store(args.store)
            output = {"store": str(args.store), "initialized": True}
        else:
            store = load_store(args.store)
            if args.command == "propose":
                output = present(propose(
                    store, seed=args.seed, hook=args.hook, ruler=args.ruler,
                    bridge=args.bridge, unexpected=args.unexpected,
                    relevant=args.relevant, expected_impact=parse_impacts(args.expected)))
                save_store(args.store, store)
            elif args.command == "confirm":
                output = present(confirm(store, args.id, joy=args.joy,
                                         must=args.must, note=args.note))
                save_store(args.store, store)
            elif args.command == "reject":
                output = present(reject(store, args.id, note=args.note))
                save_store(args.store, store)
            elif args.command == "observe":
                output = present(observe(store, args.id, experience=args.experience,
                                         observed_impact=parse_impacts(args.impact)))
                save_store(args.store, store)
            elif args.command == "show":
                output = present(get_entry(store, args.id))
            elif args.command == "audit":
                output = audit_store(store)
            else:
                output = [present(entry) for entry in store["entries"]]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ContractError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
