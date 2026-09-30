"""FastAPI application for NetCheck - TCP Network Health Monitor.

Provides a REST API to check TCP connectivity to a host:port and keeps
the last 10 check results in memory (no database).
"""

from collections import deque
from typing import Deque, List

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from network_checker import check_tcp_connection, CheckResult, DEFAULT_TIMEOUT


app = FastAPI(title="NetCheck", version="1.0.0")

# In-memory history of the last 10 checks
_history: Deque[dict] = deque(maxlen=10)


@app.get("/health")
def health() -> dict:
    """Health endpoint for the service itself."""
    return {"status": "ok"}


@app.get("/api/check")
def api_check(
    host: str = Query(..., description="Hostname or IP address to check"),
    port: int = Query(..., ge=1, le=65535, description="TCP port to check"),
    timeout: float = Query(DEFAULT_TIMEOUT, ge=0.1, le=10.0, description="Connection timeout in seconds"),
) -> JSONResponse:
    """Check TCP connectivity to host:port and return the result."""
    result: CheckResult = check_tcp_connection(host, port, timeout)
    data = result.to_dict()
    _history.append(data)
    return JSONResponse(content=data)


@app.get("/api/history")
def api_history() -> List[dict]:
    """Return the last 10 check results (newest last)."""
    return list(_history)


# Serve the frontend from /static
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")
