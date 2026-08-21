#!/usr/bin/env python3
"""문항 데이터와 생성된 링크를 전수 검사한다.

빌더(`eng-make-question`)도 자체 검증을 하지만, 아래 넷은 잡아 주지 않거나
경고로만 알려 주고 지나간다 — 그런데 넷 다 실제로 문제지를 망친 적이 있다.

  1. 파닉스 단어가 자기 지문에 없음
     → 아이가 지문에서 답을 확인할 수가 없다.
  2. 빈칸 정답이 보기에 없음 / `___` 표시 누락
  3. 인용한 문장 번호가 지문 범위를 벗어남
  4. O/X 정답이 한쪽으로 몰림
     → 전부 O면 읽지 않고도 만점이 나온다.

여기에 목차와 읽기 페이지의 링크가 실제 파일을 가리키는지도 함께 본다.

사용법:
    python3 tools/check_data.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    os.chdir(ROOT)
    errors, warnings = [], []

    units = sorted(int(re.search(r'unit(\d+)', p).group(1))
                   for p in glob.glob('data/unit*.quiz.json'))
    if not units:
        sys.exit("data/unitNN.quiz.json 이 하나도 없습니다.")

    for n in units:
        tag = f'unit{n:02d}'
        d = json.load(open(f'data/{tag}.quiz.json', encoding='utf-8'))
        flat = ' '.join(s for p in d['paras'] for s in p).lower()
        nsent = sum(len(p) for p in d['paras'])

        for ph in d['phonics']:
            word = ph['q'].replace('_', ph['a']).lower()
            if word not in flat:
                errors.append(f"{tag} 파닉스 '{ph['q']}' → '{word}' 가 지문에 없음")

        for f in d['fill']:
            if f['a'] not in d['fill_bank']:
                errors.append(f"{tag} 빈칸 정답 '{f['a']}' 가 보기에 없음")
            if '___' not in f['en']:
                errors.append(f"{tag} 빈칸 표시(___) 누락: {f['en']}")
        if len(d['fill_bank']) < len(d['fill']):
            errors.append(f"{tag} 보기 수가 문항 수보다 적음")

        for item in d['scan'] + d['tf']:
            for num in re.findall(r'\d+', item['sent']):
                if not 1 <= int(num) <= nsent:
                    errors.append(f"{tag} 문장번호 {num} 범위 초과 (지문 {nsent}문장)")

        o = sum(1 for t in d['tf'] if t['answer'] == 'O')
        if not 0 < o < len(d['tf']):
            errors.append(f"{tag} O/X 가 한쪽으로 몰림 (O {o}/{len(d['tf'])})")
        if not any('gloss' in t for t in d['tf']):
            warnings.append(f"{tag} O/X 에 지문 밖 단어 뜻풀이(gloss)가 하나도 없음")

        ko = [m['ko'] for m in d['match']]
        if sorted(ko) != sorted(d['match_ko_order']):
            errors.append(f"{tag} match_ko_order 가 match 와 다름")
        if ko == d['match_ko_order']:
            errors.append(f"{tag} match_ko_order 가 섞이지 않음")

    # 링크: 목차 → 각 페이지, 읽기 페이지 → A4 문제지
    if os.path.exists('index.html'):
        h = open('index.html', encoding='utf-8').read()
        for u in re.findall(r'href="((?:read|print)/[^"]+)"', h):
            if not os.path.exists(u):
                errors.append(f"목차 링크 깨짐: {u}")
    for n in units:
        p = f'read/unit{n:02d}.html'
        if not os.path.exists(p):
            continue
        m = re.search(r'data-nav="print" href="\.\./([^"]+)"', open(p, encoding='utf-8').read())
        if not m:
            errors.append(f"unit{n:02d} 읽기 페이지에 A4 출력 링크가 없음")
        elif not os.path.exists(m.group(1)):
            errors.append(f"unit{n:02d} A4 출력 링크 깨짐: {m.group(1)}")

    for w in warnings:
        print(f"  ⚠ {w}")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(f"\n검사 실패 — 오류 {len(errors)}건")
    print(f"유닛 {len(units)}개 검사 통과 (경고 {len(warnings)}건)")


if __name__ == "__main__":
    main()
