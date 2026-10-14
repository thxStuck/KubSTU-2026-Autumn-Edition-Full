# Color Illusion

> **Category:** Hardware / Stego · **Event:** KubSTU CTF 2026 Autumn · **#263**
> Task author: [@van_1pi](https://t.me/van_1pi)

## 📌 Task

An artist claims this picture hides a message.
"Not all colors are what they seem," he said mysteriously.

**Files:** [stego-easy.zip](../../../assets/STEGO/Color%20Illusion/stego-easy.zip)

## 🏁 Solution

Unzip the archive and open `colors.gif`. The hint ("not all colors are what they seem") points at the **color values**, not the visible picture. Inspect the image's color planes / palette — e.g. with **Aperisolve**, **Stegsolve** (bit‑plane browser) or by dumping the palette — and the flag is spelled out by the anomalous color entries.

**Flag:** `KubSTU{Pr0bAbly_ea8y_steG0}`
