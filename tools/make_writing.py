import re, sys, pathlib
root = pathlib.Path(sys.argv[1])
BASE = "https://clarity31765.github.io"
cfg = {
 "en": dict(src="index.html", out="writing/index.html", lang="en",
   title="Writing &amp; AI in the lab — Oliver Lee",
   h1="Writing &amp; AI in the lab",
   dek="Notes on analytical methods and quality, and how I use AI in the lab with every claim checked against the source.",
   desc="Notes on analytical methods and quality by Oliver Lee, and how AI is used in the lab with every claim checked against the source.",
   home="Oliver Lee", back="Back to the main page", skip="Skip to content",
   self_url="/writing/", other_url="/ko/writing/"),
 "ko": dict(src="ko/index.html", out="ko/writing/index.html", lang="ko",
   title="글 · 실험실의 AI — 이동춘 (Oliver Lee)",
   h1="글 · 실험실의 AI",
   dek="분석법과 품질에 관한 노트, 그리고 모든 주장을 원문으로 확인하며 AI를 실험실에서 쓰는 방법.",
   desc="이동춘(Oliver Lee)의 분석법·품질 노트와, 원문 대조를 거친 실험실 AI 활용 사례.",
   home="이동춘", back="메인 페이지로 돌아가기", skip="본문 바로가기",
   self_url="/ko/writing/", other_url="/writing/"),
}
for k, c in cfg.items():
    html = (root/c["src"]).read_text(encoding="utf-8")
    secs = []
    for sid in ("writing", "ai"):
        m = re.search(r'(    <section id="%s" .*?</section>)' % sid, html, re.S)
        secs.append(m.group(1))
    body = "\n\n".join(secs)
    # links: notes/ -> ../notes/ (en) ; ko page notes/ -> ../notes/ as well (ko/writing -> ko/notes)
    body = body.replace('href="notes/', 'href="../notes/')
    css = re.search(r'assets/style\.css\?v=(\d+)', html).group(1)
    vis = re.search(r'assets/visits\.js\?v=(\d+)', html).group(1)
    up = "../" if k == "en" else "../../"
    en_href = "../writing/" if k=="ko" else "./"
    ko_href = "../ko/writing/" if k=="en" else "./"
    out = f'''<!doctype html>
<html lang="{c["lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c["title"]}</title>
<meta name="description" content="{c["desc"]}">
<meta name="theme-color" content="#0a0f17">
<link rel="canonical" href="{BASE}{c["self_url"]}">
<link rel="alternate" hreflang="en" href="{BASE}/writing/">
<link rel="alternate" hreflang="ko" href="{BASE}/ko/writing/">
<link rel="alternate" hreflang="x-default" href="{BASE}/writing/">
<link rel="icon" href="{up}assets/favicon.svg?v=2" type="image/svg+xml">
<link rel="icon" href="{up}assets/favicon-32.png?v=2" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png?v=2">
<link rel="stylesheet" href="{up}assets/style.css?v={css}">
<meta property="og:type" content="website">
<meta property="og:title" content="{c["h1"]}">
<meta property="og:description" content="{c["desc"]}">
<meta property="og:url" content="{BASE}{c["self_url"]}">
</head>
<body>
<a class="skip" href="#content">{c["skip"]}</a>
<div class="topbar"><nav class="lang" aria-label="Language"><a href="{en_href}" lang="en" hreflang="en"{' aria-current="true"' if k=="en" else ''}>EN</a><a href="{ko_href}" lang="ko" hreflang="ko"{' aria-current="true"' if k=="ko" else ''}>한국어</a></nav></div>

<div class="article-shell">
  <p class="crumb"><a href="../">{c["home"]}</a></p>

  <header class="article-head">
    <h1>{c["h1"]}</h1>
    <p class="dek">{c["dek"]}</p>
  </header>

  <main id="content" class="content" style="padding-top:0">
<!-- Generated from {c["src"]} (sections #writing and #ai) by tools/make_writing.py. Edit the main page, then regenerate. -->
{body}

    <p style="margin-top:48px"><a href="../">{c["back"]}</a></p>
  </main>
</div>
<script src="{up}assets/visits.js?v={vis}" defer></script>
</body>
</html>
'''
    p = root/c["out"]; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(out, encoding="utf-8")
    print("wrote", p)
