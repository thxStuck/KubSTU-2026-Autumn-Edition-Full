# Bank-1

> **分类：** Web · **赛事：** KubSTU CTF 2026 Autumn

## 📌 题目

CAPY-CAPY 是一个基于 Flask 的网上银行。Flag 在一个封闭的「Flag Shop」中出售，只有高级（premium）客户才能访问；付款从账户中扣除，并由 Telegram 机器人通过一次性 offer 令牌确认。

唯一的高级用户是 `mgalankov@4274`，账户为 `ACC004`，余额约 149 万 ₽。Flag 售价 1000 ₽，所以整个题目归结为一件事：以他的名义完成一笔付款。

![银行的首页](../../../assets/Web/Bank-1/01_landing.png)

*起点。除了登录和注册表单之外别无他物——这个门面既不泄露用户名，也不泄露账号。*

每一笔转账都用一个 16 字符的 HMAC 签名来签署，而服务器**只有**在校验 PIN 码之后才会下发该签名。PIN 是八位数字，不以明文存储，暴力破解被限制为每分钟 20 次尝试。这正是题目要求绕过的那堵墙。

## 🏁 解题思路

### 概要

三个相互独立的缺陷构成的链条。单独任何一个都无法拿到 flag；合在一起则可完全接管他人的账户。

| № | 漏洞 | 要点 |
|---|---|---|
| 1 | 访问控制失效（CWE-639） | 内部的重置密码接口不校验角色，并在响应中返回受害者的登录名 |
| 2 | 第二因素泄露（CWE-200） | OTP 请求直接把验证码放在 HTTP 响应体中返回 |
| 3 | 密钥命名空间混用 | 2FA 验证码和支付签名由同一个生成器产生，因此 OTP 被当作签名接受 |

### 阶段 0. 侦察

我们注册一个普通账户——它作为立足点：几乎所有有意思的接口都需要一个有效的 JWT。

![注册表单](../../../assets/Web/Bank-1/02_register.png)

*表单要求填写俄文全名、驾照和一个 ALTCHA PoW 验证码。登录名由服务器生成：名字的首字母 + 姓氏的音译 + 四位随机数字。*

接下来是整个侦察阶段最关键的发现。网站页脚有一个「API Documentation」链接，它指向一个**无需授权、公开的 Swagger**。

![Swagger UI](../../../assets/Web/Bank-1/04_swagger_top.png)

*`/api/docs`——完整的规范以匿名方式提供。这里列出了界面上任何地方都没有链接的接口。*

![Administration 部分](../../../assets/Web/Bank-1/05_swagger_admin.png)

*「Administration」部分——只有一个接口：`POST /api/admin/reset_password`，「按标识符为某个用户设置新密码」。*

> **为什么这是一个发现。** 界面里确实有改密码的功能——在「Profile」页面。但那个表单要求当前密码，并且只能改自己的。来自 Swagger 的这个接口既不要求当前密码，又接受*别人的*标识符。

### 阶段 1. IDOR：别人的密码与登录名泄露

该接口仅由 `@jwt_required()` 保护——也就是说，它只检查调用者是否登录，仅此而已：

```python
# app.py — /api/admin/reset_password
target = User.query.get(target_user_id)
# нет проверки роли и нет сверки target_user_id с текущим пользователем
target.password = generate_password_hash(new_password)
```

标识符是小整数，所以我们逐个枚举。而这里就是第二个缺陷：**响应会返回**我们刚刚改掉密码的那个用户的登录名。事先并不需要知道受害者的昵称——接口自己就把它说了出来。

![枚举 target_user_id](../../../assets/Web/Bank-1/06_idor_enum.png)

```
uid=1 [200] Пароль пользователя aalice@1234 изменён
uid=2 [200] Пароль пользователя bbob@5678 изменён
uid=3 [200] Пароль пользователя ccharlie@9012 изменён
uid=4 [200] Пароль пользователя mgalankov@4274 изменён   ← премиум
uid=5 [200] Пароль пользователя ihakerov@1424 изменён    ← это мы сами
uid=6 [404] Целевой пользователь не найден
```

四个当中哪一个是高级用户，事先并不知道，但总共只有四个：我们逐个登录，看谁的商店会打开。

### 阶段 2. 接管高级账户

我们用自己设定的密码以 `mgalankov@4274` 登录。

![mgalankov 的仪表盘](../../../assets/Web/Bank-1/07_victim_dashboard.png)

*账户 ACC004，余额 1 486 808.50 ₽，以及付款历史。账户是我们的了。*

![Flag Shop](../../../assets/Web/Bank-1/08_flag_shop.png)

*「Flag Shop」打开了——`user.is_premium` 检查通过。*

### 阶段 3. 那堵墙：PIN 码

我们填入 offer 令牌，点「Buy」——随即撞上了这道题存在的理由。

![PIN 码提示](../../../assets/Web/Bank-1/09_pin_wall.png)

*要拿到交易签名，需要一个八位 PIN。在每分钟 20 次请求的限制下暴力破解 10⁸ 种可能——那要上千年。*

既定流程是：页面把 PIN 发送到 `/api/get_signature`，服务器校验后下发一个与收款方、金额和描述牢牢绑定的签名。该签名一次性有效，存活五分钟。它无法被伪造——HMAC 密钥在服务器上。

所以，签名不是要去伪造，而是要*通过另一条通道合法地获取*。

### 阶段 4. 自我暴露的第二因素

Swagger 中有一个「Security」部分，里面有接口 `POST /api/2fa/send`——「发送 OTP 以确认一笔转账」。我们调用它并查看响应：

