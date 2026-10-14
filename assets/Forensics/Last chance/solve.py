#!/usr/bin/env python3
import re
import base64
import hashlib
from io import BytesIO
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def solve_challenge(pdf_path):
    print(f"[*] Анализ файла: {pdf_path}...")
    with open(pdf_path, 'rb') as f:
        content = f.read()

    # 1. Извлечение частей QR-кода из метаданных
    print("[1] Извлечение фрагментов QR-кода из метаданных...")
    # Используем более гибкий поиск для метаданных
    author_match = re.search(b"/Author\s*\((QR_PART1:.*?)\)", content, re.DOTALL)
    subject_match = re.search(b"/Subject\s*\((QR_PART2:.*?)\)", content, re.DOTALL)
    
    if not author_match or not subject_match:
        print("[-] Не удалось найти части QR-кода в метаданных.")
        # Попробуем найти просто строки QR_PART
        part1_match = re.search(b"QR_PART1:([A-Za-z0-9+/=]+)", content)
        part2_match = re.search(b"QR_PART2:([A-Za-z0-9+/=]+)", content)
        if part1_match and part2_match:
            part1_b64 = part1_match.group(1)
            part2_b64 = part2_match.group(1)
        else:
            return
    else:
        part1_b64 = author_match.group(1).split(b"QR_PART1:")[1].split(b")")[0]
        part2_b64 = subject_match.group(1).split(b"QR_PART2:")[1].split(b")")[0]

    # 2. Восстановление QR-кода
    print("[2] Реконструкция изображения QR-кода...")
    img1 = Image.open(BytesIO(base64.b64decode(part1_b64)))
    img2 = Image.open(BytesIO(base64.b64decode(part2_b64)))
    
    full_qr = Image.new('RGB', (img1.width, img1.height + img2.height))
    full_qr.paste(img1, (0, 0))
    full_qr.paste(img2, (0, img1.height))
    full_qr.save("reconstructed_qr.png")
    print("    [+] Изображение сохранено как reconstructed_qr.png.")
    
    # Соль из QR-кода
    salt = "7f3c92a1b4e5" 
    print(f"    [+] Соль (из QR): {salt}")

    # 3. Извлечение IV из объекта 100
    print("[3] Извлечение IV из объекта 100...")
    # Ищем объект 100 и его поток
    obj100_match = re.search(b"100 0 obj.*?stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL)
    if obj100_match:
        stream_data = obj100_match.group(1)
        # Если данные в hex (как в pasted_content_2.txt), попробуем конвертировать
        try:
            # Проверяем, является ли это hex-строкой
            if all(c in b"0123456789abcdefABCDEF \n\r" for c in stream_data[:20]):
                stream_bytes = bytes.fromhex(stream_data.decode('latin-1').strip().replace("\n", "").replace("\r", ""))
            else:
                stream_bytes = stream_data
        except:
            stream_bytes = stream_data
            
        # IV находится по смещению 11 (после заголовка и 2 байт длины)
        iv = stream_bytes[11:27] 
        print(f"    [+] IV найден: {iv.decode('latin-1', errors='ignore')}")
    else:
        print("[-] Объект 100 не найден.")
        return

    # 4. Извлечение первой части флага из объекта 101 (ASN.1)
    print("[4] Извлечение Part 1 из объекта 101...")
    obj101_match = re.search(b"101 0 obj.*?/Contents\s*<(.*?)>", content, re.DOTALL)
    if obj101_match:
        hex_data = obj101_match.group(1).decode('latin-1').strip().replace("\n", "").replace("\r", "").replace(" ", "")
        asn1_bytes = bytes.fromhex(hex_data)
        idx = asn1_bytes.find(b'\x80')
        if idx != -1:
            length = asn1_bytes[idx+1]
            part1 = asn1_bytes[idx+2:idx+2+length].decode()
            print(f"    [+] Part 1 найдена: {part1}")
        else:
            print("[-] Тег 0x80 не найден.")
            return
    else:
        print("[-] Объект 101 не найден.")
        return

    # 5. Извлечение шифротекста из объекта 102
    print("[5] Извлечение шифротекста из объекта 102...")
    obj102_match = re.search(b"102 0 obj.*?stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL)
    if obj102_match:
        ciphertext_raw = obj102_match.group(1)
        try:
            if all(c in b"0123456789abcdefABCDEF \n\r" for c in ciphertext_raw[:20]):
                ciphertext = bytes.fromhex(ciphertext_raw.decode('latin-1').strip().replace("\n", "").replace("\r", ""))
            else:
                ciphertext = ciphertext_raw
        except:
            ciphertext = ciphertext_raw
    else:
        print("[-] Объект 102 не найден.")
        return

    # 6. Дешифровка флага
    print("[6] Дешифровка флага...")
    key = hashlib.sha256(salt.encode() + iv).digest()[:32]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
    print(f"\n[!] ФЛАГ: {decrypted.decode()}")

if __name__ == "__main__":
    solve_challenge("challenge.pdf")
