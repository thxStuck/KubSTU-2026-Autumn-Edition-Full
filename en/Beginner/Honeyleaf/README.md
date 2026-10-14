# Honeyleaf

> **Category:** Beginner / PPC · **Event:** KubSTU CTF 2026 Autumn
> Author team: mpei_larpers · Source: https://ctftime.org/writeup/41133 (CTFtime community writeup)

## 📌 Task

The instance is a small Flask service, a "bakery receipts archive", at http://159.194.244.226:8083/. The main page lists ten files: five receipts and five macOS `._*` tails. The header also carries a link to the "Checkout", but there are only two live routes: `/` with the list and `/view?file=<name>`, which shows a file.

## 🏁 Solution

Inside `/view` the path is assembled with `os.path.join(RECEIPTS_DIR, name)`, where `name` is taken straight from the query string. An absolute path in `os.path.join` overrides the base folder, and nobody strips `../`. A classic arbitrary file read:

```bash
curl 'http://159.194.244.226:8083/view?file=/flag.txt'
# kubstu{h0n3yl34f_p4th_tr4v3rs4l_defd1128}
```

With the same bug I also pulled out the server source: `/view?file=/proc/self/cwd/app.py`. Right next to the vulnerable spot the developer had even left a TODO saying that validation "still needs to be added". For good measure I also checked `../../../flag.txt` and `/proc/self/root/flag.txt` — the content is the same.

Everything else in the task is empty: the receipts add up by their totals, the `._*` files are ordinary 177-byte AppleDouble blocks, and the routes `/download`, `/counter`, `/admin`, `/api` all return 404. The flag is handed over by the service itself; a single request is enough.

**Flag:** `kubstu{h0n3yl34f_p4th_tr4v3rs4l_defd1128}`
