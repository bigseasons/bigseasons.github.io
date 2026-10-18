"""개인정보처리방침·이용약관 페이지 데이터를 만든다.

원본은 앱 저장소(dday_manager)에 있다 — 여기서 고치지 말고 원본을 고친 뒤 다시 돌린다.
  - 개인정보처리방침: docs/홈페이지/privacy_policy.txt (4개 언어 전문, 중국어는 간체 → 번체 변환)
  - 이용약관: assets/translations/{ko,en,ja,zh}.json 의 settings_screen.termsOfService / tosBody

  python3 tools/build_legal.py ../dday_manager
  (번체 변환에 opencc-python-reimplemented 가 필요하다: pip install opencc-python-reimplemented)
"""
import html, json, re, sys
from pathlib import Path

import opencc

APP = Path(sys.argv[1] if len(sys.argv) > 1 else '../dday_manager')
OUT = Path(__file__).resolve().parent.parent / 'legal'
LANGS = ['ko', 'en', 'ja', 'zh']

# 글자만 바꾼다(s2tw). 어휘까지 바꾸는 s2twp 는 「注销账号」(계정 삭제)를 「登出」(로그아웃)로 바꿔
# 법적 의미가 달라진다. 대만에서 쓰는 「帳號」만 따로 맞춘다.
_cc = opencc.OpenCC('s2tw')
def to_tw(s):
    return _cc.convert(s).replace('賬號', '帳號').replace('賬戶', '帳戶')

def inline(text):
    """이스케이프한 뒤 주소·메일만 링크로."""
    t = html.escape(text.strip())
    t = re.sub(r'(https://bigseasons\.co\.kr/?)', r'<a href="\1">\1</a>', t)
    t = re.sub(r'([\w.+-]+@[\w-]+\.[\w.]+)', r'<a href="mailto:\1">\1</a>', t)
    return t

HEADING = re.compile(r'^(제\d+조 .+|\d+\. \S.*)$')
SUBHEAD = re.compile(r'^\s*\d+\)\s')
BULLET = re.compile(r'^\s*•\s*')

def blocks_html(lines):
    out, ul = [], []
    def flush():
        if ul:
            out.append('<ul>' + ''.join('<li>' + x + '</li>' for x in ul) + '</ul>')
            ul.clear()
    for raw in lines:
        if not raw.strip():
            flush(); continue
        if BULLET.match(raw):
            ul.append(inline(BULLET.sub('', raw))); continue
        flush()
        if SUBHEAD.match(raw):
            out.append('<h3>' + inline(raw) + '</h3>')
        else:
            out.append('<p>' + inline(raw) + '</p>')
    flush()
    return ''.join(out)

def parse_privacy(text):
    lines = text.splitlines()
    starts = [i for i in range(len(lines) - 2)
              if set(lines[i].strip()) == {'='} and set(lines[i + 2].strip()) == {'='}]
    docs = []
    for n, s in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = [l for l in lines[s + 3:end] if not l.startswith('--- End of document')]
        sep = next(i for i, l in enumerate(body) if l.strip() and set(l.strip()) == {'━'})
        meta = blocks_html([BULLET.sub('', l.replace('▣', '•', 1)) if l.startswith('▣') else l for l in body[:sep]])
        sections, cur = [], None
        for l in body[sep + 1:]:
            if HEADING.match(l):
                cur = {'h': l.strip(), 'lines': []}; sections.append(cur)
            elif cur is not None:
                cur['lines'].append(l)
        docs.append({
            'title': lines[s + 1].strip(),
            'meta': meta,
            'sections': [{'h': html.escape(x['h']), 'html': blocks_html(x['lines'])} for x in sections],
        })
    assert len(docs) == 4, len(docs)
    return dict(zip(LANGS, docs))

def label_end(line):
    """「유료 기능(예: 까먹지마+): …」처럼 괄호 안에도 콜론이 있어, 괄호 밖의 첫 콜론에서 자른다."""
    depth = 0
    for i, ch in enumerate(line[:40]):
        if ch in '(（「':
            depth += 1
        elif ch in ')）」':
            depth = max(0, depth - 1)
        elif ch in ':：' and depth == 0:
            return i
    return -1

def parse_terms(lang):
    t = json.loads((APP / f'assets/translations/{lang}.json').read_text())['settings_screen']
    lines = t['tosBody'].split('\n')
    items = []
    for l in lines[1:]:
        l = BULLET.sub('', l).strip()
        if not l:
            continue
        cut = label_end(l)
        items.append({'h': html.escape(l[:cut].strip()), 'html': '<p>' + inline(l[cut + 1:]) + '</p>'} if cut > 0
                     else {'h': '', 'html': '<p>' + inline(l) + '</p>'})
    return {'title': t['termsOfService'], 'meta': '<p>' + inline(lines[0]) + '</p>', 'sections': items}

privacy = parse_privacy((APP / 'docs/홈페이지/privacy_policy.txt').read_text())
zh = privacy['zh']
privacy['zh'] = {'title': to_tw(zh['title']), 'meta': to_tw(zh['meta']),
                 'sections': [{'h': to_tw(s['h']), 'html': to_tw(s['html'])} for s in zh['sections']]}
terms = {l: parse_terms(l) for l in LANGS}

OUT.mkdir(exist_ok=True)
for name, data in (('privacy', privacy), ('terms', terms)):
    (OUT / f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    print(name, {l: len(data[l]['sections']) for l in LANGS})
