# Last chance

> **Category:** Forensics · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

We are given a suspicious PDF file. The goal is to analyze it and recover the hidden flag.

**Files:** [solve.py](../../../assets/Forensics/Last%20chance/solve.py)

## 🏁 Solution

The first thing to do when analyzing a suspicious PDF is to check its properties and metadata. This can be done with `exiftool`, `pdfid`, or simply by opening the file in a text editor and searching for dictionary objects.

### Step 1: Metadata analysis
In the metadata fields **Author** and **Subject**, strange strings in Base64 format are found:
- **Author**: `QR_PART1:<base64_data>`
- **Subject**: `QR_PART2:<base64_data>`

### Step 2: Reconstructing the QR code
We extract both strings and decode them from Base64 into PNG format. We obtain two halves of an image. By stitching them vertically (the top above the bottom), we get a complete QR code.

Scanning the QR code yields the salt value for AES:
```text
salt=7f3c92a1b4e5
```

### Step 3: Searching for hidden objects in the PDF structure
PDF files can store objects that are not displayed visually. We use `pdf-parser` or a search for the string `obj`. We find three suspicious objects added to the end of the file:

1.  **Object 100 (`/JBIG2Decode`)**: Inside the data stream, an initialization vector (**IV**) is hidden. The data is represented as a hex string.
    *   **IV**: `a1b2c3d4e5f67890` (extracted at offset 11 in the byte representation).

2.  **Object 101 (`/Sig`)**: A digital signature object containing an ASN.1 DER structure in the `/Contents` field. Inside the structure, under the non-standard tag `0x80`, the first part of the flag is hidden.
    *   **Part 1**: `part1_f4k3_s1g`

3.  **Object 102 (`/Crypt`)**: Contains an encrypted data stream in hex format — our final flag.

### Step 4: Decrypting the flag
Now we have all the components:
- **Salt (from QR)**: `7f3c92a1b4e5`
- **IV (from object 100)**: `a1b2c3d4e5f67890`
- **Ciphertext**: from object 102
- **First part of the flag (from object 101)**: `part1_f4k3_s1g`

The AES-256 key is computed as the SHA-256 hash of the concatenation of the salt and the IV:
$$\text{Key} = \text{SHA256}(\text{Salt} + \text{IV})[:32]$$

Using the AES-256-CBC algorithm with the obtained key and IV, we decrypt the data from object 102.

**Flag:** `KubSTU{part1_f4k3_s1g_metadata_stitching_is_fun_abe8776b}`
