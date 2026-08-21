#!/usr/bin/env python3
"""units.json 을 읽어 부모용 목록(list.html)을 만든다.

메인 페이지는 아이가 보는 지도(index.html, tools/build_map.py)다. 이쪽은
날짜·소요시간·상태 필터가 필요한 부모용 표라서 따로 둔다 — 지도에 이걸
다 넣으면 아이 화면이 관리 화면이 되어 버린다.

색은 읽기 페이지(english-reading-html 템플릿)의 팔레트를 그대로 가져와
목록 → 읽기 → 문제지가 한 덩어리로 보이게 맞췄다.

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
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Gaegu:wght@400;700&display=swap');
:root{
  --paper:#E8F0F7; --grid:#D3E2EF; --ink:#2A3F55; --muted:#6B8299; --line:#B9CDDD;
  --carrot:#E0384F; --carrot-soft:#FDE8EC; --leaf:#2F8F6B; --leaf-soft:#DEF0E8;
  --sky:#3F7FA8; --gold:#F2B632; --card:#FFFFFF;
  --shadow:0 3px 0 rgba(42,63,85,.13);
  --f-round:'Jua','Malgun Gothic','Apple SD Gothic Neo',sans-serif;
  --f-hand:'Gaegu','Malgun Gothic',cursive;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;color:var(--ink);
  background:
    linear-gradient(var(--grid) 1px,transparent 1px) 0 0/26px 26px,
    linear-gradient(90deg,var(--grid) 1px,transparent 1px) 0 0/26px 26px,
    var(--paper);
  font-family:ui-sans-serif,system-ui,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  line-height:1.6;padding:0 0 80px;
}
.wrap{max-width:900px;margin:0 auto;padding:0 22px}

header{padding:40px 0 22px;border-bottom:3px dashed var(--line)}
.eyebrow{
  font-size:12px;letter-spacing:.18em;text-transform:uppercase;
  color:var(--carrot);font-weight:700;margin:0 0 10px;
}
h1{
  font-family:var(--f-round);font-size:40px;line-height:1.1;margin:0;letter-spacing:-.5px;
  text-shadow:2px 2px 0 #fff, 4px 4px 0 var(--line);
}
.tagline{color:var(--muted);font-size:14px;margin:12px 0 0}
.eyebrow{font-family:var(--f-hand);font-size:17px;letter-spacing:0;text-transform:none}

/* 진행 요약 */
.summary{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 0}
.stat{
  background:var(--card);border:2.5px solid var(--ink);border-radius:14px;
  padding:10px 16px;box-shadow:var(--shadow);
}
.stat b{display:block;font-family:var(--f-round);font-size:24px;line-height:1.1}
.stat span{font-size:12px;color:var(--muted)}
.stat.done b{color:var(--leaf)}
.stat.doing b{color:var(--carrot)}
.stat.ready b{color:var(--sky)}
.stat.doing b{color:var(--carrot)}

/* 필터 */
.filters{
  position:sticky;top:0;z-index:20;background:rgba(232,240,247,.94);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
  margin:26px -22px 30px;padding:12px 22px;display:flex;gap:8px;flex-wrap:wrap;
}
.chip{
  font:inherit;font-family:var(--f-round);font-size:14px;cursor:pointer;
  border:2.5px solid var(--ink);background:var(--card);color:var(--ink);
  padding:6px 15px;border-radius:999px;transition:.15s;
  box-shadow:0 3px 0 rgba(42,63,85,.16);
}
.chip:hover{transform:translateY(-2px)}
.chip:active{transform:translateY(1px);box-shadow:0 1px 0 rgba(42,63,85,.16)}
.chip.on{background:var(--gold);color:var(--ink)}

/* 테마 묶음 */
.group{margin:0 0 34px}
.group > h2{
  font-family:var(--f-round);font-size:16px;color:var(--ink);font-weight:400;
  margin:0 0 12px;padding-bottom:8px;border-bottom:2px dashed var(--line);
}
.group > h2 .ico{margin-right:6px}
.group > h2 .rng{font-family:var(--f-hand);font-size:15px;color:var(--muted);margin-left:6px}
.group[hidden]{display:none}

.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}

.card{
  background:var(--card);border:2.5px solid var(--ink);border-radius:16px;
  padding:14px 16px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:10px;
}
.card .stamp{font-size:22px;line-height:1;flex-shrink:0}
.card[hidden]{display:none}
.card.pending{background:transparent;box-shadow:none;border-style:dashed;border-color:var(--line)}
.card.is-done{background:#FFF4F5;border-color:var(--carrot)}
.card .top{display:flex;align-items:baseline;gap:8px}
.card .no{
  font-family:var(--f-round);font-size:12px;color:#fff;background:var(--ink);
  border-radius:999px;padding:1px 8px;flex-shrink:0;
}
.card .en{font-family:var(--f-round);font-size:19px;line-height:1.2}
.card .ko{font-size:13px;color:var(--muted)}
.card .meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted)}

.badge{
  font-family:var(--f-hand);font-size:14px;font-weight:700;padding:0 9px;
  border-radius:999px;border:2px solid transparent;white-space:nowrap;
}
.badge.done{background:var(--leaf-soft);color:var(--leaf)}
.badge.doing{background:var(--carrot-soft);color:var(--carrot)}
.badge.todo{background:#E4EDF4;color:var(--muted)}

.actions{display:flex;gap:8px;margin-top:auto}
.btn{
  flex:1;text-align:center;text-decoration:none;font-family:var(--f-round);font-size:14px;
  border:2.5px solid var(--ink);border-radius:12px;padding:7px 10px;
  color:var(--ink);background:var(--card);transition:.15s;
  box-shadow:0 3px 0 rgba(42,63,85,.16);
}
.btn:hover{transform:translateY(-2px)}
.btn:active{transform:translateY(1px);box-shadow:0 1px 0 rgba(42,63,85,.16)}
.btn.primary{background:var(--gold)}
.pending .note{font-size:12px;color:var(--muted);font-style:italic}

.empty{color:var(--muted);font-size:14px;padding:20px 0}
.empty[hidden]{display:none}

footer{
  margin-top:20px;padding-top:20px;border-top:2px dashed var(--line);
  font-size:13px;color:var(--muted);
}
footer b{color:var(--ink)}
footer a,.tagline a,.eyebrow a{color:var(--carrot);font-weight:600;text-decoration:none}
footer a:hover,.tagline a:hover,.eyebrow a:hover{text-decoration:underline}

@media (max-width:520px){
  h1{font-size:30px}
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

    status = u.get("status", "todo")
    return (
        f'<article class="card{"" if ready else " pending"}'
        f'{" is-done" if status == "done" else ""}"'
        f' data-status="{status}" data-ready="{"1" if ready else "0"}">'
        f'<div class="top"><span class="no">{n}</span>'
        f'<span class="stamp">{u.get("ico", "📘")}</span>'
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
        f'<section class="group"><h2>'
        f'<span class="ico">{g.get("ico", "📍")}</span>{html.escape(g["theme"])}'
        f'<span class="rng">{g["units"][0]["n"]}~{g["units"][-1]["n"]}권</span></h2>'
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
<title>부모용 목록 — {html.escape(data["subtitle"])}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <header>
    <p class="eyebrow"><a href="index.html">← 영어 모험 지도</a></p>
    <h1>{html.escape(data["subtitle"])}</h1>
    <p class="tagline">부모용 목록입니다 — 학습 날짜와 걸린 시간, 상태별 필터.
      아이 화면은 <a href="index.html">영어 모험 지도</a> 쪽입니다.</p>
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
    path = os.path.join(ROOT, "list.html")
    open(path, "w", encoding="utf-8").write(out)
    print(f"생성: list.html  (유닛 {len(units)}개, 자료 준비됨 {ready}개)")


if __name__ == "__main__":
    main()
