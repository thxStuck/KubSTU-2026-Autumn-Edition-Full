
from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from cryptography.hazmat.primitives import serialization
from scapy.all import TCP, rdpcap

EXPECTED_PREFIX = b"KubSTU{"
END_MARKER = b"-----END RSA PRIVATE KEY-----"


def fail(message: str) -> None:
    raise SystemExit(f"[!] {message}")


def tcp_payloads(pcap_path: Path):
    packets = rdpcap(str(pcap_path))
    for packet in packets:
        if TCP in packet and bytes(packet[TCP].payload):
            yield packet, bytes(packet[TCP].payload)


def reassemble(pcap_path: Path, src: str, sport: int, dst: str, dport: int) -> bytes:
    records = []
    for packet, payload in tcp_payloads(pcap_path):
        tcp = packet[TCP]
        ip = packet.getlayer("IP")
        if ip is None:
            continue
        if ip.src == src and tcp.sport == sport and ip.dst == dst and tcp.dport == dport:
            records.append((int(tcp.seq), payload))
    if not records:
        fail(f"stream {src}:{sport} -> {dst}:{dport} not found")
    return b"".join(payload for _, payload in sorted(records))


def inspect_heartbeats(server_stream: bytes) -> bytes:
    pos = 0
    responses = []
    anomalies = 0
    while pos + 5 <= len(server_stream):
        content_type = server_stream[pos]
        length = int.from_bytes(server_stream[pos + 3:pos + 5], "big")
        end = pos + 5 + length
        if end > len(server_stream):
            break
        body = server_stream[pos + 5:end]
        if content_type == 24 and len(body) >= 3:
            hb_type = body[0]
            claimed = int.from_bytes(body[1:3], "big")
            actual_payload = len(body) - 3
            if claimed > actual_payload:
                anomalies += 1
            if hb_type == 2:
                responses.append(body[3:-84] if len(body) >= 87 else body[3:])
        pos = end
    if anomalies < 2:
        fail(f"expected Heartbleed anomalies, found {anomalies}")

    leaked = b"".join(responses)
    if b"LEAK" not in leaked:
        fail("heartbeat responses did not contain binary LEAK records")
    return leaked


def recover_key_from_leak(leaked: bytes) -> bytes:

    pos = 0
    chunks = {}
    xor_key = b"heartbeat-heap-2014"
    while pos + 8 <= len(leaked):
        if leaked[pos:pos + 4] != b"LEAK":
            pos += 1
            continue
        chunk_id = int.from_bytes(leaked[pos + 4:pos + 6], "big")
        length = int.from_bytes(leaked[pos + 6:pos + 8], "big")
        encoded = leaked[pos + 8:pos + 8 + length]
        if len(encoded) != length:
            fail("truncated LEAK record")
        chunks[chunk_id] = bytes(v ^ xor_key[i % len(xor_key)] for i, v in enumerate(encoded))
        pos += 8 + length
    if not chunks:
        fail("no LEAK records found in Heartbleed responses")
    pieces = [chunks[i] for i in sorted(chunks)]
    assembled = pieces.pop(0)
    while pieces:
        piece = pieces.pop(0)
        max_overlap = min(len(assembled), len(piece))
        overlap = next((n for n in range(max_overlap, 0, -1) if assembled[-n:] == piece[:n]), 0)
        assembled += piece[overlap:]
    candidate = assembled
    begin_marker = b"-----BEGIN RSA PRIVATE KEY-----"
    begin = candidate.find(begin_marker)
    end = candidate.find(END_MARKER, begin)
    if begin < 0 or end < 0:
        fail("could not reconstruct PEM RSA key from memory fragments")
    key = candidate[begin:end + len(END_MARKER)] + b"\n"
    serialization.load_pem_private_key(key, password=None)
    return key


def extract_zip(pcap_path: Path) -> bytes:
    stream = reassemble(pcap_path, "10.23.7.19", 445, "10.23.7.44", 51500)
    smb_marker = stream.find(b"\xfeSMB")
    if smb_marker < 0:
        fail("SMB2 marker not found")
    marker = stream.find(b"COUNT", smb_marker)
    if marker < 0 or marker + 7 > len(stream):
        fail("chunk count marker not found")
    count = int.from_bytes(stream[marker + 5:marker + 7], "big")
    pos = marker + 7
    chunks = {}
    xor_key = b"Northstar-IR-2026"
    while pos + 8 <= len(stream) and len(chunks) < count:
        if stream[pos:pos + 4] != b"CHNK":
            pos += 1
            continue
        chunk_id = int.from_bytes(stream[pos + 4:pos + 6], "big")
        length = int.from_bytes(stream[pos + 6:pos + 8], "big")
        encoded = stream[pos + 8:pos + 8 + length]
        if len(encoded) != length:
            fail("truncated CHNK record")
        chunks[chunk_id] = bytes(v ^ xor_key[i % len(xor_key)] for i, v in enumerate(encoded))
        pos += 8 + length
    if len(chunks) != count:
        fail(f"expected {count} chunks, decoded {len(chunks)}")
    zip_bytes = b"".join(chunks[i] for i in range(count))
    if not zip_bytes.startswith(b"PK\x03\x04"):
        fail("decoded chunk stream is not a ZIP")
    return zip_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Solve northstar-heartbleed in one command")
    parser.add_argument("root", nargs="?", default=".", help="extracted challenge directory")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    artifacts = root / "artifacts"
    pcap = artifacts / "incident.pcap"
    if not pcap.is_file():
        fail(f"missing {pcap}")

    tls_server = reassemble(pcap, "10.23.7.10", 443, "10.23.7.44", 49152)
    leaked = inspect_heartbeats(tls_server)
    (root / "heartbeat_leaks.bin").write_bytes(leaked)
    key = recover_key_from_leak(leaked)
    key_path = root / "server_recovered.key"
    key_path.write_bytes(key)

    zip_bytes = extract_zip(pcap)
    with ZipFile(BytesIO(zip_bytes)) as archive:
        if "flag.txt" not in archive.namelist():
            fail("flag.txt not found in extracted ZIP")
        flag = archive.read("flag.txt").strip()
    if not flag.startswith(EXPECTED_PREFIX) or not re.fullmatch(rb"KubSTU\{[^\r\n{}]+\}", flag):
        fail(f"unexpected flag format: {flag!r}")
    (root / "dropbox_payload_from_pcap.zip").write_bytes(zip_bytes)

    print("[+] Heartbleed anomalies: detected")
    print(f"[+] Leaked heartbeat bytes: {len(leaked)}")
    print(f"[+] RSA private key: {key_path}")
    print(f"[+] ZIP extracted from embedded SMB stream: {root / 'dropbox_payload_from_pcap.zip'}")
    print(flag.decode())
    return 0


if __name__ == "__main__":
    sys.exit(main())
