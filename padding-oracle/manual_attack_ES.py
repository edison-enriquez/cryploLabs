#!/usr/bin/python3
"""
Ataque manual de oraculo de relleno - version comentada en espanol.
Codespaces-ready: ORACLE_HOST (defecto 127.0.0.1).
"""
import os
import socket
from binascii import hexlify, unhexlify

HOST = os.getenv("ORACLE_HOST", "127.0.0.1")
PORT = int(os.getenv("ORACLE_PORT_L1", "5000"))

def xor(first, second):
    return bytearray(x ^ y for x, y in zip(first, second))

class PaddingOracle:
    def __init__(self, host, port) -> None:
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        ciphertext = self.s.recv(4096).decode().strip()
        self.ctext = unhexlify(ciphertext)

    def decrypt(self, ctext: bytes) -> None:
        self._send(hexlify(ctext))
        return self._recv()

    def _recv(self):
        resp = self.s.recv(4096).decode().strip()
        return resp

    def _send(self, hexstr: bytes):
        self.s.send(hexstr + b'\n')

    def __del__(self):
        self.s.close()


if __name__ == "__main__":
    print(f"Conectando a {HOST}:{PORT} ...")
    oracle = PaddingOracle(HOST, PORT)
    iv_and_ctext = bytearray(oracle.ctext)
    IV = iv_and_ctext[00:16]
    C1 = iv_and_ctext[16:32]
    C2 = iv_and_ctext[32:48]
    print("C1:  " + C1.hex())
    print("C2:  " + C2.hex())

    D2 = bytearray(16)
    for i in range(16):
        D2[i] = C1[i]

    CC1 = bytearray(16)

    K = 1
    for i in range(256):
        CC1[16 - K] = i
        status = oracle.decrypt(IV + CC1 + C2)
        if status == "Valid":
            print("Valido: i = 0x{:02x}".format(i))
            print("CC1: " + CC1.hex())

    P2 = xor(C1, D2)
    print("P2:  " + P2.hex())
