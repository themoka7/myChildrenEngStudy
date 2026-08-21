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

/* ---------- 안내 패널 ---------- */
.guide-open{
  position:fixed;top:14px;right:14px;z-index:40;font-family:inherit;font-size:15px;
  cursor:pointer;color:var(--ink);background:var(--card);
  border:2.5px solid var(--ink);border-radius:14px;padding:8px 14px;
  box-shadow:0 3px 0 rgba(42,63,85,.18);
}
.guide-open:hover{transform:translateY(-2px)}
.guide-open:active{transform:translateY(1px);box-shadow:0 1px 0 rgba(42,63,85,.18)}
.guide-open:focus-visible{outline:4px solid var(--stamp);outline-offset:3px}
.guide-back{
  position:fixed;inset:0;background:rgba(42,63,85,.45);z-index:70;
  opacity:0;pointer-events:none;transition:opacity .25s;
}
.guide-back.on{opacity:1;pointer-events:auto}
.guide{
  position:fixed;top:0;right:0;bottom:0;width:min(560px,100%);z-index:80;
  background:#eef2f7;overflow-y:auto;overscroll-behavior:contain;
  border-left:3px solid var(--ink);box-shadow:-6px 0 0 rgba(42,63,85,.10);
  transform:translateX(101%);transition:transform .3s cubic-bezier(.3,.9,.3,1);
}
.guide.on{transform:none}
.guide-close{
  position:sticky;top:0;z-index:5;width:100%;font-family:inherit;font-size:15px;
  cursor:pointer;color:var(--ink);background:rgba(238,242,247,.94);
  backdrop-filter:blur(8px);border:0;border-bottom:2px solid #d7e0ea;
  padding:12px;text-align:right;
}
.guide-close:focus-visible{outline:4px solid var(--stamp);outline-offset:-4px}

/* 좁은 화면에서는 가운데 정렬한 제목이 오른쪽 위 버튼과 겹친다 —
   제목을 버튼 아래로 내린다 */
