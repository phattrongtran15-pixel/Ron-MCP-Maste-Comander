"""Unit tests for MailboxManager asynchronous ticket system."""

import shutil
import tempfile
import unittest
from pathlib import Path
from ron_mcp_commander.mailbox import MailboxManager


class TestMailboxManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mailbox = MailboxManager(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_dispatch_and_fetch_pending(self):
        ticket_id = self.mailbox.dispatch_ticket(
            action="summarize_text",
            payload={"text": "hello world"},
            target_worker="ollama-qwen",
        )
        self.assertTrue(ticket_id.startswith("TICKET-"))

        # Checking immediately should return PENDING
        status = self.mailbox.fetch_result(ticket_id)
        self.assertEqual(status["status"], "PENDING")

    def test_complete_task_success(self):
        ticket_id = self.mailbox.dispatch_ticket(
            action="parse_csv",
            payload={"file": "data.csv"},
            target_worker="local-parser",
        )

        # Worker completes task
        self.mailbox.complete_task(
            ticket_id=ticket_id,
            result_payload={"rows_parsed": 100},
            worker_name="local-parser",
            success=True,
        )

        # Fetch result
        result = self.mailbox.fetch_result(ticket_id)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["rows_parsed"], 100)

        # Ensure ticket was moved from inbox to archive
        self.assertFalse((self.mailbox.inbox_dir / f"{ticket_id}.json").exists())
        self.assertTrue((self.mailbox.archive_dir / f"{ticket_id}.json").exists())

    def test_timeout_detection(self):
        # Create ticket with 0 timeout seconds
        ticket_id = self.mailbox.dispatch_ticket(
            action="heavy_computation",
            payload={},
            target_worker="sleeping-worker",
            timeout_seconds=0,
        )

        result = self.mailbox.fetch_result(ticket_id)
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertIn("timed out", result["error"])


if __name__ == "__main__":
    unittest.main()
