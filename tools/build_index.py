#!/usr/bin/env python3
"""units.json 을 읽어 메인 목차(index.html)를 만든다.

유닛을 추가할 때는 units.json 만 고치고 이걸 다시 돌린다.
색은 읽기 페이지(english-reading-html 템플릿)의 팔레트를 그대로 가져와
목차 → 읽기 → 문제지가 한 덩어리로 보이게 맞췄다.

사용법:
    python3 tools/build_index.py
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS = {
    "done":  ("학습완료", "done"),
    "doing": ("학습중",   "doing"),
    "todo":  ("아직",     "todo"),
}

CSS = """
:root{
  --paper:#FBF7EE; --ink:#2A2520; --muted:#8A8073; --line:#E5DCC8;
  --carrot:#E0712F; --carrot-soft:#FBE6D7; --leaf:#5C7A4A; --leaf-soft:#E7EEDF;
  --sky:#3E6B8F; --card:#FFFFFF;
  --shadow:0 1px 2px rgba(42,37,32,.06),0 8px 24px rgba(42,37,32,.06);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--paper);color:var(--ink);
  font-family:ui-sans-serif,system-ui,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  line-height:1.6;padding:0 0 80px;
}
.wrap{max-width:900px;margin:0 auto;padding:0 22px}

header{padding:44px 0 22px;border-bottom:2px solid var(--ink)}
.eyebrow{
  font-size:12px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--carrot);font-weight:700;margin:0 0 10px;
}
h1{
  font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-size:44px;line-height:1.05;margin:0;letter-spacing:-.01em;
}
.tagline{color:var(--muted);font-size:14px;margin:12px 0 0}

/* 진행 요약 */
.summary{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 0}
.stat{
  background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:10px 14px;box-shadow:var(--shadow);
}
.stat b{display:block;font-size:22px;line-height:1.1}
.stat span{font-size:12px;color:var(--muted)}
.stat.done b{color:var(--leaf)}
.stat.doing b{color:var(--carrot)}
.stat.ready b{color:var(--sky)}

/* 필터 */
.filters{
  position:sticky;top:0;z-index:20;background:rgba(251,247,238,.92);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
  margin:26px -22px 30px;padding:12px 22px;display:flex;gap:8px;flex-wrap:wrap;
}
.chip{
  font:inherit;font-size:13px;font-weight:600;cursor:pointer;
  border:1px solid var(--line);background:var(--card);color:var(--ink);
  padding:7px 14px;border-radius:999px;transition:.15s;
}
.chip:hover{border-color:var(--carrot);color:var(--carrot)}
.chip.on{background:var(--carrot);border-color:var(--carrot);color:#fff}

/* 테마 묶음 */
.group{margin:0 0 34px}
.group > h2{
  font-size:13px;letter-spacing:.1em;color:var(--muted);font-weight:700;
  margin:0 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line);
}
.group[hidden]{display:none}

.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}

.card{
  background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:14px 16px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:10px;
}
.card[hidden]{display:none}
.card.pending{background:transparent;box-shadow:none;border-style:dashed}
.card .top{display:flex;align-items:baseline;gap:8px}
.card .no{
  font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.06em;
  flex-shrink:0;padding-top:2px;
}
.card .en{
  font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-size:19px;font-weight:700;line-height:1.2;
}
.card .ko{font-size:13px;color:var(--muted)}
.card .meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted)}