@media (max-width:600px){
  .top{padding-top:58px}
}
@media (max-width:660px){
  .guide-open{top:10px;right:10px;font-size:14px;padding:7px 11px}
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

# 안내 패널 CSS. 모든 규칙에 #intro 를 붙여 둔다 — 원본은 section·h2·.btn
# 같은 일반 선택자를 쓰는데, 지도의 구역도 <section class="zone"> 이라서
# 범위를 안 묶으면 지도 배치가 깨진다. 색 변수도 #intro 안에서만 산다.
INTRO_CSS = """
#intro{
  --paper:#fff; --ink:#12243a; --sub:#5b7288; --line:#d7e0ea;
  --hl:#ffe24a; --stamp:#e0384f;
  --f-dis:'Black Han Sans','Malgun Gothic',sans-serif;
  --f-body:'IBM Plex Sans KR','Malgun Gothic','Apple SD Gothic Neo',sans-serif;
  --f-hand:'Gaegu','Malgun Gothic',cursive;
  font-family:var(--f-body);font-size:15.5px;line-height:1.7;color:var(--ink);
  text-align:left;
}
#intro .wrap{padding:0 22px}
#intro section{padding:38px 0}
#intro h2{font-family:var(--f-dis);font-size:25px;margin:0 0 8px;
  letter-spacing:-.5px;font-weight:400;line-height:1.3}
#intro .lead{color:var(--sub);margin:0 0 22px;font-size:15.5px}
#intro .eyebrow{font-family:var(--f-hand);font-size:17px;color:var(--stamp);
  margin:0 0 2px;letter-spacing:.5px}

/* 형광펜 — 이 안내의 시그니처. isolation 으로 mark 자체를 쌓임 문맥으로
   만들어 두면, 패널에 배경이 깔려도 밑줄이 뒤로 숨지 않는다. */
#intro mark{background:none;color:inherit;position:relative;isolation:isolate;
  padding:0 .12em;white-space:nowrap}
#intro mark::before{
  content:"";position:absolute;left:0;right:0;bottom:.06em;height:.55em;
  background:var(--hl);z-index:-1;border-radius:2px 6px 3px 5px;
  transform:scaleX(0);transform-origin:left center;
  transition:transform .5s cubic-bezier(.4,.1,.2,1);
}
#intro .lit mark::before{transform:scaleX(1)}
#intro .lit mark:nth-of-type(2)::before{transition-delay:.16s}
#intro .lit mark:nth-of-type(3)::before{transition-delay:.32s}

#intro .hero{background:var(--paper);border-bottom:1px solid var(--line);
  padding:26px 0 34px;position:relative;overflow:hidden}
#intro .hero::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:repeating-linear-gradient(180deg,rgba(18,36,58,.022) 0 1px,transparent 1px 27px)}
#intro .hero .wrap{position:relative;z-index:1}
#intro .tag{display:inline-block;font-family:var(--f-hand);font-size:16px;
  color:var(--stamp);border:2px solid var(--stamp);border-radius:99px;
  padding:1px 13px;transform:rotate(-1.5deg)}
#intro .hero h1{font-family:var(--f-dis);font-weight:400;letter-spacing:-1px;
  font-size:clamp(30px,7vw,42px);line-height:1.24;margin:14px 0 0}
#intro .hero .sub{margin:16px 0 0;font-size:16px;color:var(--sub)}
#intro .cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
#intro .btn{font-family:inherit;font-size:15px;font-weight:600;text-decoration:none;
  padding:11px 20px;border-radius:11px;border:2px solid var(--ink);cursor:pointer;
  color:var(--ink);background:var(--paper);display:inline-block;
  transition:transform .14s,box-shadow .14s;box-shadow:0 3px 0 var(--ink)}
#intro .btn:hover{transform:translateY(-2px);box-shadow:0 5px 0 var(--ink)}
#intro .btn:active{transform:translateY(2px);box-shadow:0 1px 0 var(--ink)}
#intro .btn:focus-visible{outline:3px solid var(--stamp);outline-offset:3px}
#intro .btn.solid{background:var(--hl)}

#intro .stats{display:flex;flex-wrap:wrap;margin-top:28px;border-top:1px solid var(--line)}
#intro .stat{flex:1 1 120px;padding:14px 4px 0;border-right:1px solid var(--line)}
#intro .stat:last-child{border-right:0}
#intro .stat b{display:block;font-family:var(--f-dis);font-weight:400;font-size:25px;line-height:1.1}
#intro .stat span{font-size:12.5px;color:var(--sub)}

#intro .routine{background:#eef2f7}
#intro .tl{position:relative}
#intro .tl::before{content:"";position:absolute;left:8px;top:14px;bottom:14px;
  width:2px;background:var(--line)}
#intro .step{display:flex;flex-direction:column;gap:2px;padding:8px 0 8px 30px;position:relative}
#intro .step .clock{font-family:var(--f-hand);font-size:18px;color:var(--stamp)}
#intro .step .dot{position:absolute;left:2px;top:14px;width:13px;height:13px;
  background:var(--paper);border:3px solid var(--ink);border-radius:50%}
#intro .step .body{background:var(--paper);border:1px solid var(--line);
  border-radius:12px;padding:11px 15px}
#intro .step .body b{display:block;font-size:15.5px}
#intro .step .body span{font-size:14px;color:var(--sub)}

#intro .two{display:grid;gap:16px}
#intro .card{background:var(--paper);border:1px solid var(--line);
  border-radius:16px;padding:22px}
#intro .card .ic{font-size:30px;line-height:1}
#intro .card h3{font-family:var(--f-dis);font-weight:400;font-size:20px;margin:8px 0 4px}
#intro .card p{margin:0 0 12px;color:var(--sub);font-size:14.5px}
#intro .card ul{margin:0;padding-left:18px;font-size:14.5px}
#intro .card li{margin-bottom:6px}
#intro .card li::marker{color:var(--stamp)}
#intro .card .go{display:inline-block;margin-top:12px;font-weight:600;font-size:14.5px;
  color:var(--ink);text-decoration:none;border-bottom:2.5px solid var(--hl)}
#intro .card .go:hover{border-bottom-color:var(--stamp)}

#intro .q6{display:grid;grid-template-columns:1fr 1fr;gap:12px}
#intro .q{background:var(--paper);border:1px solid var(--line);border-radius:13px;padding:14px 15px}
#intro .q b{display:inline-flex;align-items:center;justify-content:center;
  width:25px;height:25px;border-radius:7px;background:var(--ink);color:#fff;
  font-size:13.5px;margin-bottom:8px}
#intro .q .t{display:block;font-weight:600;font-size:14.5px}
#intro .q .d{display:block;font-size:13.5px;color:var(--sub);margin-top:2px}

#intro .answer{background:var(--paper);border-top:1px solid var(--line);
  border-bottom:1px solid var(--line)}
#intro .memo{background:#fffdf3;border:1px solid #eadfae;border-radius:14px;
  padding:20px 22px;font-family:var(--f-hand);font-size:18px;line-height:1.75;
  transform:rotate(-.6deg);box-shadow:0 2px 0 #eadfae;margin-top:22px}
#intro .memo .h{font-family:var(--f-body);font-weight:700;font-size:12.5px;
  color:var(--stamp);letter-spacing:1px;margin-bottom:9px}
#intro .memo p{margin:0 0 12px}
#intro .memo p:last-child{margin:0}
#intro .memo q{color:var(--ink);font-weight:700}

#intro .chips{display:flex;flex-wrap:wrap;gap:8px}
#intro .chip{background:var(--paper);border:1px solid var(--line);border-radius:99px;
  padding:6px 14px;font-size:14.5px}
#intro .chip i{font-style:normal;margin-right:5px}
#intro .chip u{text-decoration:none;color:var(--sub);font-size:12.5px;margin-left:5px}

#intro .map{background:var(--ink);color:#fff}
#intro .map h2{color:#fff}
#intro .map .lead{color:#a9bed2}
/* 어두운 칸의 형광펜. 흰 글씨를 그대로 두면 노랑 위 흰 글씨가 되어 안
   읽히고, 글씨만 진하게 바꾸면 띠가 글자 아래쪽 55% 만 덮기 때문에 위쪽
   절반이 남색 배경에 묻혀 글자가 반만 보인다. 어두운 데서는 띠를 글자
   높이만큼 채워 도장처럼 만든다. */
#intro .map h2 mark{color:var(--ink)}
#intro .map h2 mark::before{height:1.12em;bottom:-.07em;border-radius:4px 8px 5px 7px}
#intro .map .box{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);
  border-radius:18px;padding:22px}
#intro .map .stamps{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
#intro .map .s{width:34px;height:34px;border-radius:10px;
  border:2px solid rgba(255,255,255,.3);display:flex;align-items:center;
  justify-content:center;font-size:15px}
#intro .map .s.on{border-color:var(--stamp);background:rgba(224,56,79,.22)}
#intro .map .txt p{margin:0 0 16px;color:#c6d6e4;font-size:15px}
#intro .map .btn{background:var(--hl);border-color:var(--hl);
  box-shadow:0 3px 0 #c9ae2f;color:var(--ink)}
#intro .map .btn:hover{box-shadow:0 5px 0 #c9ae2f}

#intro footer{padding:30px 0 46px;text-align:center;color:var(--sub);font-size:14px}
#intro footer .made{font-family:var(--f-hand);font-size:17px;color:var(--ink);margin-bottom:6px}

@media (min-width:520px){
  #intro .two{grid-template-columns:1fr 1fr}
}
@media (prefers-reduced-motion:reduce){
  #intro mark::before{transform:scaleX(1)!important}
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

/* ---------- 안내 패널 ---------- */
const guide = document.getElementById('guide');
const guideBack = document.getElementById('guideBack');
const guideOpen = document.getElementById('guideOpen');
let guideFonts = false;

function showGuide(){
  /* 안내 전용 글꼴은 처음 열 때만 받아 온다 — 닫혀 있는 동안 세 벌을
     미리 받을 이유가 없다. Gaegu 는 지도에서 이미 쓰고 있다. */
  if(!guideFonts){
    const l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=IBM+Plex+Sans+KR:wght@400;600;700&display=swap';
    document.head.appendChild(l);
    guideFonts = true;
    litGuide();
  }
  paintGuideStamps();
  guide.classList.add('on');
  guideBack.classList.add('on');
  guide.setAttribute('aria-hidden','false');
  document.body.style.overflow = 'hidden';
  document.getElementById('guideClose').focus();
}
function hideGuide(){
  guide.classList.remove('on');
  guideBack.classList.remove('on');
  guide.setAttribute('aria-hidden','true');
  document.body.style.overflow = '';
  guideOpen.focus();
}

/* 형광펜 밑줄. 원본은 화면 전체를 기준으로 보는데, 안내는 패널 안에서
   따로 스크롤되므로 그 패널을 기준(root)으로 줘야 제때 그어진다. */
function litGuide(){
  const t = guide.querySelectorAll('.reveal');
  if(!('IntersectionObserver' in window)){
    t.forEach(e=>e.classList.add('lit')); return;
  }
  const io = new IntersectionObserver(es=>{
    es.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('lit'); io.unobserve(e.target); } });
  }, {root: guide, threshold:.5});
  t.forEach(e=>io.observe(e));
}

/* 안내 속 도장 그림은 지금 진도를 그대로 보여 준다 — 가짜 상태를 보여
   주면 바로 아래 지도와 어긋난다. */
function paintGuideStamps(){
  const box = document.getElementById('guideStamps');
  box.innerHTML = all.slice(0,16).map(u=>
    '<span class="s' + (done.has(u.n) ? ' on' : '') + '">' + u.ico + '</span>').join('');
}

guideOpen.addEventListener('click', showGuide);
document.getElementById('guideClose').addEventListener('click', hideGuide);
guideBack.addEventListener('click', hideGuide);
guide.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click', hideGuide));

document.getElementById('popStamp').addEventListener('click', toggle);
document.getElementById('popClose').addEventListener('click', close);
document.getElementById('back').addEventListener('click', e=>{
  if(e.target.id === 'back') close();
});
document.addEventListener('keydown', e=>{
  if(e.key !== 'Escape') return;
  /* 카드가 열려 있으면 카드부터, 아니면 안내를 닫는다 */
  if(cur != null) close();
  else if(guide.classList.contains('on')) hideGuide();
});
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

    chips = "".join(
        f'<span class="chip"><i>{g.get("ico", "📍")}</i>{html.escape(g["theme"])}'
        f'<u>{g["units"][0]["n"]}–{g["units"][-1]["n"]}</u></span>'
        for g in data["groups"])

    intro = f"""
<div id="intro">

<header class="hero">
  <div class="wrap">
    <span class="tag">{html.escape(data["course"])} · 집에서</span>
    <h1 class="reveal">하루 <mark>20분</mark>,<br>영어책 <mark>{len(units)}권</mark></h1>
    <p class="sub">
      화면으로 읽고, 종이로 풉니다.
      단어에 손을 대면 뜻이 뜨고, 다 읽으면 A4로 뽑아 연필로 풀어요.
      부모가 영어를 못해도 옆에서 봐줄 수 있게 <b>정답지에 할 말까지</b> 적어 뒀습니다.
    </p>
    <div class="cta">
      <button class="btn solid" data-close>🗺 지도로 돌아가기</button>
      <a class="btn" href="list.html">📚 {len(units)}권 목록 보기</a>
    </div>

    <div class="stats">
      <div class="stat"><b>{len(units)}권</b><span>EBS 펀리딩 전편</span></div>
      <div class="stat"><b>{len(data["groups"])}개</b><span>주제 · 동물부터 우주까지</span></div>
      <div class="stat"><b>20분</b><span>하루 한 권 분량</span></div>
      <div class="stat"><b>A4 3장</b><span>문제 2 + 정답 1</span></div>
    </div>
  </div>
</header>

<section class="routine">
  <div class="wrap">
    <p class="eyebrow">하루 한 권</p>
    <h2 class="reveal">20분이 <mark>이렇게</mark> 흘러갑니다</h2>
    <p class="lead">순서를 정해 두면 매일 뭘 할지 고민하지 않아도 됩니다. 정답지 맨 아래에 이 표가 그대로 들어 있어요.</p>

    <div class="tl">
      <div class="step"><div class="clock">0~3분</div><div class="dot"></div>
        <div class="body"><b>소리 먼저</b><span>그날 나올 단어를 소리로 풀어 봅니다 — /k/-/l/-/o/-/ck/-/s/ → clocks</span></div></div>
      <div class="step"><div class="clock">3~8분</div><div class="dot"></div>
        <div class="body"><b>소리 내어 두 번 읽기</b><span>아이가 읽고 부모는 듣기만 하면 됩니다. 부모가 못 읽어도 괜찮아요</span></div></div>
      <div class="step"><div class="clock">8~17분</div><div class="dot"></div>
        <div class="body"><b>연필로 풀기</b><span>문제지 2장. 막히면 지문을 다시 봐도 됩니다 — 찾아내는 것도 실력이니까요</span></div></div>
      <div class="step"><div class="clock">17~19분</div><div class="dot"></div>
        <div class="body"><b>안 보고 말해 보기</b><span>오늘 따라 쓴 문장 두 개를 지문 없이 입으로</span></div></div>
      <div class="step"><div class="clock">19~20분</div><div class="dot"></div>
        <div class="body"><b>별점 색칠</b><span>“오늘 새로 안 단어 하나만 말해줘” — 이 한마디로 마무리</span></div></div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">쓰는 법</p>
    <h2 class="reveal">화면으로 읽고, <mark>종이로 풉니다</mark></h2>
    <p class="lead">두 가지를 같은 지문으로 만들어 뒀습니다. 읽기는 화면이 편하고, 푸는 건 종이가 낫더라고요.</p>

    <div class="two">
      <div class="card">
        <div class="ic">📖</div>
        <h3>읽기 페이지</h3>
        <p>혼자서도 읽어 나갈 수 있게</p>
        <ul>
          <li>점선 단어에 손을 대면 <b>품사·발음·뜻</b>이 뜹니다</li>
          <li>문장마다 <b>해석 버튼</b> — 먼저 짐작해 보고 눌러요</li>
          <li>🔊 <b>듣기</b>로 발음 확인</li>
          <li>끝나면 <b>단어 퀴즈</b> 4지선다</li>
        </ul>
        <a class="go" href="read/unit01.html">1권 Rabbits 열어 보기 →</a>
      </div>

      <div class="card">
        <div class="ic">🖨</div>
        <h3>A4 문제지</h3>
        <p>연필을 쥐어야 남는 것이 있어서</p>
        <ul>
          <li>지문 + <b>문제 2장</b>, 문장마다 번호가 붙어 있어요</li>
          <li><b>부모용 정답 1장</b>이 따로 나옵니다</li>
          <li>정답지를 빼고 인쇄하는 버튼도 있어요</li>
          <li>배율 100%, 배경 그래픽 켜고 인쇄하면 끝</li>
        </ul>
        <a class="go" href="print/unit01.html">문제지 미리 보기 →</a>
      </div>
    </div>
  </div>
</section>

<section class="routine">
  <div class="wrap">
    <p class="eyebrow">문제지 속</p>
    <h2 class="reveal">여섯 문항이 <mark>매번 같은 순서</mark>로</h2>
    <p class="lead">형식이 고정돼 있으면 아이가 “뭘 하라는 거지”에 힘을 안 씁니다. 그 힘을 내용에 쓰게 하려고요.</p>

    <div class="q6">
      <div class="q"><b>1</b><span class="t">단어와 뜻 잇기</span><span class="d">지문 앞뒤에서 고루 뽑은 단어</span></div>
      <div class="q"><b>2</b><span class="t">빠진 모음 쓰기</span><span class="d">h_p · cl_cks — 소리 내어 읽으며</span></div>
      <div class="q"><b>3</b><span class="t">지문에서 찾아 쓰기</span><span class="d">몇 번 문장에서 찾았는지도 적어요</span></div>
      <div class="q"><b>4</b><span class="t">맞으면 O, 틀리면 X</span><span class="d">지문에 없는 내용이 꼭 하나 섞여 있어요</span></div>
      <div class="q"><b>5</b><span class="t">보기에서 골라 빈칸</span><span class="d">쓰지 않는 보기가 하나 들어 있습니다</span></div>
      <div class="q"><b>6</b><span class="t">따라 쓰고 한 번 더</span><span class="d">회색 글씨 위에 덧쓰고, 아래 줄에 혼자</span></div>
    </div>
  </div>
</section>

<section class="answer">
  <div class="wrap">
    <p class="eyebrow">이게 핵심입니다</p>
    <h2 class="reveal">정답지에 <mark>할 말</mark>이 적혀 있어요</h2>
    <p class="lead" style="margin-bottom:14px">
      정답만 있으면 반쪽입니다. 아이가 틀렸을 때 뭐라고 해야 할지 모르면
      그 자리에서 공부가 멈추더라고요. 그래서 <b>그대로 읽으면 되는 문장</b>으로 적었습니다.
    </p>
    <p class="lead" style="margin:0">
      조동사·과거형·복수형 규칙은 일부러 넣지 않았습니다.
      지금은 <b>소리 · 낱말 · 찾기</b> 세 가지면 충분하니까요.
    </p>
    <aside class="memo">
      <div class="h">부모용 지도 노트</div>
      <p>dig을 dog으로 쓰는 건 아주 흔한 실수입니다. 틀렸다고 하지 말고 <q>그건 무슨 뜻이지?</q> 하고 옆의 한글 뜻을 다시 보게 하세요.</p>
      <p>4번은 지문에 <b>없는</b> 내용입니다. <q>지문에 그런 말 있었어?</q> 하고 되물어 주세요.</p>
      <p>답을 못 찾아도 문장 번호만 찾아내면 절반은 성공이에요.</p>
    </aside>
  </div>
</section>

<section>
  <div class="wrap">
    <p class="eyebrow">{len(units)}권</p>
    <h2 class="reveal">토끼로 시작해서 <mark>원기둥</mark>까지</h2>
    <p class="lead">쉬운 순서로 놓여 있습니다. 뒤로 갈수록 문장이 길어지고, 25권부터는 이야기가 나와요.</p>
    <div class="chips">{chips}</div>
  </div>
</section>

<section class="map">
  <div class="wrap">
    <p class="eyebrow">아이용</p>
    <h2 class="reveal">다 읽으면 <mark>도장을 쾅</mark></h2>
    <p class="lead">진도표는 어른 물건입니다. 아이한테는 도장 모으는 지도를 줬어요.</p>
    <div class="box">
      <div class="stamps" id="guideStamps" aria-hidden="true"></div>
      <div class="txt">
        <p>정거장 하나를 다 지나면 색종이가 쏟아지고, 토끼가 다음 칸으로 옮겨 갑니다.
           지금 어디쯤 왔는지 한눈에 보여요.</p>
        <button class="btn" data-close>🗺 지도로 돌아가기</button>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <div class="made">집에서 만든 영어 공부 자료</div>
    본문 출처 · EBS 초등 「Touch! 초등 영어 — 펀리딩」<br>
    인쇄는 A4 세로, 배율 100%, 배경 그래픽 켜기
  </div>
</footer>

</div>
"""

    out = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>영어 모험 지도 — 도장 {len(units)}개 모으기</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Jua&family=Gaegu:wght@400;700&display=swap" rel="stylesheet">
<style>{CSS}
{INTRO_CSS}</style>
</head>
<body>

<button class="guide-open" id="guideOpen">📋 안내 보기</button>

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

<div class="guide-back" id="guideBack"></div>
<aside class="guide" id="guide" role="dialog" aria-modal="true" aria-label="안내" aria-hidden="true">
  <button class="guide-close" id="guideClose">✕ 닫기</button>
  {intro}
</aside>

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
