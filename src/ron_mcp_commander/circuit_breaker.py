"""Core Circuit Breaker and Quota Protection for Multi-Agent / A2A Systems."""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"         # Normal operation, calls allowed through
    HALF_OPEN = "HALF_OPEN"   # Testing recovery with bounded single probe
    OPEN = "OPEN"             # Tripped: all calls immediately blocked (Fail-Closed)


class CircuitBreakerOpenError(Exception):
    """Raised when an operation is attempted while the circuit is tripped OPEN."""
    pass


class QuotaBudgetExceededError(Exception):
    """Raised when token or invocation count exceeds the hard ceiling budget."""
    pass


class GreedyFallbackViolationError(Exception):
    """Raised when an orchestrator tries to execute a delegated task itself after failure."""
    pass


class WorkerDelegationFailedError(Exception):
    """Raised when a delegated worker fails or times out."""
    pass


class CircuitBreaker:
    """Protects Multi-Agent A2A systems against cascade failures, endless loops,

    and greedy token burns when subagents or external tools fail to respond.
    """

    def __init__(
        self,
        name: str = "A2A-Master-Circuit-Breaker",
        max_consecutive_failures: int = 2,
        reset_timeout_seconds: float = 60.0,
        token_budget_ceiling: int = 20000,
        enable_greedy_fallback_defense: bool = True,
    ):
        self.name = name
        self.max_consecutive_failures = max_consecutive_failures
        self.reset_timeout_seconds = reset_timeout_seconds
        self.token_budget_ceiling = token_budget_ceiling
        self.enable_greedy_fallback_defense = enable_greedy_fallback_defense

        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.total_tokens_consumed = 0
        self.last_state_change = time.time()
        self.trip_reason: Optional[str] = None
        self.delegated_task_registry: Dict[str, str] = {}  # task_id -> worker_name

    def record_tokens(self, tokens_used: int) -> int:
        """Record token consumption and enforce hard budget ceiling."""
        self.total_tokens_consumed += tokens_used
        if self.total_tokens_consumed >= self.token_budget_ceiling:
            self.trip(
                reason=(
                    f"TOKEN_BUDGET_EXCEEDED: Consumed {self.total_tokens_consumed} tokens "
                    f"(Ceiling: {self.token_budget_ceiling})"
                )
            )
            raise QuotaBudgetExceededError(self.trip_reason)
        return self.total_tokens_consumed

    def trip(self, reason: str) -> None:
        """Trip circuit to OPEN state (Fail-Closed). Blocks further calls."""
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        self.trip_reason = reason
        logger.critical(f"[{self.name}] CIRCUIT TRIPPED TO OPEN: {reason}")

    def reset(self) -> None:
        """Reset circuit to CLOSED state (Normal)."""
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.trip_reason = None
        self.last_state_change = time.time()
        logger.info(f"[{self.name}] Circuit manually reset to CLOSED.")

    def can_execute(self) -> bool:
        """Check if circuit allows execution."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            elapsed = time.time() - self.last_state_change
            if elapsed >= self.reset_timeout_seconds:
                # Transition to HALF_OPEN to test recovery
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = time.time()
                logger.warning(f"[{self.name}] Recovery timeout elapsed. Transitioning to HALF_OPEN.")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def execute_delegation(
        self,
        task_id: str,
        target_worker: str,
        worker_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a task through a delegated worker with strict Circuit Breaker guards.

        If the worker fails, it NEVER falls back to greedy self-execution.
        """
        # Register delegation ownership
        self.delegated_task_registry[task_id] = target_worker

        if not self.can_execute():
            raise CircuitBreakerOpenError(
                f"[{self.name}] Circuit is OPEN (Fail-Closed). Execution rejected. Reason: {self.trip_reason}"
            )

        try:
            result = worker_fn(*args, **kwargs)
            # Success in execution
            if self.state == CircuitState.HALF_OPEN:
                # Canary probe succeeded, restore to CLOSED
                self.reset()
            else:
                self.consecutive_failures = 0
            return result
        except Exception as exc:
            self.consecutive_failures += 1
            logger.error(
                f"[{self.name}] Worker '{target_worker}' failed task '{task_id}' "
                f"({self.consecutive_failures}/{self.max_consecutive_failures}): {exc}"
            )

            if self.consecutive_failures >= self.max_consecutive_failures:
                self.trip(
                    reason=(
                        f"CONSECUTIVE_WORKER_FAILURES: Worker '{target_worker}' "
                        f"failed {self.consecutive_failures} times. Last error: {exc}"
                    )
                )

            raise WorkerDelegationFailedError(
                f"Delegated worker '{target_worker}' failed task '{task_id}'. "
                f"Greedy fallback is strictly forbidden under POL-A2A-CIRCUIT-BREAKER."
            ) from exc

    def intercept_orchestrator_execution(self, task_id: str) -> None:
        """Enforces anti-greedy defense. If an orchestrator attempts to execute

        a task that was already designated for a worker, halt immediately.
        """
        if not self.enable_greedy_fallback_defense:
            return

        if task_id in self.delegated_task_registry:
            worker = self.delegated_task_registry[task_id]
            self.trip(
                reason=(
                    f"GREEDY_FALLBACK_INTERCEPTED: Orchestrator attempted to execute "
                    f"task '{task_id}' assigned to worker '{worker}'."
                )
            )
            raise GreedyFallbackViolationError(
                f"VIOLATION: Orchestrator tried to execute task '{task_id}' assigned to worker '{worker}'. "
                f"Under Ron-Sho law, the orchestrator MUST HALT instead of burning quota."
            )

    def get_status_report(self) -> Dict[str, Any]:
        """Return structured status report for monitoring and logging."""
        return {
            "name": self.name,
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "max_failures_threshold": self.max_consecutive_failures,
            "tokens_consumed": self.total_tokens_consumed,
            "token_budget_ceiling": self.token_budget_ceiling,
            "tokens_remaining": max(0, self.token_budget_ceiling - self.total_tokens_consumed),
            "trip_reason": self.trip_reason,
            "last_state_change_timestamp": self.last_state_change,
        }

    def generate_issue_alert(
        self,
        task_id: str,
        target_worker: str,
        error_message: str,
        next_action_suggestion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate structured 'HAVE ISSUE' alert report. Silent halt is strictly forbidden."""
        suggested_action = next_action_suggestion or (
            f"Check if worker '{target_worker}' is running locally (e.g. check endpoint or 'ollama list'). "
            "Then run 'ron-guard status' or reset the circuit breaker."
        )
        return {
            "alert": "CRITICAL_ISSUE_DETECTED",
            "highlight": f"HAVE ISSUE: Worker '{target_worker}' is unresponsive on task '{task_id}'.",
            "task_id": task_id,
            "target_worker": target_worker,
            "root_cause": error_message,
            "circuit_state": self.state.value,
            "quota_status": f"{self.total_tokens_consumed}/{self.token_budget_ceiling} tokens used (Budget preserved)",
            "one_next_valid_action": suggested_action,
        }

    def format_issue_alert_markdown(
        self,
        task_id: str,
        target_worker: str,
        error_message: str,
        next_action_suggestion: Optional[str] = None,
    ) -> str:
        """Format the HAVE ISSUE alert in high-visibility markdown for human operators."""
        alert = self.generate_issue_alert(task_id, target_worker, error_message, next_action_suggestion)
        return (
            f"\n🚨 **[HAVE ISSUE: WORKER UNRESPONSIVE / CIRCUIT TRIPPED]**\n"
            f"- **Issue:** Worker `{alert['target_worker']}` failed or timed out on task `{alert['task_id']}`\n"
            f"- **Root Cause:** `{alert['root_cause']}`\n"
            f"- **Circuit State:** `{alert['circuit_state']}` (Execution halted to protect quota)\n"
            f"- **Quota Preservation:** `{alert['quota_status']}`\n\n"
            f"👉 **ONE NEXT VALID ACTION FOR OPERATOR:**\n"
            f"> {alert['one_next_valid_action']}\n"
        )

