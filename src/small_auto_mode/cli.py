"""Small offline-first command interface."""
import argparse
import json
from . import gate, jev, search


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)
    for name in ("gate", "jev-build", "jev-query"):
        sub = s.add_parser(name)
        sub.add_argument("--case", required=True)
        sub.add_argument("--policy", required=True)
        if name == "gate":
            sub.add_argument("--assessment")
    sub = s.add_parser("search")
    sub.add_argument("--catalog", required=True)
    sub.add_argument("--query", required=True)
    sub.add_argument("--limit", type=int, default=5)
    args = p.parse_args()
    if args.command == "search":
        tools = [search.Tool.from_dict(x) for x in jev.load_json(args.catalog)]
        result = search.search(tools, args.query, args.limit).as_dict()
    else:
        try:
            case, policy = jev.load_json(args.case), jev.load_json(args.policy)
            if args.command == "gate":
                result = gate.decide(case, policy, jev.load_json(args.assessment) if args.assessment else None)
            elif args.command == "jev-query":
                result = jev.query(case, policy)
            else:
                result = jev.decision(case, policy) if jev.precheck(case, policy) else jev.build_request(case, policy)
        except (ValueError, OSError, TypeError, KeyError):
            result = {"decision": "ask", "reason": "invalid_input"}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
