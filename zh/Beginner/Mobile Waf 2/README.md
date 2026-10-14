# Mobile Waf 2

> **类别:** Beginner / PPC · **赛事:** KubSTU CTF 2026 Autumn
> 作者团队: mpei_larpers · 来源: https://ctftime.org/writeup/41135 (CTFtime 社区题解)

## 📌 题目

位于 193.168.46.146:31832 的服务是 "WAF Gauntlet"。它进行 100 个回合：发来描述某个请求的 JSON（方法、路径、query、头部、正文），并期待回复一个字符串——`allow` 或 `block`。只需拦截那些带有真实、可执行攻击的请求（XSS、SQLi、SSTI、SSRF、命令注入、XXE/NoSQL/反序列化、HTTP 滥用、LFI/path traversal），其余一律放行，包括那些刁钻但无害的"仿冒品"。错一次游戏就结束。每回合 3 秒，每条连接 150 秒。

## 🏁 解题过程

这个服务最大的弱点是它会自己解释自己的错误。答错时会收到 `# wrong at round N: expected block (xss)`，然后连接关闭——也就是说，该回合的攻击类别直接泄露在错误文本里。数据集的采集就源于此："全部 allow"策略会在第一个含攻击的回合就失败（而且服务会告诉你是哪一类），"全部 block"策略则会在第一个无害回合失败。只有当下一个回合到来时，某回合才算被确认，所以标签不是猜的，而是精确的。

这样就积累出一个语料库：325 个已确认样本，外加约 500 个标注了攻击类型的回合。不用逆向任何二进制——整道题变成了一个分类问题。

接下来是一个基于规则的分类器（waf_filter.py）。每个字段都被展开成若干表示形式——原始、最多三次 url-decode、去掉 SQL 注释后的、%uXXXX、HTML 实体、base64 块——然后按每个类别的规则集逐一跑过。规则中比较有意思的有：`alg:none` 的 JWT、Shellshock、带 `--checkpoint-action=exec` 的 tar、`powershell -enc`、带 `-write` 的 ImageMagick、Log4Shell、.NET BinaryFormatter 和 Ruby Marshal 块、base64 包裹的 SSRF 目标、CRLF、request smuggling、X-Forwarded-Host、HTTP 参数污染、path confusion。同样重要的是不要被无害的"仿冒品"绊倒：文本中被转义的标记、像 `{{customer_name}}` 这样的模板变量、普通语句中夹带的 SQL 词、散文里的 `file://`、以及正常 URL 中看起来敏感的名字。

离线验证：497 个已标注样本上 0 处不一致，325 个已确认样本上也是 0。实战运行：`python3 solve.py` 第一次尝试就通过了 100/100，服务发来 `# cleared 100/100` 以及 JSON 形式的 flag：

```
{"flag": "kubstu{w4f_g4untl3t_100_r0unds_e7075354d674}"}
```

**Flag:** `kubstu{w4f_g4untl3t_100_r0unds_e7075354d674}`
