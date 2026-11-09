"""Unit tests for CircuitBreaker and Anti-Greedy Quota Guard."""

import unittest
from ron_mcp_commander.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    QuotaBudgetExceededError,
    GreedyFallbackViolationError,
    WorkerDelegationFailedError,
)


class TestCircuitBreaker(unittest.TestCase):

    def setUp(self):
        self.cb = CircuitBreaker(
            name="Test-Breaker",
            max_consecutive_failures=2,
            reset_timeout_seconds=10.0,
            token_budget_ceiling=1000,
            enable_greedy_fallback_defense=True,
        )

    def test_normal_successful_execution(self):
        def dummy_worker(x, y):
            return x + y

        result = self.cb.execute_delegation("task-1", "worker-a", dummy_worker, 3, 4)
        self.assertEqual(result, 7)
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
        self.assertEqual(self.cb.consecutive_failures, 0)

    def test_consecutive_failures_trip_circuit(self):
        def failing_worker():
            raise ConnectionError("Worker offline / Ollama down")

        # 1st failure: should raise WorkerDelegationFailedError, circuit still CLOSED
        with self.assertRaises(WorkerDelegationFailedError):
            self.cb.execute_delegation("task-fail-1", "worker-a", failing_worker)
        self.assertEqual(self.cb.consecutive_failures, 1)
        self.assertEqual(self.cb.state, CircuitState.CLOSED)

        # 2nd failure: reaches max_consecutive_failures -> trips to OPEN
        with self.assertRaises(WorkerDelegationFailedError):
            self.cb.execute_delegation("task-fail-2", "worker-a", failing_worker)
        self.assertEqual(self.cb.consecutive_failures, 2)
        self.assertEqual(self.cb.state, CircuitState.OPEN)

        # 3rd attempt: immediately rejected by Circuit Breaker (Fail-Closed)
        with self.assertRaises(CircuitBreakerOpenError):
            self.cb.execute_delegation("task-fail-3", "worker-a", failing_worker)

    def test_intercept_greedy_fallback(self):
        """Verify orchestrator is blocked if it tries to execute a delegated task."""
        def dummy_worker():
            return "ok"

        # Delegate task-alpha to worker-ollama
        self.cb.execute_delegation("task-alpha", "worker-ollama", dummy_worker)

        # Now suppose orchestrator tries to run task-alpha directly itself:
        with self.assertRaises(GreedyFallbackViolationError):
            self.cb.intercept_orchestrator_execution("task-alpha")

        # Circuit must be tripped to prevent further quota burn
        self.assertEqual(self.cb.state, CircuitState.OPEN)
        self.assertIn("GREEDY_FALLBACK_INTERCEPTED", self.cb.trip_reason)

    def test_token_budget_ceiling_enforcement(self):
        """Verify token consumption is stopped hard at budget limit."""
        self.cb.record_tokens(400)
        self.assertEqual(self.cb.total_tokens_consumed, 400)
        self.assertEqual(self.cb.state, CircuitState.CLOSED)

        # Adding 700 tokens reaches 1100, exceeding ceiling of 1000
        with self.assertRaises(QuotaBudgetExceededError):
            self.cb.record_tokens(700)

        self.assertEqual(self.cb.state, CircuitState.OPEN)
        self.assertIn("TOKEN_BUDGET_EXCEEDED", self.cb.trip_reason)

    def test_manual_reset(self):
        self.cb.trip("Manual test trip")
        self.assertEqual(self.cb.state, CircuitState.OPEN)
        self.cb.reset()
        self.assertEqual(self.cb.state, CircuitState.CLOSED)
        self.assertIsNone(self.cb.trip_reason)


if __name__ == "__main__":
    unittest.main()
