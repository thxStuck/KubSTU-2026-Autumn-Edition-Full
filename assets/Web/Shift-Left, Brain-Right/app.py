from flask import Flask, request, render_template_string

app = Flask(__name__)

PAGE = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Академия DevSecOps — Курсы по безопасной разработке</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
  background: #f6f5f4;
  color: #000;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
}
a { color: inherit; text-decoration: none; }

/* ---- Nav ---- */
.nav {
  position: sticky; top: 0; z-index: 100; height: 64px;
  background: rgba(246, 245, 244, 0.82);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  box-shadow:
    0px 0.7px 1.462px 0px rgb(0% 0% 0% / 0.015),
    0px 3px 9px 0px rgb(0% 0% 0% / 0.03);
}
.nav-inner {
  max-width: 1200px; margin: 0 auto; height: 100%;
  padding: 0 32px; display: flex; align-items: center;
  justify-content: space-between; gap: 24px;
}
.logo {
  font-size: 16px; font-weight: 600; letter-spacing: -0.2px;
  display: flex; align-items: center; gap: 8px; color: #000;
}
.logo-mark {
  width: 28px; height: 28px; border-radius: 8px;
  background: #0075de; display: grid; place-items: center; font-size: 15px;
}
.nav-links { display: flex; gap: 4px; list-style: none; }
.nav-links a {
  display: inline-block; padding: 8px 14px; border-radius: 8px;
  font-size: 14px; font-weight: 500; color: rgba(0,0,0,0.54);
  transition: color 200ms ease, background 200ms ease;
}
.nav-links a:hover { color: #000; background: rgba(0,0,0,0.04); }
.nav-cta { display: flex; gap: 8px; align-items: center; }

/* ---- Buttons ---- */
.btn {
  font-family: inherit; font-size: 14px; font-weight: 500;
  border-radius: 8px; padding: 8px 16px; border: none; cursor: pointer;
  transition: background 200ms ease, transform 200ms ease, color 200ms ease;
  display: inline-flex; align-items: center; gap: 6px; line-height: 1.2;
}
.btn-primary { background: #0075de; color: #ffffff; }
.btn-primary:hover { background: #0062bb; }
.btn-ghost { background: #e6f3fe; color: #0075de; }
.btn-ghost:hover { background: #d1e8fc; }
.btn-text { background: transparent; color: rgba(0,0,0,0.95); }
.btn-text:hover { background: rgba(0,0,0,0.05); }

/* ---- Hero ---- */
.hero { max-width: 1200px; margin: 0 auto; padding: 80px 32px 48px; text-align: center; }
.marks { display: flex; justify-content: center; gap: 10px; margin-bottom: 40px; }
.mark {
  width: 46px; height: 46px; border-radius: 9999px; background: #ffffff;
  display: grid; place-items: center; font-size: 22px; border: 2px solid;
  transition: transform 220ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.mark:nth-child(1) { border-color: #097fe8; }
.mark:nth-child(2) { border-color: #f64932; }
.mark:nth-child(3) { border-color: #ffb110; }
.mark:nth-child(4) { border-color: #62aef0; }
.mark:nth-child(5) { border-color: #e89d01; }
.mark:nth-child(6) { border-color: #b18164; }
.mark:nth-child(7) { border-color: #02093a; }
.mark:hover { transform: translateY(-4px) rotate(-6deg); }

h1.hero-title {
  font-size: 72px; font-weight: 500; line-height: 1.08;
  letter-spacing: -2.016px; color: #000000;
  margin: 0 auto 24px; max-width: 960px;
}
.pill {
  display: inline-block; background: #f6d5b8; color: #000000;
  border-radius: 9999px; padding: 4px 22px 6px; line-height: 1.05;
  white-space: nowrap;
}
.hero-sub {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 18px; line-height: 1.56; color: #615d59;
  max-width: 620px; margin: 0 auto 36px;
}
.hero-cta { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }

/* ---- Search ---- */
.search-section { max-width: 1200px; margin: 0 auto; padding: 24px 32px 64px; }
.search-form {
  max-width: 720px; margin: 0 auto; display: flex; gap: 8px;
  background: #ffffff; border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px; padding: 8px; transition: border-color 200ms ease;
}
.search-form:focus-within { border-color: rgba(0,0,0,0.18); }
.search-form input {
  flex: 1; border: none; outline: none; font-family: inherit;
  font-size: 16px; padding: 8px 12px; background: transparent; color: #000;
}
.search-form input::placeholder { color: #757575; }

/* ---- Result ---- */
.result-wrap { max-width: 720px; margin: 24px auto 0; }
.result-card {
  background: #ffffff; border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px; padding: 24px; text-align: left;
  transition: transform 200ms ease;
}
.result-label {
  font-size: 12px; font-weight: 500; letter-spacing: 0.12px;
  text-transform: uppercase; color: #757575; margin-bottom: 10px;
}
.result-value {
  font-size: 22px; font-weight: 500; letter-spacing: -0.242px;
  line-height: 1.35; color: #000;
  word-break: break-word; overflow-wrap: anywhere;
}

/* ---- Modules ---- */
.modules { max-width: 1200px; margin: 0 auto; padding: 24px 32px 80px; }
.section-head { margin-bottom: 40px; max-width: 720px; }
.section-head h2 {
  font-size: 48px; font-weight: 500; line-height: 1.08;
  letter-spacing: -1.89px; color: #000; margin-bottom: 12px;
}
.section-head p {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 18px; line-height: 1.56; color: #615d59;
}
.module-grid {
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px;
}
.module-card {
  background: #ffffff; border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px; padding: 24px; display: flex; flex-direction: column;
  gap: 12px; min-height: 240px; transition: transform 200ms ease;
}
.module-card:hover { transform: translateY(-3px); }
.module-card.is-marigold { background: #ffb110; border-color: transparent; }
.module-card.is-midnight {
  background: #02093a; border-color: transparent; color: #ffffff;
}

.tag {
  align-self: flex-start; font-size: 12px; font-weight: 500;
  letter-spacing: 0.12px; padding: 4px 12px; border-radius: 9999px;
  background: rgba(0,0,0,0.08); color: #000;
}
.module-card.is-marigold .tag { background: rgba(0,0,0,0.08); color: #000; }
.module-card.is-midnight .tag { background: rgba(255,255,255,0.15); color: #fff; }

.module-card h3 {
  font-size: 22px; font-weight: 600; letter-spacing: -0.242px;
  line-height: 1.27; margin-top: 4px;
}
.module-card p { font-size: 14px; line-height: 1.5; color: #615d59; flex: 1; }
.module-card.is-marigold p { color: rgba(0,0,0,0.7); }
.module-card.is-midnight p { color: rgba(255,255,255,0.72); }

.module-card .meta {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12px; color: #757575; padding-top: 12px;
  border-top: 1px solid rgba(0,0,0,0.06);
}
.module-card.is-marigold .meta { color: rgba(0,0,0,0.6); border-color: rgba(0,0,0,0.1); }
.module-card.is-midnight .meta { color: rgba(255,255,255,0.6); border-color: rgba(255,255,255,0.12); }

/* ---- Footer ---- */
footer {
  max-width: 1200px; margin: 0 auto; padding: 32px;
  border-top: 1px solid rgba(0,0,0,0.06);
  display: flex; justify-content: space-between; align-items: center;
  font-size: 14px; color: #757575; flex-wrap: wrap; gap: 16px;
}
footer .foot-links { display: flex; gap: 20px; }
footer a:hover { color: #000; }

@media (max-width: 900px) {
  h1.hero-title { font-size: 48px; letter-spacing: -1.5px; }
  .section-head h2 { font-size: 36px; letter-spacing: -1.2px; }
  .module-grid { grid-template-columns: 1fr; }
  .nav-links { display: none; }
}
@media (max-width: 600px) {
  h1.hero-title { font-size: 36px; letter-spacing: -1px; }
  .hero { padding: 48px 20px 32px; }
  .search-section, .modules { padding-left: 20px; padding-right: 20px; }
  .nav-inner { padding: 0 20px; }
}
</style>
</head>
<body>

<nav class="nav">
  <div class="nav-inner">
    <a class="logo" href="/">
      <span class="logo-mark">🛡️</span>
      <span>Академия DevSecOps</span>
    </a>
    <ul class="nav-links">
      <li><a href="#modules">Курсы</a></li>
      <li><a href="#tracks">Треки</a></li>
      <li><a href="#pricing">Тарифы</a></li>
      <li><a href="#about">О школе</a></li>
    </ul>
    <div class="nav-cta">
      <a class="btn btn-text" href="#">Войти</a>
      <a class="btn btn-primary" href="#modules">Начать бесплатно</a>
    </div>
  </div>
</nav>

<section class="hero">
  <div class="marks" aria-hidden="true">
    <div class="mark">👩‍💻</div>
    <div class="mark">🧑‍🔧</div>
    <div class="mark">🕵️</div>
    <div class="mark">👨‍🚀</div>
    <div class="mark">🧙</div>
    <div class="mark">🐧</div>
    <div class="mark">🦊</div>
  </div>

  <h1 class="hero-title">
    Учитесь <span class="pill">защищать</span><br>
    код, а не только писать его.
  </h1>

  <p class="hero-sub">
    Практические курсы по безопасной разработке: от SAST в CI до побега из контейнеров.
    Всё на реальных стендах, без сухой теории.
  </p>

  <div class="hero-cta">
    <a class="btn btn-primary" href="#search">Найти курс</a>
    <a class="btn btn-ghost" href="#modules">Смотреть программу</a>
  </div>
</section>

<section class="search-section" id="search">
  <form class="search-form" method="get" action="/">
    <input
      type="text"
      name="course"
      placeholder="Введите название курса (например, «DevSecOps»)"
      autocomplete="off"
    >
    <button class="btn btn-primary" type="submit">Искать</button>
  </form>

  <div class="result-wrap">
    <div class="result-card">
      <div class="result-label">Результат поиска</div>
      <div class="result-value">__COURSE_QUERY__</div>
    </div>
  </div>
</section>

<section class="modules" id="modules">
  <div class="section-head">
    <h2>Доступные модули</h2>
    <p>Три направления, с которых начинают почти все инженеры в академии.</p>
  </div>

  <div class="module-grid">
    <article class="module-card">
      <span class="tag">Модуль 01</span>
      <h3>Внедрение SAST/DAST в GitLab CI</h3>
      <p>Настройка статического и динамического анализа в пайплайне: правила, гейты, отчёты и работа с ложными срабатываниями.</p>
      <div class="meta"><span>6 часов · практика</span><span>→</span></div>
    </article>

    <article class="module-card is-marigold">
      <span class="tag">Модуль 02</span>
      <h3>Безопасность Docker-образов</h3>
      <p>Минимальные базовые образы, rootless-контейнеры, сканирование слоёв и разбор типичных ошибок в Dockerfile.</p>
      <div class="meta"><span>4 часа · практика</span><span>→</span></div>
    </article>

    <article class="module-card is-midnight">
      <span class="tag">Модуль 03</span>
      <h3>Управление секретами (HashiCorp Vault)</h3>
      <p>Динамические секреты, политики доступа, интеграция с Kubernetes и паттерны безопасной ротации ключей.</p>
      <div class="meta"><span>5 часов · практика</span><span>→</span></div>
    </article>
  </div>
</section>

<footer>
  <div>© 2026 Академия DevSecOps</div>
  <div class="foot-links">
    <a href="#">Политика</a>
    <a href="#">Контакты</a>
    <a href="#">GitHub</a>
  </div>
</footer>

</body>
</html>'''


@app.route('/')
def index():
    course_query = request.args.get('course', 'Введение в DevSecOps')

    # УЯЗВИМОСТЬ: пользовательский ввод подставляется в исходный текст
    # шаблона ДО его компиляции в Jinja2 (семантически эквивалентно
    # f-строке из оригинального кода).
    template = PAGE.replace('__COURSE_QUERY__', course_query)

    return render_template_string(template)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