![OTP 泄露](../../../assets/Web/Bank-1/10_otp_leak.png)

```json
POST /api/2fa/send  {"purpose": "transfer"}

{
  "masked_number": "+7-***-**-****",
  "otp": "31f0818ebf466718",
  "status": "sent",
  "timestamp": 1789858049
}
```

电话号码被仔细地打码了——但一次性验证码本身却以明文躺在响应里。

> **决定一切的细节。** OTP 不是短信里的六位数字。它是*16 个十六进制字符*——正是银行在收据上打印交易签名所用的那个格式。

### 阶段 5. 用 OTP 代替签名

格式吻合并非偶然。2FA 验证码由与支付签名相同的生成器产生：

```python
# app.py — генерация 2FA-кода
ts  = int(datetime.now(timezone.utc).timestamp())
otp = generate_signature_from_timestamp(ts)   # тот же HMAC, что у подписи
```

而转账处理逻辑在为 PIN 下发的列表中找不到签名后，便转去在未使用的 OTP 中寻找它——并予以接受：

```python
# app.py — /transfer
ok, reason = consume_pending_signature(...)   # не прошло: PIN мы не вводили
if not ok:
    otp_rec = TwoFactorCode.query.filter_by(
        user_id=user.id, code=transaction_signature,
        purpose='transfer', used=False).first()
    if otp_rec:
        ok = True
        transaction_timestamp = otp_rec.signature_timestamp
```

我们手动提交转账表单，把 OTP 放进 `transaction_signature` 字段。完全不输入 PIN：

```http
POST /transfer

to_account             = FLAG_SHOP
amount                 = 1000.00
product_id             = 1
token                  = <offer-токен из Telegram-бота>
transaction_timestamp  = 1789858049
transaction_signature  = 31f0818ebf466718   ← это OTP
```

![购买已确认](../../../assets/Web/Bank-1/11_purchase_ok.png)

*「Purchase confirmed! Флаг отправлен в Telegram бот.」余额恰好减少了 1000 ₽。*

收据毫无疑问地表明，充当签名的正是那个一次性验证码：

![交易收据](../../../assets/Web/Bank-1/12_receipt.png)

*「Transaction signature」字段——`31f0818ebf466718`，就是那个 OTP。*

### Flag

```
KubSTU{0tp_1s_th3_s1gnatur3_c4py_b4nk_0wn3d}
```

机器人在 `FLAG_CONTENT` 中只保存内部部分，并自行将其包裹（`f'KubSTU{{{flag_content}}}'`）。在购买确认后，它把该字符串作为消息发送，并以 `flag.txt` 文件再复制一份。

### 根源：签名到底哪里出了问题

签名仅由两个字段计算得出：

```python
# notquiterandom.py
message = timestamp.to_bytes(8, "big") + counter.to_bytes(8, "big")
mac = hmac.new(self._key, message, hashlib.sha256).digest()
```

其中既没有金额，也没有收款方，也没有付款方。唯一把签名与某笔具体付款绑定起来的，是服务器端的白名单（whitelist），而记录要在 PIN 校验之后才会进入其中。OTP 分支完全绕过了这个白名单，随之而来的是所有绑定都失效了：一个下发出来的 OTP 就能授权一笔**转到任意账户、任意金额**的转账。

这里跟密码学毫无关系——HMAC-SHA256 是老实的，密钥也没有泄露。被破坏的是信任模型：为一个目的（确认用户拥有手机）下发的密钥，被用于另一个目的（确认用户批准了某笔具体付款）而接受。

### 一路上有哪些阻碍

| 机制 | 作用 | 如何绕过 |
|---|---|---|
| ALTCHA PoW 验证码 | 在登录、注册、重置密码和 OTP 请求时都需要。challenge 一次性有效，存活 120 秒 | 在浏览器中求解：找到使 `sha256(salt + n)` 等于 challenge 的 `n` |
| 基于 User-Agent 的反机器人 | 在 POST 请求上拦截 `python-requests`、`curl`、`HeadlessChrome` 之类 | 用真实浏览器操作，或设置一个普通的 UA |
| 速率限制 | 重置密码——10/分钟，PIN 校验——20/分钟，按 IP 计 | 枚举五个 ID 在限制之内；对暴力破解 PIN 来说这永远都不够 |

> **值得一提的死胡同。**「Security」页面上有一个双因素开关。它写入 `is_2fa` 字段，而该字段在转账逻辑中一次都没被读取过——切换它什么都不会改变。一个假线索。

### 如何修复

1. 在 `/api/admin/reset_password` 中**增加角色检查**，并且不要在响应中返回登录名——一个中性的「done」就够了。
2. **绝不在 HTTP 响应中下发 OTP。** 第二因素必须走另一条通道，否则它就不是「第二」因素。
3. **分离密钥命名空间。** OTP 和支付签名必须用不同的密钥、不同的上下文来计算——这样一来，把一个替换成另一个在原理上就不再可行。
4. **对付款本身进行签名。** 把付款方、收款方、金额和描述纳入签名，而不仅仅是 timestamp。
5. 在 `/transfer` 中**移除那条绕过分支**：签名只接受来自 PIN 校验后下发的白名单。
6. **让登录响应一致。** 现在「user not found」和「wrong password」是不同的消息，这本身就允许枚举登录名。

*本次通关在 stand `127.0.0.1:35801` 上完成，该环境以生产配置从题目源码部署。截图是在一次连续的运行过程中拍摄的；flag 由 Telegram 机器人作为同一次购买的结果下发。*

**Flag:** `KubSTU{0tp_1s_th3_s1gnatur3_c4py_b4nk_0wn3d}`
