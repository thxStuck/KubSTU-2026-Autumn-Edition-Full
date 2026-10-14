# Not to give, not to take

> **Category:** Forensics · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

In archive.zip the local ZIP records are left, but the central directory (Central Directory, CD) and the end-of-archive record (EOCD) are missing. The files must be recovered without trusting a naive search for the PK\x03\x04 signature, and the integrity of the extracted data must be verified.

**Files:** [recover.py](../../../assets/Forensics/Not%20to%20give,%20not%20to%20take/recover.py)

## 🏁 Solution

The archive contains six real records. The following peculiarities are intentionally left in it:

- secret.txt uses Deflate and the general-purpose bit 3 flag (0x0008): in the local header the CRC and sizes are zero, and a Data Descriptor is placed after the compressed stream.
- café.txt is written in the old CP437 encoding: the byte 0x82 in the name means é; the UTF-8 flag is not set.
- evidence_03.bin has a CRC mismatch and must be extracted with an explicit corruption mark.
- calibration.dat uses the Deflate method, but its compressed stream contains the bytes of a false PK\x03\x04 signature.
- The Store (0) and Deflate (8) methods are used.
- The flag is stored in the compressed secret.txt.

ZIP utilities usually use the central directory as an index of records. Here the archive starts with correct local headers, but the index is removed. Therefore standard tools may report that the archive is corrupted, or may not show the file list.

The absence of the trailing structures can be checked, for example, like this:

```bash
xxd -g 1 archive.zip | tail
# CD starts with PK 01 02; EOCD starts with PK 05 06.
# Neither signature is present in this file.
```

Searching for PK\x03\x04 is also not a sufficient solution: the signature appears once inside the compressed data of calibration.dat. If you start parsing it as another record, you get false fields and a wrong archive boundary.

All multi-byte numbers in ZIP are stored in little-endian. The start of the compressed data is computed like this:

```text
data_start = header_offset + 30 + filename_length + extra_length
```

For Store, the compressed data is the file bytes themselves. For Deflate, ZIP uses a raw DEFLATE stream: in Python it is decompressed via zlib.decompress(data, -15), i.e. without the zlib wrapper.

A reliable strategy in this case is to go from a known boundary to a known boundary.

1. Check the signature at the current offset.
2. Read the local header, the name and the extra fields.
3. If bit 3 is cleared, take the length of the compressed data from the local header and skip past that data.
4. If bit 3 is set, do not use the zero sizes from the header. For Deflate, determine the end of the stream by means of the decoder, then read the Data Descriptor.
5. Decompress the file, compute the CRC-32 and compare it with the expected value.
6. Look for the next record only by the computed boundary, not by scanning every byte for PK\x03\x04.

In the Data Descriptor of this task there is a PK\x07\x08 signature, followed by CRC-32, compressed size and uncompressed size — 4 bytes each. In total, the descriptor occupies 16 bytes.

For Deflate, the end of the stream can be obtained via zlib.decompressobj(-15): after the DEFLATE stream ends, the decoder sets eof, and everything that comes after the stream (in this case, the descriptor) is returned in unused_data. This allows the boundary to be determined correctly, without taking a false signature inside the stream for a new record.

secret.txt has the flag 0x0008 set. Therefore the local CRC and size fields are zero and do not describe the actual data. After the raw Deflate stream, the decoder finds the Data Descriptor:

- CRC-32: 88097019
- compressed size: 54 bytes
- uncompressed size: 53 bytes

The descriptor signature is at offset 227 (0xe3). After reading the 16-byte descriptor, the next local record starts exactly at offset 243.

In total, the records must be parsed sequentially, the descriptor handled, the names decoded and the CRC verified.

**Flag:** `KubSTU{local_headers_lie_central_directory_does_not}`
