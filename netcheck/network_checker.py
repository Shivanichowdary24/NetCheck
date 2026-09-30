"""TCP connection health checker.

Performs a single TCP connect to a host:port, measures the round-trip
latency in milliseconds, and returns a structured result.
"""

import socket
import time
import ssl
from dataclasses import dataclass
from typing import Optional


DEFAULT_TIMEOUT = 3.0  # seconds


@dataclass
class CheckResult:
    target: str
    port: int
    online: bool
    latency_ms: Optional[float]
    timestamp: str
    error: Optional[str]

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "port": self.port,
            "online": self.online,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
            "error": self.error,
        }


def _validate_port(port: int) -> Optional[str]:
    if not isinstance(port, int):
        return "Port must be an integer"
    if port < 1 or port > 65535:
        return "Port must be between 1 and 65535"
    return None


def check_tcp_connection(
    host: str, port: int, timeout: float = DEFAULT_TIMEOUT
) -> CheckResult:
    """Attempt a TCP connection to host:port.

    Returns a CheckResult with online status, latency in ms, and an
    error message if the connection failed.
    """
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).isoformat()

    if not host or not isinstance(host, str):
        return CheckResult(
            target=str(host) if host else "",
            port=port,
            online=False,
            latency_ms=None,
            timestamp=timestamp,
            error="Host is required",
        )

    port_error = _validate_port(port)
    if port_error:
        return CheckResult(
            target=host,
            port=port,
            online=False,
            latency_ms=None,
            timestamp=timestamp,
            error=port_error,
        )

    try:
        start = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            end = time.perf_counter()
            latency_ms = round((end - start) * 1000, 2)
        return CheckResult(
            target=host,
            port=port,
            online=True,
            latency_ms=latency_ms,
            timestamp=timestamp,
            error=None,
        )
    except socket.gaierror:
        return CheckResult(
            target=host, port=port, online=False, latency_ms=None,
            timestamp=timestamp, error="DNS resolution failed for host",
        )
    except socket.timeout:
        return CheckResult(
            target=host, port=port, online=False, latency_ms=None,
            timestamp=timestamp, error=f"Connection timed out after {timeout}s",
        )
    except ConnectionRefusedError:
        return CheckResult(
            target=host, port=port, online=False, latency_ms=None,
            timestamp=timestamp, error="Connection refused by target",
        )
    except OSError as exc:
        return CheckResult(
            target=host, port=port, online=False, latency_ms=None,
            timestamp=timestamp, error=f"Network error: {exc.strerror or str(exc)}",
        )
    except Exception as exc:  # pragma: no cover - safety net
        return CheckResult(
            target=host, port=port, online=False, latency_ms=None,
            timestamp=timestamp,
            error=f"Unexpected error: {type(exc).__name__}: {exc}",
        )