.badge{
  font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;
  border:1px solid transparent;white-space:nowrap;
}
.badge.done{background:var(--leaf-soft);color:var(--leaf)}
.badge.doing{background:var(--carrot-soft);color:var(--carrot)}
.badge.todo{background:#EFEBE2;color:var(--muted)}

.actions{display:flex;gap:8px;margin-top:auto}
.btn{
  flex:1;text-align:center;text-decoration:none;font-size:13px;font-weight:600;
  border:1px solid var(--line);border-radius:999px;padding:8px 10px;
  color:var(--ink);background:var(--paper);transition:.15s;
}
.btn:hover{border-color:var(--carrot);color:var(--carrot)}
.btn.primary{background:var(--carrot);border-color:var(--carrot);color:#fff}
.btn.primary:hover{filter:brightness(1.06);color:#fff}
.pending .note{font-size:12px;color:var(--muted);font-style:italic}

.empty{color:var(--muted);font-size:14px;padding:20px 0}
.empty[hidden]{display:none}

footer{
  margin-top:20px;padding-top:20px;border-top:1px solid var(--line);
  font-size:13px;color:var(--muted);
}
footer b{color:var(--ink)}

@media (max-width:520px){
  h1{font-size:34px}
  .cards{grid-template-columns:1fr}
}
"""

JS = """
var chips = document.querySelectorAll('.chip');
var cards = document.querySelectorAll('.card');
var groups = document.querySelectorAll('.group');
var empty = document.getElementById('empty');

function apply(f){
  cards.forEach(function(c){
    c.hidden = !(f === 'all'
      || (f === 'ready' && c.dataset.ready === '1')
      || c.dataset.status === f);
  });
  // 카드가 하나도 안 남은 테마는 제목까지 숨긴다
  var shown = 0;
  groups.forEach(function(g){
    var n = g.querySelectorAll('.card:not([hidden])').length;
    g.hidden = n === 0;
    shown += n;
  });
  empty.hidden = shown > 0;
}

chips.forEach(function(chip){
  chip.addEventListener('click', function(){
    chips.forEach(function(c){ c.classList.toggle('on', c === chip); });
    apply(chip.dataset.filter);
  });
});
"""


def card(u):
    n = u["n"]
    label, cls = STATUS[u.get("status", "todo")]
    ready = bool(u.get("ready"))

    meta = [f'<span class="badge {cls}">{label}</span>']
    if u.get("date"):
        meta.append(f'<span>{html.escape(u["date"])}</span>')
    if u.get("min"):
        meta.append(f'<span>{u["min"]}분</span>')

    if ready:
        actions = (f'<div class="actions">'
                   f'<a class="btn primary" href="read/unit{n:02d}.html">📖 읽기</a>'
                   f'<a class="btn" href="print/unit{n:02d}.html">🖨 A4 출력</a>'
                   f'</div>')
    else:
        actions = '<div class="actions"><span class="note">자료 준비 중</span></div>'

    return (
        f'<article class="card{"" if ready else " pending"}"'
        f' data-status="{u.get("status", "todo")}" data-ready="{"1" if ready else "0"}">'
        f'<div class="top"><span class="no">UNIT {n}</span>'
        f'<span class="en">{html.escape(u["en"])}</span></div>'
        f'<div class="ko">{html.escape(u["ko"])}</div>'
        f'<div class="meta">{"".join(meta)}</div>'
        f'{actions}'
        f'</article>'
    )


def main():
    data = json.load(open(os.path.join(ROOT, "units.json"), encoding="utf-8"))
    units = [u for g in data["groups"] for u in g["units"]]

    counts = {k: sum(1 for u in units if u.get("status", "todo") == k)
              for k in STATUS}
    ready = sum(1 for u in units if u.get("ready"))

    groups = "".join(
        f'<section class="group"><h2>{html.escape(g["theme"])}</h2>'
        f'<div class="cards">{"".join(card(u) for u in g["units"])}</div></section>'
        for g in data["groups"]
    )

    chips = "".join(
        f'<button class="chip{" on" if f == "all" else ""}" data-filter="{f}">{t}</button>'
        for f, t in [("all", f"전체 {len(units)}"), ("ready", f"자료 있음 {ready}"),
                     ("done", f"학습완료 {counts['done']}"),
                     ("doing", f"학습중 {counts['doing']}"),
                     ("todo", f"아직 {counts['todo']}")]
    )

    out = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(data["subtitle"])} — {html.escape(data["course"])}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <header>
    <p class="eyebrow">{html.escape(data["course"])}</p>
    <h1>{html.escape(data["subtitle"])}</h1>
    <p class="tagline">유닛을 고르면 <b>읽기 페이지</b>로 들어갑니다.
      단어에 손을 대면 뜻이 뜨고, 문장마다 해석·듣기 버튼이 있어요.
      종이에 뽑아 풀려면 <b>A4 출력</b>을 누르세요.</p>
    <div class="summary">
      <div class="stat done"><b>{counts['done']}</b><span>학습완료</span></div>
      <div class="stat doing"><b>{counts['doing']}</b><span>학습중</span></div>
      <div class="stat"><b>{counts['todo']}</b><span>아직</span></div>
      <div class="stat ready"><b>{ready}</b><span>자료 준비됨</span></div>
    </div>
  </header>

  <div class="filters">{chips}</div>

  {groups}

  <p class="empty" id="empty" hidden>해당하는 유닛이 없어요.</p>

  <footer>
    <b>인쇄</b> — A4 출력 페이지에서 <b>Ctrl+P</b>(맥은 ⌘+P), 배율 100%,
    「배경 그래픽」을 켜고 인쇄하세요. 문제 2장 + 부모용 정답·지도 노트 1장이 나옵니다.
    정답지를 빼고 뽑으려면 위쪽의 <b>「정답지 빼고 인쇄」</b>를 체크하세요.
  </footer>

</div>
<script>{JS}</script>
</body>
</html>
"""
    path = os.path.join(ROOT, "index.html")
    open(path, "w", encoding="utf-8").write(out)
    print(f"생성: index.html  (유닛 {len(units)}개, 자료 준비됨 {ready}개)")


if __name__ == "__main__":
    main()
