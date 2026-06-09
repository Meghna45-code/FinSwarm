"""
FinSwarm Server Startup Script
Binds uvicorn to BOTH IPv4 (127.0.0.1) and IPv6 (::1) on port 8000.

Why: On Windows, 'localhost' resolves to ::1 (IPv6) in the browser but
uvicorn's default --host 0.0.0.0 only covers IPv4, causing 'Failed to fetch'.
This script passes pre-bound sockets for both address families.
"""

import asyncio
import socket
import sys
import os

import uvicorn


async def main():
    port = int(os.getenv("PORT", "8000"))

    config = uvicorn.Config(
        "backend.app.main:app",
        log_level="info",
        # host/port are overridden by the sockets below
    )
    server = uvicorn.Server(config)

    sockets = []

    # --- IPv4 socket (127.0.0.1) ---
    try:
        ipv4_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ipv4_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ipv4_sock.bind(("127.0.0.1", port))
        ipv4_sock.listen(128)
        sockets.append(ipv4_sock)
        print(f"[startup] Bound to IPv4 127.0.0.1:{port}")
    except OSError as e:
        print(f"[startup] WARNING: Could not bind IPv4 127.0.0.1:{port} — {e}")

    # --- IPv6 socket (::1) ---
    try:
        ipv6_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        ipv6_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # IPV6_V6ONLY=1 keeps this socket strictly IPv6 (no dual-stack ambiguity)
        ipv6_sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        ipv6_sock.bind(("::1", port))
        ipv6_sock.listen(128)
        sockets.append(ipv6_sock)
        print(f"[startup] Bound to IPv6 ::1:{port}")
    except OSError as e:
        print(f"[startup] WARNING: Could not bind IPv6 ::1:{port} — {e}")

    if not sockets:
        print("[startup] ERROR: Failed to bind any socket. Is port 8000 already in use?")
        sys.exit(1)

    print(f"[startup] FinSwarm running — open http://localhost:{port}/ in your browser")
    await server.serve(sockets=sockets)


if __name__ == "__main__":
    asyncio.run(main())
