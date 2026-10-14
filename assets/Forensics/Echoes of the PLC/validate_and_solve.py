

from __future__ import annotations

import collections
import ipaddress
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

PCAP = Path("/home/ubuntu/kubstu_wireshark_ctf/echoes_of_the_plc/echoes_of_the_plc.pcap")
CONTROLLER = ipaddress.ip_address("10.20.7.23").packed
PLC = ipaddress.ip_address("10.20.7.7").packed
BROKER = ipaddress.ip_address("10.20.7.19").packed
EXPECTED_FLAG = b"KubSTU{modbus_echoes_keep_the_secret}"


@dataclass
class Record:
    index: int
    timestamp: float
    packet: bytes


def parse_records() -> list[Record]:
    raw = PCAP.read_bytes()
    assert raw[:4] == b"\xd4\xc3\xb2\xa1", "PCAP magic is invalid"
    assert struct.unpack_from("<HH", raw, 4) == (2, 4), "PCAP version is invalid"
    offset = 24
    records: list[Record] = []
    while offset < len(raw):
        assert offset + 16 <= len(raw), "Truncated PCAP record header"
        seconds, microseconds, captured, original = struct.unpack_from("<IIII", raw, offset)
        assert captured == original, "Unexpected truncated frame"
        offset += 16
        assert offset + captured <= len(raw), "Truncated frame payload"
        records.append(Record(len(records), seconds + microseconds / 1_000_000, raw[offset:offset + captured]))
        offset += captured
    assert offset == len(raw), "Unexpected trailing data"
    return records


def ipv4(record: Record) -> tuple[int, bytes, bytes, bytes] | None:
    packet = record.packet
    if len(packet) < 34 or packet[12:14] != b"\x08\x00":
        return None
    ip_offset = 14
    header_length = (packet[ip_offset] & 0x0F) * 4
    if header_length < 20 or len(packet) < ip_offset + header_length:
        return None
    protocol = packet[ip_offset + 9]
    source = packet[ip_offset + 12:ip_offset + 16]
    destination = packet[ip_offset + 16:ip_offset + 20]
    return protocol, source, destination, packet[ip_offset + header_length:]


def tcp_fields(payload: bytes) -> tuple[int, int, int, bytes] | None:
    if len(payload) < 20:
        return None
    source_port, destination_port, sequence = struct.unpack_from("!HHL", payload)
    header_length = ((payload[12] >> 4) & 0x0F) * 4
    if header_length < 20 or len(payload) < header_length:
        return None
    return source_port, destination_port, sequence, payload[header_length:]


def icmp_fields(payload: bytes) -> tuple[int, int, int, bytes] | None:
    if len(payload) < 8:
        return None
    message_type, _, _, identifier, sequence = struct.unpack_from("!BBHHH", payload)
    return message_type, identifier, sequence, payload[8:]


def target_modbus_blocks(records: list[Record]) -> tuple[list[tuple[int, bytes]], list[int]]:
    blocks: list[tuple[int, bytes]] = []
    positions: list[int] = []
    for record in records:
        parsed = ipv4(record)
        if not parsed:
            continue
        protocol, source, destination, network_payload = parsed
        if protocol != 6 or source != PLC or destination != CONTROLLER:
            continue
        tcp = tcp_fields(network_payload)
        if not tcp:
            continue
        source_port, destination_port, _, application = tcp
        if source_port != 502 or destination_port != 49310 or len(application) < 9:
            continue
        transaction, protocol_id, length = struct.unpack_from("!HHH", application)
        if protocol_id != 0 or len(application) != 6 + length:
            continue
        unit, function, byte_count = application[6], application[7], application[8]
        if unit == 7 and function == 4 and byte_count == len(application) - 9:
            blocks.append((transaction, application[9:]))
            positions.append(record.index)
    return sorted(blocks), positions


def target_masks(records: list[Record]) -> dict[int, bytes]:
    masks: dict[int, bytes] = {}
    for record in records:
        parsed = ipv4(record)
        if not parsed:
            continue
        protocol, source, destination, network_payload = parsed
        if protocol != 1 or source != PLC or destination != CONTROLLER:
            continue
        icmp = icmp_fields(network_payload)
        if not icmp:
            continue
        message_type, identifier, sequence, data = icmp
        if message_type == 0 and identifier == 3199:
            masks[sequence] = data
    return masks


