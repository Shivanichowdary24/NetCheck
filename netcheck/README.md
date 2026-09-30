# NetCheck - TCP Network Health Monitor

## Project Purpose

NetCheck is a lightweight tool that checks whether a TCP port on a given host
is reachable. You enter a hostname or IP address and a port number, and NetCheck
attempts a TCP connection, reports whether the target is online or offline, and
measures the connection latency in milliseconds.

It is designed to be small, self-contained, and easy to explain in a software
or networking interview.

## TCP Connection Concept

A TCP connection begins with a three-way handshake:

1. The client sends a **SYN** packet to the server.
2. The server replies with **SYN-ACK**.
3. The client sends **ACK** and the connection is established.

NetCheck acts as a TCP client. It uses Python's `socket.create_connection()`
to initiate this handshake against the target host and port. If the handshake
completes, the port is considered **online**. If the handshake fails (timeout,
refused, DNS failure), the port is considered **offline**.

The connection is closed immediately after the handshake completes — no data
is sent or received. This makes the check fast and non-intrusive.

## How Latency is Measured

Latency is measured as the wall-clock time from just before the connection
attempt starts to just after it succeeds:

```python
start = time.perf_counter()
socket.create_connection((host, port), timeout)
end = time.perf_counter()
latency_ms = (end - start) * 1000
```

`time.perf_counter()` is used instead of `time.time()` because it provides
monotonic, high-resolution timing suitable for short-duration measurements.

This latency includes:
- DNS resolution time (if the host is a hostname, not an IP)
- TCP SYN packet travel time to the server
- Server processing time for the SYN-ACK
- SYN-ACK travel time back to the client

It does **not** include application-layer handshake time (e.g., TLS negotiation),
since the connection is closed immediately after the TCP handshake.

## Architecture

```
Browser (HTML/CSS/JS)
        |
        | HTTP GET /api/check?host=...&port=...
        v
FastAPI (app.py)
        |
        | calls check_tcp_connection()
        v
network_checker.py
        |
        | socket.create_connection()
        v
   Target host:port
```

**Components:**

| File | Responsibility |
|------|---------------|
| `app.py` | FastAPI app, REST endpoints, in-memory history |
| `network_checker.py` | TCP connection logic, latency measurement, error handling |
| `static/index.html` | Frontend markup |
| `static/app.js` | Frontend logic (API calls, DOM updates) |
| `static/style.css` | Frontend styling |

**No database is used.** The last 10 check results are stored in an
in-memory `deque` and are lost when the server restarts.

## Installation

Requires Python 3.8 or later.

```bash
cd netcheck
pip install -r requirements.txt
```

## How to Run

```bash
cd netcheck
uvicorn app:app --reload --port 8000
```

Then open http://localhost:8000 in your browser.

## API Examples

### Check a host

```
GET /api/check?host=example.com&port=443
```

**Response (online):**
```json
{
  "target": "example.com",
  "port": 443,
  "online": true,
  "latency_ms": 24.53,
  "timestamp": "2026-09-30T12:00:00.000000+00:00",
  "error": null
}
```

**Response (offline):**
```json
{
  "target": "example.com",
  "port": 9999,
  "online": false,
  "latency_ms": null,
  "timestamp": "2026-09-30T12:00:01.000000+00:00",
  "error": "Connection refused by target"
}
```

### Optional timeout parameter

```
GET /api/check?host=example.com&port=443&timeout=5
```

The timeout is in seconds and defaults to 3.0. Range: 0.1 to 10.0.

### Health check

```
GET /health
```

**Response:**
```json
{ "status": "ok" }
```

### History

```
GET /api/history
```

Returns the last 10 check results (newest is last).

## Error Handling

NetCheck handles the following error cases gracefully:

| Error | Message | Behavior |
|-------|---------|----------|
| Invalid/empty host | "Host is required" | Returns offline, no connection attempt |
| Invalid port (out of range) | "Port must be between 1 and 65535" | Returns offline, no connection attempt |
| DNS resolution failure | "DNS resolution failed for host" | Returns offline |
| Connection timeout | "Connection timed out after Ns" | Returns offline |
| Connection refused | "Connection refused by target" | Returns offline |
| Other network error | "Network error: ..." | Returns offline |
| Unexpected exception | "Unexpected error: ..." | Returns offline |

The frontend validates inputs before sending the request and displays
error messages inline.

## Limitations

- **No persistence**: History is stored in memory only and is lost on restart.
- **No authentication**: The API is open to anyone who can reach the server.
- **TCP only**: Does not check UDP or application-layer (HTTP/HTTPS) health.
- **No TLS handshake**: Latency measures the TCP connection only, not TLS
  negotiation or application response time.
- **Single check per request**: No batching or scheduled monitoring.
- **Not a security tool**: This performs a basic connectivity check and should
  not be used as a port scanner.
- **Rate limiting**: None is implemented. Running this against hosts you do not
  own may be considered abuse.
