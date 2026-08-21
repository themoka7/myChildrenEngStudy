#!/usr/bin/env python3
"""유닛 하나의 두 페이지를 만든다.

  read/unitNN.html   화면용 읽기 페이지   (english-reading-html 스킬)
  print/unitNN.html  A4 인쇄용 문제지     (eng-make-question 스킬)

두 스킬의 빌더를 그대로 호출한 뒤, 결과물에 사이트 내비게이션(목차/서로
건너가기 링크)만 덧붙인다. 스킬 템플릿과 CSS는 손대지 않는다 — 내비는
이 저장소의 관심사이고 스킬의 관심사가 아니다.

사용법:
    python3 tools/build_unit.py 1
    python3 tools/build_unit.py 1 --skills ~/.claude/skills/synced

입력은 data/unitNN.read.json 과 data/unitNN.quiz.json.
한쪽 데이터만 있으면 그쪽만 만들고 넘어간다.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SKILLS = os.path.expanduser("~/.claude/skills/synced")

# 스킬 빌더의 기본 진행 순서. 1번(워밍업)만 유닛마다 갈아 끼운다.
DEFAULT_ROUTINE = [
    None,  # warmup_line() 이 채운다
    '<b>3~8분</b> 1쪽 지문 소리 내어 읽기 2회. 부모가 못 읽어도 됩니다 — 아이가 읽고 부모가 듣기',
    '<b>8~17분</b> 1쪽 → 2쪽 순서로 손으로 풀기 (③번은 지문을 다시 봐도 됩니다)',
    '<b>17~19분</b> ⑥번 문장을 지문 안 보고 말해 보기',
    '<b>19~20분</b> 별점 색칠 + "오늘 새로 안 단어 하나만 말해줘"',
]


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"빌드 실패: {' '.join(cmd)}\n{p.stdout}{p.stderr}")
    return p.stdout + p.stderr


def inject(path, head_css, after_marker, nav_html):
    """생성된 HTML에 CSS 한 줄과 내비 링크를 끼워 넣는다."""
    html = open(path, encoding="utf-8").read()
    if "data-nav=" in html:
        return  # 이미 넣었다
    if after_marker not in html:
        sys.exit(f"내비를 넣을 자리를 못 찾았습니다: {path} ({after_marker!r})\n"
                 "스킬 템플릿이 바뀐 것 같습니다 — tools/build_unit.py 를 맞춰 주세요.")
    html = html.replace("</head>", f"<style>{head_css}</style>\n</head>", 1)
    html = html.replace(after_marker, after_marker + nav_html, 1)
    open(path, "w", encoding="utf-8").write(html)


# 읽기 페이지를 메인 지도와 같은 팔레트로 맞춘다. 스킬 템플릿은 그대로 두고
# :root 변수만 덮어쓴다 — 이 <style> 이 템플릿 스타일 뒤에 들어가서 이긴다.
# 지문 글꼴(세리프)은 건드리지 않는다. 읽기가 이 페이지의 목적이고, 제목과
# 버튼만 지도와 같은 글꼴로 맞춰도 같은 자료로 보인다.
READ_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
:root{
  --paper:#E8F0F7; --ink:#2A3F55; --muted:#6B8299; --line:#B9CDDD;
  --carrot:#E0384F; --carrot-soft:#FDE8EC;
  --leaf:#2F8F6B;   --leaf-soft:#DEF0E8;
  --sky:#3F7FA8;    --card:#FFFFFF;
  --grid:#D8E5F0;
  --f-round:'Jua','Malgun Gothic','Apple SD Gothic Neo',sans-serif;
}
body{
  background:
    linear-gradient(var(--grid) 1px,transparent 1px) 0 0/26px 26px,
    linear-gradient(90deg,var(--grid) 1px,transparent 1px) 0 0/26px 26px,
    var(--paper);
}
/* 격자 위에 지문을 그냥 얹으면 읽기 힘들다 — 지도의 칸처럼 흰 카드에 올린다 */
main,.closing{
  background:var(--card);border:2.5px solid var(--line);border-radius:18px;
  padding:22px 24px;box-shadow:0 3px 0 rgba(42,63,85,.10);
}
main{margin-top:14px}
.closing{margin-top:16px;background:var(--leaf-soft);border-color:#BFDFD1}
header{border-bottom:3px dashed var(--line)}
h1{font-family:var(--f-round);letter-spacing:-.5px}
.eyebrow{color:var(--carrot)}
/* 툴바는 스크롤에 붙어 따라오므로 종이색을 깔아 지문이 비쳐 보이지 않게 한다 */
.toolbar{background:rgba(232,240,247,.92);border-bottom:1px solid var(--line)}
/* 툴바 버튼도 지도와 같은 모양 — 두꺼운 테두리 + 아래로 떨어지는 그림자 */
.toolbar .btn{
  font-family:var(--f-round);border:2.5px solid var(--ink);
  box-shadow:0 3px 0 rgba(42,63,85,.16);
}
.toolbar .btn:hover{transform:translateY(-2px)}
.toolbar .btn.on{background:var(--carrot);border-color:var(--carrot)}
a.sitenav{text-decoration:none;display:inline-flex;align-items:center;gap:4px}
/* 듣기·해석 버튼: 템플릿은 opacity:.35 로 두고 줄에 마우스를 올릴 때만
   살려 놓는데, 휴대폰에는 hover 가 없어서 계속 흐린 채로 남는다. */
.say,.stog{opacity:.8}
@media (hover:none){ .say,.stog{opacity:1} }
.say{border-color:var(--line)}
.fab{font-family:var(--f-round);box-shadow:0 4px 0 rgba(42,63,85,.22)}
.tip .ipa{color:#A9C3D8}
.q-opt.wrong{background:var(--carrot-soft)}
/* 휴대폰에서는 카드 여백을 줄인다 — 양쪽 24px 을 그대로 두면 문장이 일찍 접힌다 */
@media (max-width:520px){ main,.closing{padding:16px 14px;border-radius:14px} }
"""


