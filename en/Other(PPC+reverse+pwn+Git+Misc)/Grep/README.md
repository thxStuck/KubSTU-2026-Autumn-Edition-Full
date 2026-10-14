# Grep: almost but not quite

> **Category:** DevSecOps / Git · **Difficulty:** Easy · **Event:** KubSTU CTF 2026 Autumn

## 📌 Task

The security team has detected suspicious activity: service keys have leaked from the production environment. A developer claims to have noticed the error promptly, reverted the changes, and insists that the secret is no longer present in the clean repository.

However, the security team disagrees with him. They provided you with this archive and asked you to find the very service key he's talking about.

Flag format: KubCTF{...}

**Files:** [ctf_repo.zip](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/Grep/ctf_repo.zip)

## 🏁 Solution

The task is based on a dangling commit.

1. Unzip the archive.
2. Run `git fsck --lost-found` in the terminal. You'll get the message `dangling commit 3bdea0f23e83a6a3757ae2b7c7b781c174493d26`.
3. Now view this commit: `git show 3bdea0f23e83a6a3757ae2b7c7b781c174493d26`

![screen](../../../assets/Other(PPC+reverse+pwn+Git+Misc)/Grep/screen.png)
