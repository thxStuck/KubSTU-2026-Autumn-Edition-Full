# Grep: almost but not quite

> **类别：** DevSecOps / Git · **难度：** Easy · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

安全团队发现了可疑活动：生产环境中泄露了服务密钥。一位开发者声称自己及时发现了错误，回滚了改动，并坚称干净的仓库里已经不再有这个密钥了。

然而安全团队并不认同他的说法。他们把这个压缩包交给你，请你找出他所说的那个服务密钥。

Flag 格式：KubCTF{...}

**文件：** [ctf_repo.zip](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/Grep/ctf_repo.zip)

## 🏁 解答

本题的核心是一个悬空（dangling）提交。

1. 解压压缩包。
2. 在终端中运行 `git fsck --lost-found`。你会得到消息 `dangling commit 3bdea0f23e83a6a3757ae2b7c7b781c174493d26`。
3. 现在查看这个提交：`git show 3bdea0f23e83a6a3757ae2b7c7b781c174493d26`

![screen](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/Grep/screen.png)