def build_read(n, skills):
    src = os.path.join(ROOT, "data", f"unit{n:02d}.read.json")
    out = os.path.join(ROOT, "read", f"unit{n:02d}.html")
    if not os.path.exists(src):
        return None
    print(run([sys.executable, os.path.join(skills, "english-reading-html", "build.py"),
               src, out]).strip())

    # 읽기 페이지는 밝은 툴바 — 스킬의 .btn 스타일을 그대로 재사용한다.
    inject(
        out,
        READ_CSS,
        '<div class="toolbar">',
        f'<a class="btn sitenav" data-nav="index" href="../index.html">← 목차</a>'
        f'<a class="btn sitenav" data-nav="print" href="../print/unit{n:02d}.html">🖨 A4 출력</a>',
    )
    return out


# 소리 하나로 읽는 글자 묶음. 긴 것부터 찾는다 (tch 가 ch 보다 먼저).
DIGRAPHS = ("tch", "qu", "ck", "ss", "ll", "ff", "zz", "sh", "ch", "th", "ng", "ph", "wh",
            "kn", "wr")  # knob·write 의 첫 글자는 소리가 없다
# 글자 이름과 소리가 다른 것만 바로잡는다 — c 는 /k/, kn 은 /n/ 하나.
SOUND = {"c": "k", "x": "ks", "qu": "kw", "kn": "n", "wr": "r"}


def sound_out(word):
    """단어를 소리 단위로 끊어 /h/-/o/-/p/ 꼴로 만든다. 확실하지 않으면 None."""
    w = word.lower()
    if not w.isalpha():
        return None
    parts, i = [], 0
    while i < len(w):
        for dg in DIGRAPHS:
            if w.startswith(dg, i):
                parts.append(dg)
                i += len(dg)
                break
        else:
            parts.append(w[i])
            i += 1
    # 모음 덩어리가 하나인 단음절만 끊어 준다. 다음절이나 모음 이중자는
    # 소리 규칙이 이 단계 밖이라, 잘못 끊어 주는 것보다 안 끊는 편이 낫다.
    vowels = [p for p in parts if p[0] in "aeiou"]
    if len(vowels) != 1 or len(vowels[0]) != 1:
        return None
    return "-".join(f"/{SOUND.get(p, p)}/" for p in parts)


def warmup_line(quiz):
    """정답지 「20분 진행 순서」 1번을 그 유닛의 ②번 첫 단어로 만든다.

    스킬 빌더의 기본값은 예시 지문(Rabbits)의 hop 으로 고정돼 있어서, 그대로
    두면 52장 전부가 자기 지문에 없는 단어를 연습시키라고 말한다.
    """
    ph = quiz["phonics"][0]
    word = ph["q"].replace("_", ph["a"])
    split = sound_out(word)
    hint = f"({split} → {word})" if split else f"(예: {word})"
    return f'<b>0~3분</b> 파닉스 워밍업 — ②번 단어를 소리로 먼저 읽히기 {hint}'


def build_print(n, skills):
    src = os.path.join(ROOT, "data", f"unit{n:02d}.quiz.json")
    out = os.path.join(ROOT, "print", f"unit{n:02d}.html")
    if not os.path.exists(src):
        return None

    # 워밍업 줄만 채워 임시 사본으로 넘긴다 — data/ 원본은 손대지 않는다.
    quiz = json.load(open(src, encoding="utf-8"))
    if not quiz.get("routine"):
        steps = DEFAULT_ROUTINE[:]
        steps[0] = warmup_line(quiz)
        quiz["routine"] = steps
        src = os.path.join(tempfile.gettempdir(), f"unit{n:02d}.quiz.json")
        json.dump(quiz, open(src, "w", encoding="utf-8"), ensure_ascii=False)

    # --check 는 weasyprint 로 실제 렌더링해 3쪽인지 / 잘린 곳이 없는지 본다.
    log = run([sys.executable, os.path.join(skills, "eng-make-question", "scripts", "build.py"),
               src, "-o", out, "--check"])
    print(log.strip())
    if "잘림 발생" in log:
        sys.exit("A4 레이아웃이 넘칩니다 — 문항을 덜어내고 다시 빌드하세요.")

    # 문제지는 어두운 툴바 — 링크도 거기에 맞춘다. 인쇄 시엔 툴바째로 숨겨진다.
    inject(
        out,
        ".toolbar a.sitenav{color:#fbbf24;font-weight:700;text-decoration:none;font-size:14px}",
        '<div class="toolbar">',
        f'<a class="sitenav" data-nav="index" href="../index.html">← 목차</a>'
        f'<a class="sitenav" data-nav="read" href="../read/unit{n:02d}.html">📖 읽기</a>',
    )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("unit", type=int, help="유닛 번호 (1~52)")
    ap.add_argument("--skills", default=DEFAULT_SKILLS,
                    help=f"스킬 디렉터리 (기본 {DEFAULT_SKILLS})")
    a = ap.parse_args()

    made = [p for p in (build_read(a.unit, a.skills), build_print(a.unit, a.skills)) if p]
    if not made:
        sys.exit(f"Unit {a.unit} 데이터가 없습니다 — "
                 f"data/unit{a.unit:02d}.read.json / .quiz.json 을 먼저 만드세요.")
    for p in made:
        print("  →", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
