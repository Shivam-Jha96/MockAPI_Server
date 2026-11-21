"""In-memory thread-safe state store for Mock API Server."""
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class MemoryStore:
    """Thread-safe state store for outbound messages, quality status, and telemetry."""

    def __init__(self, max_outbox_size: int = 1000) -> None:
        self._lock = threading.Lock()
        self._max_outbox_size = max_outbox_size
        self._outbox: List[Dict[str, Any]] = []
        self._quality_ratings: Dict[str, str] = {}
        self._metrics: Dict[str, int] = {
            "inbound_webhooks_total": 0,
            "outbound_messages_total": 0,
            "opt_out_events_total": 0,
            "crypto_operations_total": 0,
            "parse_schedule_requests_total": 0,
        }

    def add_outbox_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Store an outbound message in bounded outbox (pruning oldest if exceeding limit)."""
        with self._lock:
            record = {
                **message,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
            self._outbox.append(record)
            if len(self._outbox) > self._max_outbox_size:
                self._outbox = self._outbox[-self._max_outbox_size:]
            self._metrics["outbound_messages_total"] += 1
            return record

    def get_outbox(
        self,
        phone_number_id: Optional[str] = None,
        recipient: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored outbound messages with optional filtering."""
        with self._lock:
            results = list(self._outbox)
            if phone_number_id:
                results = [m for m in results if m.get("phone_number_id") == phone_number_id]
            if recipient:
                results = [m for m in results if m.get("to") == recipient]
            return results

    def get_message_by_wamid(self, wamid: str) -> Optional[Dict[str, Any]]:
        """Find a message by its wamid."""
        with self._lock:
            for m in self._outbox:
                if m.get("wamid") == wamid:
                    return m
            return None

    def clear_outbox(self) -> int:
        """Clear all messages in outbox and return count of deleted items."""
        with self._lock:
            count = len(self._outbox)
            self._outbox.clear()
            return count

    def set_quality_rating(self, phone_number_id: str, rating: str) -> None:
        """Set WABA phone number quality rating (GREEN, YELLOW, RED)."""
        normalized_rating = rating.upper()
        if normalized_rating not in ("GREEN", "YELLOW", "RED"):
            normalized_rating = "GREEN"
        with self._lock:
            self._quality_ratings[phone_number_id] = normalized_rating

    def get_quality_rating(self, phone_number_id: str) -> str:
        """Get WABA phone number quality rating, defaults to GREEN."""
        with self._lock:
            return self._quality_ratings.get(phone_number_id, "GREEN")

    def increment_metric(self, metric_name: str, amount: int = 1) -> None:
        """Increment a named telemetry metric counter."""
        with self._lock:
            self._metrics[metric_name] = self._metrics.get(metric_name, 0) + amount

    def get_metric(self, metric_name: str) -> int:
        """Get value of a named telemetry metric."""
        with self._lock:
            return self._metrics.get(metric_name, 0)

    def get_metrics_prometheus(self, default_phone_id: str = "109876543210987") -> str:
        """Generate Prometheus exposition format string."""
        with self._lock:
            inbound = self._metrics.get("inbound_webhooks_total", 0)
            outbound = self._metrics.get("outbound_messages_total", 0)
            opt_out = self._metrics.get("opt_out_events_total", 0)
            crypto = self._metrics.get("crypto_operations_total", 0)
            nlu = self._metrics.get("parse_schedule_requests_total", 0)

            # Quality ratings
            rating_lines = []
            phone_ids = set(self._quality_ratings.keys())
            if default_phone_id not in phone_ids:
                phone_ids.add(default_phone_id)

            for pid in sorted(phone_ids):
                curr = self._quality_ratings.get(pid, "GREEN")
                for r in ("GREEN", "YELLOW", "RED"):
                    val = 1.0 if r == curr else 0.0
                    rating_lines.append(f'waba_quality_rating{{phone_number_id="{pid}",rating="{r}"}} {val}')

        ratings_str = "\n".join(rating_lines)
        return (
            "# HELP waba_quality_rating WABA Phone Number Quality Status (1.0 indicates active status)\n"
            "# TYPE waba_quality_rating gauge\n"
            f"{ratings_str}\n"
            "# HELP inbound_webhooks_total Total inbound webhook events received\n"
            "# TYPE inbound_webhooks_total counter\n"
            f"inbound_webhooks_total {inbound}\n"
            "# HELP outbound_messages_total Total outbound messages sent via Graph API\n"
            "# TYPE outbound_messages_total counter\n"
            f"outbound_messages_total {outbound}\n"
            "# HELP opt_out_events_total Total opt-out requests processed\n"
            "# TYPE opt_out_events_total counter\n"
            f"opt_out_events_total {opt_out}\n"
            "# HELP crypto_operations_total Total KMS cryptographic operations performed\n"
            "# TYPE crypto_operations_total counter\n"
            f"crypto_operations_total {crypto}\n"
            "# HELP parse_schedule_requests_total Total NLU schedule parsing requests\n"
            "# TYPE parse_schedule_requests_total counter\n"
            f"parse_schedule_requests_total {nlu}\n"
        )

    def reset(self) -> None:
        """Reset state store for clean testing."""
        with self._lock:
            self._outbox.clear()
            self._quality_ratings.clear()
            for k in self._metrics:
                self._metrics[k] = 0


# Global singleton instance
memory_store = MemoryStore()
