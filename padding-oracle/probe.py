import os
import socket
HOST = os.getenv("ORACLE_HOST", "127.0.0.1")
for port in (5000, 6000):
    s = socket.create_connection((HOST, port), timeout=5)
    data = s.recv(4096).decode().strip()
    print(f"port={port} len_hex={len(data)} len_bytes={len(data)//2}")
    print(data)
    print()
    s.close()
