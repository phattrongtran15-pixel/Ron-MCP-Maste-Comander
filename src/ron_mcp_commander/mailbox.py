"""Asynchronous Ticket Mailbox Manager for A2A and Multi-Agent Orchestration.

Decouples Orchestrator from Workers so that communication is asynchronous,
eliminating synchronous blocking loops and preventing quota-burning panics.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


class MailboxManager:
    """Manages file-based task tickets in an inbox/outbox directory layout."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.inbox_dir = self.base_dir / "inbox"
        self.outbox_dir = self.base_dir / "outbox"
        self.archive_dir = self.base_dir / "archive"

        # Ensure directories exist
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def dispatch_ticket(
        self,
        action: str,
        payload: Dict[str, Any],
        target_worker: str,
        issuer: str = "Antigravity-Orchestrator",
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> str:
        """Create and write an asynchronous task ticket to the inbox."""
        ticket_id = f"TICKET-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        ticket_data = {
            "ticket_id": ticket_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "issuer": issuer,
            "target_worker": target_worker,
            "action": action,
            "payload": payload,
            "timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
            "status": "PENDING",
        }

        ticket_path = self.inbox_dir / f"{ticket_id}.json"
        with open(ticket_path, "w", encoding="utf-8") as f:
            json.dump(ticket_data, f, indent=2, ensure_ascii=False)

        return ticket_id

    def fetch_result(self, ticket_id: str) -> Dict[str, Any]:
        """Check outbox for task result. Does not block."""
        result_path = self.outbox_dir / f"result_{ticket_id}.json"
        if result_path.exists():
            with open(result_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Check if the ticket has timed out
        inbox_path = self.inbox_dir / f"{ticket_id}.json"
        if inbox_path.exists():
            with open(inbox_path, "r", encoding="utf-8") as f:
                ticket_data = json.load(f)
            created_at = datetime.fromisoformat(ticket_data["created_at"])
            elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()
            if elapsed > ticket_data.get("timeout_seconds", 30):
                return {
                    "ticket_id": ticket_id,
                    "status": "TIMEOUT",
                    "error": f"Worker '{ticket_data.get('target_worker')}' timed out after {elapsed:.1f}s.",
                }

        return {
            "ticket_id": ticket_id,
            "status": "PENDING",
            "message": "Task is still queued or processing by worker.",
        }

    def complete_task(
        self,
        ticket_id: str,
        result_payload: Dict[str, Any],
        worker_name: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Worker writes the completed result to outbox and moves ticket to archive."""
        result_data = {
            "ticket_id": ticket_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "worker_name": worker_name,
            "success": success,
            "result": result_payload,
            "error": error_message,
            "status": "COMPLETED" if success else "FAILED",
        }

        result_path = self.outbox_dir / f"result_{ticket_id}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        # Move inbox ticket to archive
        inbox_path = self.inbox_dir / f"{ticket_id}.json"
        if inbox_path.exists():
            archive_path = self.archive_dir / f"{ticket_id}.json"
            inbox_path.rename(archive_path)
