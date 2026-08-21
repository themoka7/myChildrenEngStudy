#!/usr/bin/env python3
"""A4 문제지에서 어느 쪽이 넘치는지 짚어 준다.

`build_unit.py` 는 "잘림 발생"만 알려 주고 어느 쪽인지는 말해 주지 않는다.
`.page` 가 높이 고정 + `overflow:hidden` 이라 넘친 내용은 쪽수를 늘리지 않고
조용히 사라지므로, 각 쪽을 따로 떼어 높이를 풀고 렌더링해 본다.
한 쪽이 2장 이상으로 벌어지면 그 쪽이 넘치는 쪽이다.

사용법:
    python3 tools/where_overflow.py print/unit04.html
"""
import logging
import re
import sys

logging.getLogger("weasyprint").setLevel(logging.ERROR)

RELAX = ('<style>@media print{ .page{ height:auto !important; '
         'overflow:visible !important; } }</style>')
NAMES = ["1쪽 (문제 ①②)", "2쪽 (문제 ③④⑤⑥)", "3쪽 (정답지)"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("사용법: python3 tools/where_overflow.py <print/unitNN.html>")
    try:
        from weasyprint import HTML as WHTML
    except ImportError:
        raise SystemExit("weasyprint 가 없습니다: "
                         "pip install weasyprint --break-system-packages -q")

    src = open(sys.argv[1], encoding="utf-8").read()
    head = src.split("<body>")[0] + "<body>" + RELAX
    pages = re.findall(r'<section class="page.*?</section>', src, re.S)
    if not pages:
        raise SystemExit("`.page` 구역을 못 찾았습니다 — 스킬 템플릿이 바뀐 것 같습니다.")

    for name, page in zip(NAMES, pages):
        n = len(WHTML(string=head + page + "</body></html>", base_url=".").render().pages)
        print(f"  {name}: {n}장 {'← 넘침' if n > 1 else 'OK'}")


if __name__ == "__main__":
    main()