def mqtt_manifest_present(records: list[Record]) -> bool:
    segments: list[tuple[int, bytes]] = []
    for record in records:
        parsed = ipv4(record)
        if not parsed:
            continue
        protocol, source, destination, network_payload = parsed
        if protocol != 6 or source != BROKER or destination != CONTROLLER:
            continue
        tcp = tcp_fields(network_payload)
        if not tcp:
            continue
        source_port, destination_port, sequence, application = tcp
        if source_port == 1883 and destination_port == 49152 and application:
            segments.append((sequence, application))
    stream = b"".join(payload for _, payload in sorted(segments))
    return (
        b"facility/maintenance/calibration-manifest" in stream
        and b"transaction_id ascending" in stream
        and b"ICMP Echo Reply id=3199" in stream
        and b'"final":"zlib"' in stream
    )


def protocol_and_port_statistics(records: list[Record]) -> tuple[collections.Counter[str], set[int]]:
    protocols: collections.Counter[str] = collections.Counter()
    ports: set[int] = set()
    for record in records:
        if len(record.packet) < 14:
            continue
        ether_type = record.packet[12:14]
        if ether_type == b"\x08\x06":
            protocols["ARP"] += 1
            continue
        parsed = ipv4(record)
        if not parsed:
            continue
        protocol, _, _, payload = parsed
        protocols[{1: "ICMP", 6: "TCP", 17: "UDP"}.get(protocol, str(protocol))] += 1
        if protocol in (6, 17) and len(payload) >= 4:
            ports.update(struct.unpack_from("!HH", payload))
    return protocols, ports


def check_interleaving(records: list[Record], target_positions: list[int]) -> tuple[int, float]:
    gaps = [later - earlier - 1 for earlier, later in zip(target_positions, target_positions[1:])]
    assert gaps and max(gaps) >= 5, "Target blocks are not interleaved with enough unrelated traffic"
    separated_fraction = sum(gap >= 1 for gap in gaps) / len(gaps)
    assert separated_fraction >= 0.75, "Target blocks are too often adjacent"
    category_counts = []
    for start in range(0, len(records), 50):
        categories = set()
        for record in records[start:start + 50]:
            if len(record.packet) < 14:
                continue
            if record.packet[12:14] == b"\x08\x06":
                categories.add("ARP")
                continue
            parsed = ipv4(record)
            if parsed:
                categories.add({1: "ICMP", 6: "TCP", 17: "UDP"}.get(parsed[0], str(parsed[0])))
        category_counts.append(len(categories))
    average_categories = sum(category_counts) / len(category_counts)
    assert average_categories >= 2.5, "Traffic appears grouped instead of mixed"
    return max(gaps), separated_fraction


def main() -> None:
    raw = PCAP.read_bytes()
    records = parse_records()
    assert len(records) >= 30_000, "PCAP lacks sufficient volume"
    assert len(raw) >= 9_000_000, "PCAP lacks sufficient byte volume"
    assert EXPECTED_FLAG not in raw, "Flag is exposed in the capture"
    assert mqtt_manifest_present(records), "MQTT manifest was not found"

    blocks, positions = target_modbus_blocks(records)
    masks = target_masks(records)
    assert len(blocks) >= 5, "Target Modbus response blocks not found"
    assert len(blocks) == len(masks), "A mask is missing or extraneous"
    restored = bytearray()
    for transaction, encrypted in blocks:
        sequence = transaction - 0x4000
        mask = masks[sequence]
        assert len(mask) == len(encrypted), "Mask length does not match Modbus block"
        restored.extend(value ^ mask[index] for index, value in enumerate(encrypted))
    plaintext = zlib.decompress(bytes(restored))
    assert EXPECTED_FLAG in plaintext, "The intended reconstruction does not recover the flag"

    protocols, ports = protocol_and_port_statistics(records)
    required_ports = {67, 69, 80, 123, 161, 502, 514, 1883, 5683, 9001}
    assert required_ports.issubset(ports), "One or more required noise protocols are absent"
    max_gap, separated_fraction = check_interleaving(records, positions)

    stats = ", ".join(f"{name}: {count}" for name, count in sorted(protocols.items()))
    print(f"Validated PCAP: {len(records)} frames, {len(raw):,} bytes.")
    print(f"Link/network protocol counts: {stats}.")
    print(f"Target Modbus blocks: {len(blocks)}; correlated ICMP masks: {len(masks)}.")
    print(f"Interleaving: maximum unrelated-frame gap {max_gap}; non-adjacent target-block pairs {separated_fraction:.0%}.")
    print(f"Recovered flag: {EXPECTED_FLAG.decode()}.")


if __name__ == "__main__":
    main()
