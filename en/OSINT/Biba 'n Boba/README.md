# Biba 'n Boba

> **Category:** OSINT · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

![biba_boba.jpg](../../../assets/OSINT/Biba%20'n%20Boba/biba_boba.jpg)

Somewhere on the university grounds two of them live. They say nothing, go nowhere, and have been watching everyone in the inner courtyard for several months already. The university couldn't resist telling about them — take a look at the official accounts.

The flag will be a link to a post from the university's Telegram channel.

**Files:** [biba_boba.jpg](../../../assets/OSINT/Biba%20'n%20Boba/biba_boba.jpg)

## 🏁 Solution

### Step 1. Initial inspection

In the photo we have a small art object, two stones with eyes. The object seems unremarkable, but from the description we understand that the university has told about them.

### Step 2. Search

Based on the above, we head to the university's social networks: vk.com/kubstu_official or t.me/kubstu_official. On the official pages we start by searching for keywords: `камень, камни, двое` (stone, stones, two), etc.

![search_res.png](../../../assets/OSINT/Biba%20'n%20Boba/search_res.png)

Literally the very first result in the output catches the eye.

![searched_post.png](../../../assets/OSINT/Biba%20'n%20Boba/searched_post.png)

And here is the post we're interested in. Now we grab the link and wrap it in `KubSTU{}` — `https://t.me/kubstu_official/9761`

The task is solved :)

**Flag:** `KubSTU{https://t.me/kubstu_official/9761}`
