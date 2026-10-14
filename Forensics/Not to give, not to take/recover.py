
from __future__ import annotations

import argparse
import binascii
import struct
import zlib
from pathlib import Path

LOCAL = b"PK\x03\x04"
DESCRIPTOR = b"PK\x07\x08"
LOCAL_HEADER = struct.Struct("<IHHHHHIIIHH")
DATA_DESCRIPTOR = struct.Struct("<IIII")


def crc32(data: bytes) -> int:
    return binascii.crc32(data) & 0xFFFFFFFF


def decode_name(raw: bytes, flags: int) -> str:
    return raw.decode("utf-8" if flags & 0x0800 else "cp437")


def inflate_raw(data: bytes) -> bytes:
    return zlib.decompress(data, -15)


def recover(blob: bytes) -> list[tuple[str, bytes, int, int]]:
    records = []
    pos = 0

    while pos < len(blob):
        if blob[pos:pos + 4] != LOCAL:
            raise ValueError(f"Expected a local header at offset {pos}; got {blob[pos:pos + 4]!r}")
        if pos + LOCAL_HEADER.size > len(blob):
            raise ValueError(f"Truncated local header at offset {pos}")

        (signature, version, flags, method, mtime, mdate, header_crc,
         header_csize, header_usize, name_len, extra_len) = LOCAL_HEADER.unpack_from(blob, pos)
        if signature != 0x04034B50:
            raise ValueError(f"Invalid local-header signature at offset {pos}")
        name_start = pos + LOCAL_HEADER.size
        data_start = name_start + name_len + extra_len
        if data_start > len(blob):
            raise ValueError(f"Truncated name/extra fields at offset {pos}")
        name = decode_name(blob[name_start:name_start + name_len], flags)

        if flags & 0x0008:
            if method == 8:
                decoder = zlib.decompressobj(-15)
                contents = decoder.decompress(blob[data_start:])
                contents += decoder.flush()
                if not decoder.eof:
                    raise ValueError(f"Incomplete DEFLATE stream for {name!r}")
                compressed_len = len(blob[data_start:]) - len(decoder.unused_data)
                descriptor_at = data_start + compressed_len
                if blob[descriptor_at:descriptor_at + 4] != DESCRIPTOR:
                    raise ValueError(f"Missing signed data descriptor after {name!r}")
                if descriptor_at + DATA_DESCRIPTOR.size > len(blob):
                    raise ValueError(f"Truncated data descriptor for {name!r}")
                _, expected_crc, descriptor_csize, descriptor_usize = DATA_DESCRIPTOR.unpack_from(blob, descriptor_at)
                if descriptor_csize != compressed_len or descriptor_usize != len(contents):
                    raise ValueError(f"Data-descriptor sizes do not match for {name!r}")
                next_pos = descriptor_at + DATA_DESCRIPTOR.size
            elif method == 0:
                descriptor_at = blob.find(DESCRIPTOR, data_start)
                contents = None
                expected_crc = None
                next_pos = None
                while descriptor_at >= 0:
                    candidate = blob[data_start:descriptor_at]
                    if descriptor_at + DATA_DESCRIPTOR.size <= len(blob):
                        _, candidate_crc, candidate_csize, candidate_usize = DATA_DESCRIPTOR.unpack_from(blob, descriptor_at)
                        if (candidate_csize == len(candidate) == candidate_usize
                                and candidate_crc == crc32(candidate)):
                            contents = candidate
                            expected_crc = candidate_crc
                            next_pos = descriptor_at + DATA_DESCRIPTOR.size
                            break
                    descriptor_at = blob.find(DESCRIPTOR, descriptor_at + 1)
                if contents is None or expected_crc is None or next_pos is None:
                    raise ValueError(f"Could not validate stored data descriptor for {name!r}")
            else:
                raise ValueError(f"Unsupported method {method} for descriptor entry {name!r}")
        else:
            compressed_len = header_csize
            data_end = data_start + compressed_len
            if data_end > len(blob):
                raise ValueError(f"Compressed data for {name!r} extends past end of file")
            compressed = blob[data_start:data_end]
            if method == 0:
                contents = compressed
            elif method == 8:
                contents = inflate_raw(compressed)
            else:
                raise ValueError(f"Unsupported compression method {method} for {name!r}")
            expected_crc = header_crc
            if len(contents) != header_usize:
                raise ValueError(f"Uncompressed size mismatch for {name!r}: {len(contents)} != {header_usize}")
            next_pos = data_end

        records.append((name, contents, expected_crc, pos))
        pos = next_pos

    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="damaged ZIP file with local records only")
    parser.add_argument("-o", "--output", type=Path, default=Path("recovered"), help="output directory")
    args = parser.parse_args()

    blob = args.archive.read_bytes()
    records = recover(blob)
    args.output.mkdir(parents=True, exist_ok=True)

    for name, contents, expected_crc, offset in records:
        if Path(name).name != name or name in ("", ".", ".."):
            raise ValueError(f"Refusing unsafe output name: {name!r}")
        actual_crc = crc32(contents)
        status = "OK" if actual_crc == expected_crc else "CRC MISMATCH — PRESERVED AS DAMAGED"
        (args.output / name).write_bytes(contents)
        print(f"offset=0x{offset:04x}  {name!r:24}  {len(contents):4} bytes  CRC {status} "
              f"(expected {expected_crc:08x}, got {actual_crc:08x})")

    print(f"Recovered {len(records)} records. The damaged-CRC entry is still written to disk.")


if __name__ == "__main__":
    main()
