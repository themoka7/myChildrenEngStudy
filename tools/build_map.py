#!/usr/bin/env python3
"""units.json 을 읽어 메인 페이지(index.html) — 「영어 모험 지도」를 만든다.

아이가 보는 화면이다. 52권이 테마별 구역으로 길에 늘어서 있고, 한 권을
끝내면 그 칸에 도장을 찍는다. 칸을 누르면 읽기 페이지·A4 문제지로 갈 수
있고, 부모용 표(날짜·소요시간·필터)는 list.html 쪽에 있다.

도장은 두 군데에서 온다.
  units.json 의 status:"done"  → 지도에 심어 두는 씨앗(SEED). 저장소의 기록.
  브라우저 localStorage         → 아이가 직접 찍은 도장. 그 기기에만 남는다.
씨앗이 늘어나면(내가 units.json 을 고치면) 새로 늘어난 것만 더한다 —
아이가 일부러 빼 놓은 도장을 되살리지 않기 위해서다.

사용법:
    python3 tools/build_map.py
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSS = """
:root{
  --paper:#e8f0f7; --grid:#d3e2ef; --ink:#2a3f55; --sub:#6b8299;
  --stamp:#e0384f; --gold:#f2b632; --card:#ffffff; --line:#b9cddd;
  --shadow:0 3px 0 rgba(42,63,85,.13);
  --f-display:'Jua','Malgun Gothic','Apple SD Gothic Neo',sans-serif;
  --f-hand:'Gaegu','Malgun Gothic',cursive;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  font-family:var(--f-display);color:var(--ink);
  background:
    linear-gradient(var(--grid) 1px,transparent 1px) 0 0/26px 26px,
    linear-gradient(90deg,var(--grid) 1px,transparent 1px) 0 0/26px 26px,
    var(--paper);
  -webkit-text-size-adjust:100%;
}

/* ---------- 머리 ---------- */
.top{max-width:920px;margin:0 auto;padding:26px 18px 6px;text-align:center}
.top h1{
  margin:0;font-size:clamp(26px,6vw,40px);letter-spacing:-.5px;
  text-shadow:2px 2px 0 #fff, 4px 4px 0 var(--line);
}
.top h1 .em{color:var(--stamp)}
.top p{margin:8px 0 0;font-family:var(--f-hand);font-size:19px;color:var(--sub)}

