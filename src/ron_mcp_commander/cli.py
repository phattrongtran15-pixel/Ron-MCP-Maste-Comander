"""Command Line Interface for Ron MCP Master Commander."""

import argparse
import json
import sys
from pathlib import Path
from .circuit_breaker import CircuitBreaker
from .mailbox import MailboxManager


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ron-guard",
        description="Ron MCP Commander - Quota Guard and Multi-Agent Circuit Breaker",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="Check current Circuit Breaker status")
    status_parser.add_argument("--budget", type=int, default=20000, help="Token budget ceiling")

    # Subcommand: ticket-dispatch
    dispatch_parser = subparsers.add_parser("dispatch", help="Dispatch an async task ticket to mailbox")
    dispatch_parser.add_argument("--action", required=True, help="Action name")
    dispatch_parser.add_argument("--worker", required=True, help="Target worker name")
    dispatch_parser.add_argument("--payload", default="{}", help="JSON payload string")
    dispatch_parser.add_argument("--mailbox-dir", default="./.mailbox", help="Mailbox base directory")

    # Subcommand: ticket-check
    check_parser = subparsers.add_parser("check", help="Check ticket result in mailbox")
    check_parser.add_argument("--ticket-id", required=True, help="Ticket ID to check")
    check_parser.add_argument("--mailbox-dir", default="./.mailbox", help="Mailbox base directory")

    args = parser.parse_args()

    if args.command == "status":
        cb = CircuitBreaker(token_budget_ceiling=args.budget)
        report = cb.get_status_report()
        print(json.dumps(report, indent=2))

    elif args.command == "dispatch":
        try:
            payload_data = json.loads(args.payload)
        except json.JSONDecodeError:
            print("Error: --payload must be valid JSON", file=sys.stderr)
            sys.exit(1)

        mailbox = MailboxManager(Path(args.mailbox_dir))
        ticket_id = mailbox.dispatch_ticket(
            action=args.action,
            payload=payload_data,
            target_worker=args.worker,
        )
        print(f"Ticket dispatched successfully: {ticket_id}")

    elif args.command == "check":
        mailbox = MailboxManager(Path(args.mailbox_dir))
        result = mailbox.fetch_result(args.ticket_id)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
