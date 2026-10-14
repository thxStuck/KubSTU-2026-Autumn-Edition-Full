# Honeyleaf

> **类别:** Beginner / PPC · **赛事:** KubSTU CTF 2026 Autumn
> 作者团队: mpei_larpers · 来源: https://ctftime.org/writeup/41133 (CTFtime 社区题解)

## 📌 题目

实例是一个小型 Flask 服务，一个"面包店收据档案"，位于 http://159.194.244.226:8083/。主页列出十个文件：五张收据和五个 macOS `._*` 残留文件。页头还挂着一个指向"收银台"的链接，但真正存活的路由只有两个：列出清单的 `/` 和显示文件的 `/view?file=<名称>`。

## 🏁 解题过程

在 `/view` 内部，路径是用 `os.path.join(RECEIPTS_DIR, name)` 拼出来的，其中 `name` 直接取自查询字符串。`os.path.join` 里的绝对路径会覆盖基础目录，而 `../` 也没有人过滤。这是经典的任意文件读取：

```bash
curl 'http://159.194.244.226:8083/view?file=/flag.txt'
# kubstu{h0n3yl34f_p4th_tr4v3rs4l_defd1128}
```

用同一个 bug 我还把服务器源码拉了出来：`/view?file=/proc/self/cwd/app.py`。就在漏洞处旁边，开发者甚至留下了一个 TODO，说校验"还需要补上"。为了保险起见，我又试了 `../../../flag.txt` 和 `/proc/self/root/flag.txt`——内容是一样的。

题目里其余部分都是空的：收据的金额都能对上，`._*` 是普通的 177 字节 AppleDouble 块，而路由 `/download`、`/counter`、`/admin`、`/api` 全都返回 404。flag 由服务本身交出来，一个请求就够了。

**Flag:** `kubstu{h0n3yl34f_p4th_tr4v3rs4l_defd1128}`
