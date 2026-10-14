# Biba 'n Boba

> **类别：** OSINT · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

![biba_boba.jpg](../../../assets/OSINT/Biba%20'n%20Boba/biba_boba.jpg)

在大学校园的某个地方住着两个“居民”。它们什么都不说，哪儿也不去，几个月来一直在内院里注视着每一个人。大学忍不住要介绍它们——去看看官方账号吧。

Flag 就是大学 Telegram 频道里一篇帖子的链接。

**文件：** [biba_boba.jpg](../../../assets/OSINT/Biba%20'n%20Boba/biba_boba.jpg)

## 🏁 解答

### 第 1 步：初步观察

照片里是一个不大的艺术装置，两块长了眼睛的石头。这物件看似平平无奇，但从描述可知大学曾介绍过它们。

### 第 2 步：搜索

据此，我们前往大学的社交网络：vk.com/kubstu_official 或 t.me/kubstu_official。在官方页面上，我们先用关键词搜索：`камень, камни, двое`（石头、石头[复数]、两个）等等。

![search_res.png](../../../assets/OSINT/Biba%20'n%20Boba/search_res.png)

搜索结果里第一条就引人注目。

![searched_post.png](../../../assets/OSINT/Biba%20'n%20Boba/searched_post.png)

这正是我们要找的帖子。现在把链接取出来，用 `KubSTU{}` 包起来——`https://t.me/kubstu_official/9761`

题目解决 :)

**Flag：** `KubSTU{https://t.me/kubstu_official/9761}`
