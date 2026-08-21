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
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SKILLS = os.path.expanduser("~/.claude/skills/synced")


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
        "a.sitenav{text-decoration:none;display:inline-flex;align-items:center;gap:4px}",
        '<div class="toolbar">',
        f'<a class="btn sitenav" data-nav="index" href="../index.html">← 목차</a>'
        f'<a class="btn sitenav" data-nav="print" href="../print/unit{n:02d}.html">🖨 A4 출력</a>',
    )
    return out


def build_print(n, skills):
    src = os.path.join(ROOT, "data", f"unit{n:02d}.quiz.json")
    out = os.path.join(ROOT, "print", f"unit{n:02d}.html")
    if not os.path.exists(src):
        return None
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