/* 진행 게이지 */
.gauge{max-width:560px;margin:18px auto 0}
.gauge .nums{display:flex;align-items:baseline;justify-content:center;gap:6px;margin-bottom:7px}
.gauge .big{font-size:34px;color:var(--stamp);line-height:1}
.gauge .of{font-size:17px;color:var(--sub)}
.bar{
  height:20px;border-radius:99px;background:#fff;
  border:2.5px solid var(--ink);overflow:hidden;box-shadow:var(--shadow);
}
.bar i{
  display:block;height:100%;width:0;border-radius:99px;
  background:repeating-linear-gradient(45deg,var(--gold) 0 12px,#ffd166 12px 24px);
  transition:width .5s cubic-bezier(.34,1.4,.5,1);
}
.gauge .note{margin:9px 0 0;font-family:var(--f-hand);font-size:17px;color:var(--sub)}

/* ---------- 길 ---------- */
.trail{max-width:920px;margin:0 auto;padding:22px 18px 70px;position:relative}
.trail::before{
  content:"";position:absolute;left:50%;top:0;bottom:64px;width:0;
  border-left:5px dashed var(--line);transform:translateX(-50%);z-index:0;
}
.zone{position:relative;z-index:1;margin-bottom:26px;display:flex;gap:14px;align-items:flex-start}
.zone:nth-child(even){flex-direction:row-reverse}

/* 표지판 */
.sign{
  flex:0 0 96px;text-align:center;background:var(--card);
  border:3px solid var(--ink);border-radius:16px;padding:10px 6px;
  box-shadow:var(--shadow);position:relative;
}
.sign .ico{font-size:30px;line-height:1.1}
.sign .nm{font-size:14px;margin-top:3px}
.sign .rng{font-family:var(--f-hand);font-size:14px;color:var(--sub)}
.sign .ribbon{
  display:none;position:absolute;left:50%;top:-14px;transform:translateX(-50%) rotate(-4deg);
  background:var(--gold);border:2.5px solid var(--ink);border-radius:99px;
  font-size:12px;padding:1px 9px;white-space:nowrap;
}
.zone.clear .sign{background:#fffaeb}
.zone.clear .sign .ribbon{display:block}

/* 칸 */
.tiles{flex:1;display:flex;flex-wrap:wrap;gap:10px;align-content:flex-start}
.zone:nth-child(even) .tiles{justify-content:flex-end}

.tile{
  position:relative;width:78px;height:78px;padding:0;cursor:pointer;
  font-family:inherit;color:var(--ink);
  background:var(--card);border:3px solid var(--ink);border-radius:18px;
  box-shadow:var(--shadow);transition:transform .13s,box-shadow .13s;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;
}
.tile:hover{transform:translateY(-3px);box-shadow:0 6px 0 rgba(42,63,85,.15)}
.tile:active{transform:translateY(1px);box-shadow:0 1px 0 rgba(42,63,85,.13)}
.tile:focus-visible{outline:4px solid var(--stamp);outline-offset:3px}
.tile .no{
  position:absolute;top:-9px;left:-9px;min-width:22px;height:22px;
  background:var(--ink);color:#fff;border-radius:99px;font-size:12px;
  display:flex;align-items:center;justify-content:center;padding:0 5px;
}
.tile .ico{font-size:25px;line-height:1}
.tile .en{font-size:11.5px;max-width:70px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tile .ko{font-family:var(--f-hand);font-size:12px;color:var(--sub);line-height:1}

/* 자료가 아직 없는 칸 */
.tile.pending{border-style:dashed;border-color:var(--line);background:transparent;
  box-shadow:none;cursor:default}
.tile.pending .ico,.tile.pending .en,.tile.pending .ko{opacity:.4}
.tile.pending:hover{transform:none;box-shadow:none}

/* 찍힌 도장 */
.tile .stamp{
  position:absolute;inset:0;display:none;align-items:center;justify-content:center;
  color:var(--stamp);font-size:13px;letter-spacing:1px;
  border:3.5px solid var(--stamp);border-radius:50%;
  margin:9px;opacity:.85;transform:rotate(-14deg);
  background:rgba(224,56,79,.07);
}
.tile.done{background:#fff4f5;border-color:var(--stamp)}
.tile.done .stamp{display:flex}
.tile.done .ico,.tile.done .en,.tile.done .ko{opacity:.32}
.tile.pressing .stamp{animation:press .45s cubic-bezier(.3,1.6,.5,1)}
@keyframes press{
  0%{transform:rotate(-32deg) scale(2.4);opacity:0}
  55%{transform:rotate(-10deg) scale(.88);opacity:1}
  100%{transform:rotate(-14deg) scale(1);opacity:.85}
}

/* 지금 여기 */
.tile.here{border-color:var(--gold);background:#fffaeb}
.tile .me{
  position:absolute;top:-26px;right:-12px;font-size:27px;
  animation:hop 1.5s ease-in-out infinite;
}
@keyframes hop{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}

/* 끝 깃발 */
.goal{
  position:relative;z-index:1;text-align:center;background:var(--card);
  border:3px solid var(--ink);border-radius:20px;padding:16px;
  box-shadow:var(--shadow);max-width:330px;margin:6px auto 0;
}
.goal .f{font-size:36px}
.goal .t{font-size:19px;margin-top:2px}
.goal .s{font-family:var(--f-hand);font-size:16px;color:var(--sub)}

/* ---------- 카드 ---------- */
.back{
  position:fixed;inset:0;background:rgba(42,63,85,.5);
  display:none;align-items:center;justify-content:center;padding:18px;z-index:50;
}
.back.on{display:flex}
.pop{
  background:var(--card);border:4px solid var(--ink);border-radius:24px;
  box-shadow:0 8px 0 rgba(42,63,85,.25);padding:22px;width:100%;max-width:330px;text-align:center;
  animation:pin .22s cubic-bezier(.34,1.5,.5,1);
}
@keyframes pin{from{transform:scale(.85);opacity:0}to{transform:scale(1);opacity:1}}
.pop .ico{font-size:46px;line-height:1}
.pop .no{font-family:var(--f-hand);font-size:16px;color:var(--sub);margin-top:2px}
.pop .en{font-size:25px;margin-top:1px}
.pop .ko{font-family:var(--f-hand);font-size:18px;color:var(--sub)}
.pop .btns{display:flex;flex-direction:column;gap:9px;margin-top:16px}
.btn{
  font-family:inherit;font-size:16px;padding:11px;cursor:pointer;color:var(--ink);
  background:#fff;border:3px solid var(--ink);border-radius:14px;
  box-shadow:0 3px 0 rgba(42,63,85,.18);text-decoration:none;display:block;
}
.btn:hover{transform:translateY(-2px)}
.btn:active{transform:translateY(1px);box-shadow:0 1px 0 rgba(42,63,85,.18)}
.btn:focus-visible{outline:4px solid var(--stamp);outline-offset:3px}
.btn.go{background:var(--gold)}
.btn.undo{background:#fff;color:var(--sub);font-size:14px;border-style:dashed}
.pop .close{margin-top:11px;background:none;border:0;font-family:var(--f-hand);
  font-size:16px;color:var(--sub);cursor:pointer;text-decoration:underline}

/* 축하 조각 */
.conf{position:fixed;inset:0;pointer-events:none;z-index:60;overflow:hidden}
.conf span{position:absolute;width:9px;height:14px;border-radius:2px;animation:fall 1.5s linear forwards}
@keyframes fall{to{transform:translateY(105vh) rotate(680deg);opacity:0}}

.foot{max-width:920px;margin:0 auto;padding:0 18px 40px;text-align:center;
  font-family:var(--f-hand);font-size:16px;color:var(--sub);line-height:1.9}
.foot a{color:var(--sub)}
.foot button{font-family:var(--f-hand);font-size:15px;color:var(--sub);
  background:none;border:0;text-decoration:underline;cursor:pointer;padding:0}
.foot .warn{color:var(--stamp)}
.foot .warn[hidden]{display:none}

@media (max-width:660px){
  .trail::before{left:26px;transform:none}
  .zone,.zone:nth-child(even){flex-direction:column;align-items:stretch;padding-left:52px}
  .sign{flex:none;display:flex;align-items:center;gap:9px;text-align:left;padding:8px 12px}
  .sign .ico{font-size:24px}
  .sign .ribbon{left:auto;right:10px;transform:rotate(-4deg)}
  .zone:nth-child(even) .tiles{justify-content:flex-start}
  .tile{width:72px;height:72px}
}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
}
"""

JS = r"""
const TOTAL = ZONES.reduce((n,z)=>n+z.u.length, 0);
const KEY = 'engmap.done.v2';
let done = new Set(SEED), memOnly = false;

/* units.json 의 완료 기록(SEED)과 이 기기의 도장을 합친다.
   저장할 때 그때의 SEED 를 함께 남겨 두고, 다음에 열 때 그 사이 새로
   완료로 바뀐 것만 더한다 — 아이가 일부러 뺀 도장은 되살리지 않는다. */
function load(){
  try{
    const raw = localStorage.getItem(KEY);
    if(!raw){ save(); return; }
    const o = JSON.parse(raw);
    done = new Set(o.done || []);
    const seen = new Set(o.seed || []);
    SEED.forEach(n=>{ if(!seen.has(n)) done.add(n); });
    save();
  }catch(e){ memOnly = true; }
}
function save(){
  try{ localStorage.setItem(KEY, JSON.stringify({done:[...done], seed:SEED})); }
  catch(e){ memOnly = true; }
}

const pad = n => String(n).padStart(2,'0');
const all = ZONES.flatMap(z=>z.u);
const byNo = Object.fromEntries(all.map(u=>[u.n,u]));

function build(){
  const t = document.getElementById('trail');
  t.innerHTML = '';
  ZONES.forEach(z=>{
    const el = document.createElement('section');
    el.className = 'zone';
    el.dataset.zone = z.nm;
    el.innerHTML =
      '<div class="sign"><span class="ribbon">클리어!</span>' +
        '<div class="ico">' + z.ico + '</div>' +
        '<div><div class="nm">' + z.nm + '</div>' +
        '<div class="rng">' + z.u[0].n + '~' + z.u[z.u.length-1].n + '권</div></div>' +
      '</div><div class="tiles"></div>';
    const box = el.querySelector('.tiles');
    z.u.forEach(u=>{
      const b = document.createElement('button');
      b.className = 'tile' + (u.ready ? '' : ' pending');
      b.dataset.no = u.n;
      b.setAttribute('aria-label', u.n + '권 ' + u.en + ' ' + u.ko +
        (u.ready ? '' : ' (자료 준비 중)'));
      b.innerHTML = '<span class="no">' + u.n + '</span>' +
        '<span class="ico">' + u.ico + '</span>' +
        '<span class="en">' + u.en + '</span>' +
        '<span class="ko">' + u.ko + '</span>' +
        '<span class="stamp">완료</span>';
      if(u.ready) b.addEventListener('click', ()=>open(u.n));
      else b.disabled = true;
      box.appendChild(b);
    });
    t.appendChild(el);
  });
  const g = document.createElement('div');
  g.className = 'goal';
  g.innerHTML = '<div class="f">🏁</div><div class="t">' + TOTAL + '권 완주!</div>' +
                '<div class="s">여기까지 오면 진짜 대단한 거야</div>';
  t.appendChild(g);
}

function paint(){
  const n = done.size;
  document.getElementById('cnt').textContent = n;
  document.getElementById('bar').style.width = (n/TOTAL*100) + '%';

  let here = 0;
  for(const u of all){ if(!done.has(u.n)){ here = u.n; break; } }

  document.querySelectorAll('.tile').forEach(b=>{
    const no = +b.dataset.no, is = done.has(no);
    b.classList.toggle('done', is);
    b.classList.toggle('here', no === here);
    b.setAttribute('aria-pressed', is);
    const old = b.querySelector('.me'); if(old) old.remove();
    if(no === here){
      const m = document.createElement('span');
      m.className = 'me'; m.textContent = '🐰'; m.setAttribute('aria-hidden','true');
      b.appendChild(m);
    }
  });

  ZONES.forEach(z=>{
    document.querySelector('.zone[data-zone="' + z.nm + '"]')
      .classList.toggle('clear', z.u.every(u=>done.has(u.n)));
  });

  const note = document.getElementById('note');
  if(n === 0) note.textContent = '첫 도장을 찍어 보자!';
  else if(n === TOTAL) note.textContent = TOTAL + '권 전부 끝! 진짜 다 했다 🎉';
  else note.textContent = here + '권 ' + byNo[here].en + ' 차례 · ' + (TOTAL-n) + '개 남았어';

  document.getElementById('memwarn').hidden = !memOnly;
}

let cur = null;
function open(no){
  cur = no;
  const u = byNo[no];
  document.getElementById('popIco').textContent = u.ico;
  document.getElementById('popNo').textContent = no + '권';
  document.getElementById('popEn').textContent = u.en;
  document.getElementById('popKo').textContent = u.ko;
  document.getElementById('popRead').href = 'read/unit' + pad(no) + '.html';
  document.getElementById('popPrint').href = 'print/unit' + pad(no) + '.html';
  const s = document.getElementById('popStamp'), is = done.has(no);
  s.textContent = is ? '도장 빼기' : '도장 쾅! 찍기';
  s.className = is ? 'btn undo' : 'btn go';
  document.getElementById('back').classList.add('on');
  s.focus();
}
function close(){ document.getElementById('back').classList.remove('on'); cur = null; }

function toggle(){
  if(cur == null) return;
  const no = cur, was = done.has(no);
  const zone = ZONES.find(z=>z.u.some(u=>u.n === no));
  const wasClear = zone.u.every(u=>done.has(u.n));

  was ? done.delete(no) : done.add(no);
  save(); close(); paint();

  if(!was){
    const b = document.querySelector('.tile[data-no="' + no + '"]');
    if(b){ b.classList.add('pressing'); setTimeout(()=>b.classList.remove('pressing'), 500); }
    if(!wasClear && zone.u.every(u=>done.has(u.n))) party();
  }
}

function party(){
  if(matchMedia('(prefers-reduced-motion:reduce)').matches) return;
  const c = document.createElement('div'); c.className = 'conf';
  const cols = ['#e0384f','#f2b632','#4ea6d6','#6cc48f','#b47ee0'];
  for(let i=0;i<44;i++){
    const s = document.createElement('span');
    s.style.left = Math.random()*100 + 'vw';
    s.style.top = (-12 - Math.random()*22) + 'vh';
    s.style.background = cols[i%cols.length];
    s.style.animationDelay = (Math.random()*.5) + 's';
    s.style.animationDuration = (1.2 + Math.random()*.8) + 's';
    c.appendChild(s);
  }
  document.body.appendChild(c);
  setTimeout(()=>c.remove(), 2600);
}

/* 도장은 이 기기에만 남는다. 저장소(units.json)에 옮겨 적으려면
   이 줄을 복사해서 넘기면 된다 — 집·회사 어디서 열어도 같아진다. */
function copyProgress(){
  const txt = '완료 ' + done.size + '/' + TOTAL + ' — ' +
              [...done].sort((a,b)=>a-b).join(', ');
  const out = document.getElementById('progress');
  out.textContent = txt;
  out.hidden = false;
  try{ navigator.clipboard.writeText(txt); }catch(e){}
}

document.getElementById('popStamp').addEventListener('click', toggle);
document.getElementById('popClose').addEventListener('click', close);
document.getElementById('back').addEventListener('click', e=>{
  if(e.target.id === 'back') close();
});
document.addEventListener('keydown', e=>{ if(e.key === 'Escape') close(); });
document.getElementById('copy').addEventListener('click', copyProgress);
document.getElementById('reset').addEventListener('click', ()=>{
  if(!confirm('도장을 전부 지울까요?')) return;
  done = new Set(); save(); paint();
});

load(); build(); paint();
"""


def main():
    data = json.load(open(os.path.join(ROOT, "units.json"), encoding="utf-8"))
    units = [u for g in data["groups"] for u in g["units"]]
    seed = [u["n"] for u in units if u.get("status") == "done"]

    def unit(u):
        return {"n": u["n"], "en": u["en"], "ko": u["ko"],
                "ico": u.get("ico", "📘"), "ready": bool(u.get("ready"))}

    zones = [{"nm": g["theme"], "ico": g.get("ico", "📍"),
              "u": [unit(u) for u in g["units"]]} for g in data["groups"]]

    data_js = (f"const ZONES={json.dumps(zones, ensure_ascii=False)};\n"
               f"const SEED={json.dumps(seed)};")

    out = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>영어 모험 지도 — 도장 {len(units)}개 모으기</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Jua&family=Gaegu:wght@400;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<div class="top">
  <h1>영어 모험 <span class="em">지도</span></h1>
  <p>한 권 다 읽으면 도장을 쾅! {len(units)}개를 모아 보자</p>

  <div class="gauge">
    <div class="nums"><span class="big" id="cnt">0</span><span class="of">/ {len(units)} 도장</span></div>
    <div class="bar"><i id="bar"></i></div>
    <p class="note" id="note"></p>
  </div>
</div>

<div class="trail" id="trail"></div>

<div class="foot">
  도장은 이 기기에 저장돼요.
  <span class="warn" id="memwarn" hidden>— 이 브라우저에서는 저장이 안 돼서 새로 고치면 사라져요.</span>
  <br>
  <button id="copy">진도 복사하기</button> ·
  <button id="reset">전부 지우고 처음부터</button> ·
  <a href="list.html">부모용 목록 (날짜 · 소요시간)</a>
  <div id="progress" hidden></div>
</div>

<div class="back" id="back">
  <div class="pop" role="dialog" aria-modal="true" aria-labelledby="popEn">
    <div class="ico" id="popIco"></div>
    <div class="no" id="popNo"></div>
    <div class="en" id="popEn"></div>
    <div class="ko" id="popKo"></div>
    <div class="btns">
      <a class="btn" id="popRead" href="#">📖 읽으러 가기</a>
      <a class="btn" id="popPrint" href="#">🖨 문제지 뽑기</a>
      <button class="btn go" id="popStamp">도장 쾅! 찍기</button>
    </div>
    <button class="close" id="popClose">닫기</button>
  </div>
</div>

<script>
{data_js}
{JS}
</script>
</body>
</html>
"""
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
    print(f"생성: index.html  (지도 — 칸 {len(units)}개, 미리 찍힌 도장 {len(seed)}개)")


if __name__ == "__main__":
    main()
