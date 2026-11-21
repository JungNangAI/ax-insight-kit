"""AI 산책 v2 — 표지 1 + 사례 1장씩 + 나도 해 보기 1 (PNG + 벡터 PDF)
사용: python3 build_v2.py 회차.json  → v2out/NN_k.png, v2out/AI산책_NN.pdf
"""
import json, sys, os, subprocess, re, qrcode
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'v2out')
HL = [('#3D86FF', '#8CC4FF'), ('#7B6CFF', '#BDB4FF'), ('#27B85A', '#7FEBA2')]
W = 1080

CSS = """
@font-face{font-family:'P';src:url(PretendardVariable.woff2) format('woff2');font-weight:100 900;}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:'P',sans-serif;-webkit-font-smoothing:antialiased;word-break:keep-all;color:#F1F5FF;background:#0C1844}
.pg{position:relative;width:1080px;background-color:#0E1C4C;padding:72px 72px 64px;overflow:hidden;
 background:radial-gradient(ellipse 80% 30% at 90% 0%,rgba(80,140,255,.30),transparent 70%),
 radial-gradient(ellipse 60% 25% at 0% 100%,rgba(61,134,255,.14),transparent 70%),
 repeating-linear-gradient(0deg,rgba(140,180,255,.045) 0 1px,transparent 1px 60px),
 repeating-linear-gradient(90deg,rgba(140,180,255,.045) 0 1px,transparent 1px 60px),
 linear-gradient(180deg,#14275F 0%,#0C1844 100%)}
b{font-weight:800;color:#fff}
.g{background:linear-gradient(90deg,var(--a),var(--b));-webkit-background-clip:text;background-clip:text;color:transparent}
.top{display:flex;align-items:center;gap:16px}
.brand{font-size:54px;font-weight:900;letter-spacing:-.02em;color:#06102A;background:linear-gradient(90deg,#3BE8FF,#3D86FF);padding:10px 30px;border-radius:20px;white-space:nowrap}
.lab{font-size:28px;font-weight:900;letter-spacing:.02em;color:var(--b)}
.sec{margin-top:52px}
.sec>.lab{display:flex;align-items:center;gap:14px;margin-bottom:22px}
.sec>.lab::after{content:"";flex:1;height:2px;background:linear-gradient(90deg,var(--a),transparent)}
.qr{width:168px;height:168px;border-radius:16px;border:6px solid #fff;background:#fff;flex:none}
"""

def nx(t):
    m = re.search(r'#\d+', t or ''); return m.group(0) if m else (t or '')
def josa(t):
    n = nx(t); return '으로' if n and n[-1] in '036' else '로'

def glue(html):
    def f(m):
        t = m.group(1)
        if len(t.strip()) > 14 and ' ' in t.strip():
            i = t.rstrip().rfind(' ')
            t = t[:i] + '&nbsp;' + t[i + 1:]
        return '>' + t + '<'
    return re.sub(r'>([^<>]+)<', f, html)

def em(s):
    return s.replace('<em>', '<span class="g">').replace('</em>', '</span>')

def qr(url, name):
    p = os.path.join(OUT, name)
    q = qrcode.QRCode(border=1, box_size=12); q.add_data(url); q.make(fit=True)
    q.make_image(fill_color='black', back_color='white').save(p)
    return p

def doc(body, extra=''):
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{extra}</style></head><body>{glue(body)}</body></html>'

def chrome(args):
    subprocess.run(['google-chrome', '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars'] + args,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)

def render(name, body):
    hp = os.path.join(HERE, f'_{name}.html'); open(hp, 'w').write(doc(body, 'html,body{background:#FF00FF}'))
    png = os.path.join(OUT, f'{name}.png')
    chrome(['--force-device-scale-factor=2', f'--screenshot={png}', '--window-size=1080,5000', '--virtual-time-budget=4000', f'file://{hp}'])
    im = Image.open(png).convert('RGB'); w, h = im.size; px = im.load(); bottom = h
    for y in range(h - 1, 0, -1):
        if px[w // 2, y] != (255, 0, 255):
            bottom = y + 1; break
    im.crop((0, 0, w, bottom)).save(png)
    css_h = bottom // 2
    # 벡터 PDF: 페이지 크기를 내용 높이에 정확히 맞춘다
    pp = os.path.join(HERE, f'_{name}_p.html')
    open(pp, 'w').write(doc(body, f'@page{{size:1080px {css_h + 2}px;margin:0}}html,body{{height:{css_h}px;overflow:hidden;background:#0C1844}}.g{{background:none!important;-webkit-text-fill-color:var(--s,var(--b));color:var(--s,var(--b))}}'))
    pdf = os.path.join(OUT, f'{name}.pdf')
    chrome(['--no-pdf-header-footer', '--print-to-pdf-no-header', f'--print-to-pdf={pdf}', '--virtual-time-budget=4000', f'file://{pp}'])
    return png, pdf

# ---------- 예시 화면 (글씨 최소 24px) ----------
def frame(title, inner):
    return f'''<div style="border-radius:24px;overflow:hidden;background:#081233;border:2px solid rgba(160,190,255,.45)">
<div style="height:60px;display:flex;align-items:center;gap:11px;padding:0 24px;background:rgba(120,160,255,.14);border-bottom:1px solid rgba(160,190,255,.25)">
<i style="width:15px;height:15px;border-radius:50%;background:#FF5F7E"></i><i style="width:15px;height:15px;border-radius:50%;background:#FFC94D"></i><i style="width:15px;height:15px;border-radius:50%;background:#3BE8A0"></i>
<span style="margin-left:10px;font-size:26px;font-weight:800">{title}</span><em style="margin-left:auto;font-style:normal;font-size:22px;font-weight:900;color:#06102A;background:#FFD666;border-radius:10px;padding:3px 12px">예시 화면</em></div>{inner}</div>'''

def mock_calendar(c):
    days = ['월', '화', '수', '목', '금']
    ev = {0: [('기획예산과', '간부회의', '#3D86FF')], 1: [('총무과', '직원 교육', '#2FB457'), ('복지정책과', '현장 점검', '#D23CB4')],
          2: [('○○동', '주민 행사', '#F5A524')], 3: [('기획예산과', '설명회', '#3D86FF')], 4: [('전 부서', '주간보고', '#8CB8FF')]}
    cols = ''
    for i, dn in enumerate(days):
        chips = ''.join(f'<div style="background:rgba(255,255,255,.09);border-left:6px solid {col};border-radius:9px;padding:10px 10px;margin-top:10px"><b style="display:block;font-size:24px">{t}</b><span style="font-size:24px;color:#CDD8F2">{x}</span></div>' for t, x, col in ev.get(i, []))
        cols += f'<div style="flex:1;min-width:0"><p style="font-size:28px;font-weight:900;color:#C9D6F5;text-align:center;padding-bottom:8px;border-bottom:1px solid rgba(160,190,255,.3)">{dn}</p>{chips}</div>'
    return frame('포미캐처 · 이번 주 전 부서 일정', f'<div style="display:flex;gap:10px;padding:20px">{cols}</div>')

def mock_manual(c):
    side = ''.join(f'<p style="font-size:24px;font-weight:700;color:{"#fff" if i == 1 else "#B9C6E8"};padding:9px 12px;border-radius:10px;background:{"rgba(255,255,255,.13)" if i == 1 else "transparent"}">{t}</p>' for i, t in enumerate(['연말정산', '출장·여비', '인사이동', '물품·회계']))
    return frame('서무실록 · 온라인 업무 매뉴얼', f'''<div style="display:flex;gap:20px;padding:22px"><div style="width:190px;flex:none;border-right:1px solid rgba(160,190,255,.25);padding-right:12px">{side}</div>
<div style="flex:1"><p style="font-size:30px;font-weight:900">출장 여비, 이럴 땐 이렇게</p>
<p style="font-size:25px;color:#D5DEF5;margin-top:10px;line-height:1.6">① 출장 전 : 신청·승인 확인<br>② 다녀와서 : 영수증·복명서<br>③ 정산 : 여비 서식 → 결재</p>
<p style="font-size:25px;font-weight:800;color:#FFD666;margin-top:8px">⚠ 자주 틀리는 곳 : 숙박비 상한</p></div></div>''')

def mock_minutes(c):
    bars = ''.join(f'<span style="display:inline-block;width:7px;height:{h}px;background:#7FEBA2;border-radius:3px;margin-right:5px;vertical-align:middle"></span>' for h in [18, 34, 24, 46, 30, 52, 22, 40, 28, 48, 20, 36])
    return frame('회의록 초안 AI · 내부망', f'''<div style="display:flex;align-items:center;gap:16px;padding:22px">
<div style="flex:1;background:rgba(255,255,255,.08);border-radius:14px;padding:18px 20px"><p style="font-size:24px;font-weight:900;color:#7FEBA2">녹음 파일</p>
<p style="font-size:25px;margin:8px 0">○○위원회_녹음.m4a</p><div>{bars}</div><p style="font-size:24px;color:#CDD8F2;margin-top:8px">1시간 40분</p></div>
<div style="font-size:52px;font-weight:900;color:#7FEBA2">→</div>
<div style="flex:1.1;background:rgba(255,255,255,.08);border-radius:14px;padding:18px 20px;font-size:25px;line-height:1.6;color:#E4EBFA"><p style="font-size:24px;font-weight:900;color:#7FEBA2">회의록 초안 · 10분</p>
일시 · 참석자<br>안건 1 : ○○ 심의<br>주요 발언 요약<br><b>의결 : 원안 가결</b></div></div>''')

def mock_list(c):
    # 범용 예시 화면: mock_title, mock_rows=[[왼쪽, 오른쪽, (색)]...], mock_note(선택)
    rows = ''
    for r in c.get('mock_rows', []):
        col = r[2] if len(r) > 2 else '#7FEBA2'
        rows += (f'<div style="display:flex;align-items:center;gap:16px;padding:14px 18px;margin-top:10px;border-radius:12px;background:rgba(255,255,255,.07)">'
                 f'<span style="flex:1;font-size:25px;color:#E4EBFA">{r[0]}</span>'
                 f'<span style="flex:none;font-size:24px;font-weight:900;color:#06102A;background:{col};border-radius:9px;padding:4px 14px">{r[1]}</span></div>')
    note = f'<p style="font-size:24px;font-weight:800;color:#FFD666;margin-top:14px">{c["mock_note"]}</p>' if c.get('mock_note') else ''
    return frame(c.get('mock_title', c.get('tool', '')), f'<div style="padding:12px 22px 22px">{rows}{note}</div>')

MOCK = {'calendar': mock_calendar, 'manual': mock_manual, 'minutes': mock_minutes, 'list': mock_list}

# ---------- 페이지 ----------
def cover(d):
    tiles = ''
    for i, c in enumerate(d['cases'], 1):
        a, b = HL[(i - 1) % 3]
        tiles += f'''<div style="--a:{a};--b:{b};--s:{b};margin-top:22px;border-radius:28px;padding:30px 34px;background:linear-gradient(100deg,{a}2E,rgba(255,255,255,.04) 70%);border:2px solid {a}">
<div style="display:flex;align-items:baseline;gap:14px"><span style="font-size:30px;font-weight:900;color:{b};white-space:nowrap">{c.get("label", f"0{i}")}</span><span style="font-size:30px;font-weight:700;color:#C9D6F5;white-space:nowrap">{c["org_short"]}</span><span style="font-size:32px;font-weight:900">· {c["tool"]}</span>{('<span style="margin-left:auto;flex:none;font-size:24px;font-weight:900;color:#FFD666;border:2px solid #FFD666;border-radius:999px;padding:2px 14px;white-space:nowrap">이슈 연관</span>') if c.get("tag") else ''}</div>
<p class="g" style="font-size:78px;font-weight:900;letter-spacing:-.04em;line-height:1.15;margin-top:8px">{c["cover_num"]}</p>
<p style="font-size:30px;font-weight:700;color:#DDE7FF;margin-top:4px">{c["cover_label"]}</p></div>'''
    body = f'''<div class="pg" style="--a:#3BE8FF;--b:#3D86FF;--s:#3BE8FF">
<div class="top"><p style="font-size:28px;font-weight:700;color:#C9D6F5">중랑AI혁신팀</p><img src="slogan_white2.png" style="height:52px;margin-left:auto;flex:none"></div>
<div style="display:flex;align-items:flex-end;justify-content:space-between;margin-top:40px">
<div><span class="brand" style="font-size:40px;padding:8px 26px">#{d["vol"]:02d}</span>
<p style="margin-top:30px;line-height:0"><img src="{os.path.join(HERE, 'logo', 'AI산책_로고_투명.png')}" alt="AI 산책" style="height:196px"></p>
<p style="font-size:76px;font-weight:900;letter-spacing:-.04em;line-height:1.1;margin-top:22px;color:#DDE7FF">{d.get("subtitle", "AI, 이렇게 써요")}</p></div>
<img src="chars/main.png" style="width:270px;margin-bottom:6px;flex:none"></div>
<p style="font-size:34px;font-weight:800;color:#8CE8FF;margin-top:44px">이번 호 · {d["theme"]}</p>
<p style="font-size:36px;line-height:1.5;color:#DDE7FF;margin-top:16px">{d["cover_sub"]}</p>
<div style="margin-top:30px">{tiles}</div>
<div style="margin-top:44px;border-radius:24px;padding:28px 32px;background:rgba(255,255,255,.07);display:flex;align-items:center;gap:20px">
<p style="font-size:34px;font-weight:800;line-height:1.45;flex:1">{d.get('cover_cta', '소개한 사례 모두,')} <span class="g">오늘 5분이면</span><br>우리 업무에 바로 써 볼 수 있습니다.</p><p style="font-size:44px;color:#8CE8FF;font-weight:900">▼</p></div>
</div>'''
    return body

def case(c, i, d):
    a, b = HL[(i - 1) % 3]
    bf = ''.join(f'<li style="font-size:31px;line-height:1.45;color:#AEB9D6;padding-left:28px;position:relative;margin-top:12px"><span style="position:absolute;left:0;top:0;color:#7D89A8">–</span>{x}</li>' for x in c['before'])
    af = ''.join(f'<li style="font-size:31px;line-height:1.45;font-weight:700;color:#fff;padding-left:36px;position:relative;margin-top:12px"><span style="position:absolute;left:0;top:0;color:{b};font-weight:900">✓</span>{x}</li>' for x in c['after'])
    good = ''.join(f'<div style="flex:1;text-align:center;padding:26px 8px;border-radius:22px;background:{a}1F;border:2px solid {a}66"><p class="g" style="font-size:{60 if len(v) <= 6 else 50}px;font-weight:900;letter-spacing:-.03em;line-height:1.1">{v}</p><p style="font-size:26px;font-weight:700;color:#DDE7FF;margin-top:12px;line-height:1.35">{l}</p></div>' for v, l in c['good'])
    made = ''.join(f'<div style="flex:1;border-radius:20px;padding:22px 22px;background:rgba(255,255,255,.06);font-size:28px;font-weight:700;line-height:1.4"><span style="display:block;font-size:26px;font-weight:900;color:{b};margin-bottom:6px">0{k}</span>{x}</div>' for k, x in enumerate(c['made'], 1))
    q1 = qr(c['url'], f'q{d["vol"]:02d}_{i}.png')
    issue_box = ''
    if c.get('tag'):
        issue_box = (f'<div style="margin-top:22px;border-radius:22px;padding:22px 26px;background:rgba(255,214,102,.10);border:2px solid #FFD666">'
                     f'<p style="font-size:27px;font-weight:900;color:#FFD666">{c["tag"]} · 왜 지금?</p>'
                     f'<p style="font-size:28px;line-height:1.5;color:#F3F0E0;margin-top:8px">{c.get("issue", "")}</p></div>')
    links = f'''<div style="display:flex;align-items:center;gap:22px;flex:1"><img class="qr" src="{q1}"><div><p style="font-size:30px;font-weight:900;color:{b}">{c["qr_label"]}</p><p style="font-size:26px;color:#C9D6F5;margin-top:6px">카메라로 비추면 열립니다</p></div></div>'''
    if c.get('site'):
        q2 = qr(c['site'], f's{d["vol"]:02d}_{i}.png')
        links += f'''<div style="display:flex;align-items:center;gap:22px;flex:1"><img class="qr" src="{q2}"><div><p style="font-size:30px;font-weight:900;color:{b}">{c["site_label"]}</p><p style="font-size:26px;color:#C9D6F5;margin-top:6px">{c["site_text"]}</p></div></div>'''
    body = f'''<div class="pg" style="--a:{a};--b:{b}">
<div class="top"><span style="font-size:30px;font-weight:900;color:#06102A;background:linear-gradient(90deg,{a},{b});border-radius:999px;padding:8px 26px;white-space:nowrap">{c.get("label", f"사례 {i}")}</span><span style="font-size:30px;font-weight:800;white-space:nowrap">{c["org_short"]}</span><img src="slogan_white2.png" style="height:52px;margin-left:auto;flex:none"></div>
<div style="display:flex;align-items:flex-end;gap:10px;margin-top:30px"><p style="flex:1;font-size:84px;font-weight:900;letter-spacing:-.045em;line-height:1.12">{em(c["title"])}</p><img src="{c["char"]}" style="width:230px;flex:none;margin-bottom:-6px"></div>
<p style="font-size:29px;font-weight:800;color:{b};margin-top:18px">{c.get("who_label", "만든 사람")} · {c["who"]}</p>{issue_box}
<p style="font-size:35px;line-height:1.55;color:#DDE7FF;margin-top:20px;padding-left:26px;border-left:6px solid {a}">{c["hook"]}</p>

<div class="sec"><p class="lab">무엇이 바뀌었나</p>
<div style="display:flex;align-items:stretch;gap:0">
<div style="flex:1;border-radius:24px 0 0 24px;padding:26px 26px 30px;background:rgba(255,255,255,.04);border:2px solid rgba(160,175,210,.25)"><p style="font-size:26px;font-weight:900;color:#8D99B8;letter-spacing:.06em">전에는</p><ul style="list-style:none">{bf}</ul></div>
<div style="width:56px;display:flex;align-items:center;justify-content:center;background:linear-gradient(90deg,rgba(255,255,255,.04),{a}33)"><span style="font-size:44px;font-weight:900;color:{b}">→</span></div>
<div style="flex:1.1;border-radius:0 24px 24px 0;padding:26px 26px 30px;background:{a}33;border:2px solid {a}"><p style="font-size:26px;font-weight:900;color:{b};letter-spacing:.06em">이제는</p><ul style="list-style:none">{af}</ul></div>
</div>
<div style="margin-top:26px">{MOCK[c["mock"]](c)}</div></div>

<div class="sec"><p class="lab">숫자로 보면</p><div style="display:flex;gap:16px">{good}</div></div>

<div class="sec"><p class="lab">AX 포인트 · 이렇게 만들었습니다</p><div style="display:flex;gap:14px">{made}</div></div>

<div class="sec" style="margin-top:60px"><div style="border-radius:30px;padding:38px 36px;background:linear-gradient(160deg,{a}40,{a}12);border:2px solid {b}">
<p style="font-size:30px;font-weight:900;color:{b}">작은 것부터 시작하기</p>
<p style="font-size:34px;line-height:1.55;color:#EAF0FF;margin-top:10px">{c["jungnang"]}</p>
<p style="font-size:30px;font-weight:900;color:#FFD666;margin-top:30px">오늘 5분 미션 · AI에 붙여 넣어 보세요</p>
<div style="margin-top:14px;border-radius:24px 24px 24px 8px;background:#fff;color:#0B1638;padding:26px 30px;font-size:31px;font-weight:700;line-height:1.55">{c["prompt"]}<span style="display:block;margin-top:12px;font-size:26px;font-weight:600;color:#5B6890">+ 메모·자료 붙여 넣기</span></div>
<p style="font-size:27px;font-weight:700;color:#FFC48A;margin-top:16px">⚠ {c["prompt_tip"]} · 개인정보는 넣지 않기</p></div></div>

<div style="display:flex;gap:28px;margin-top:44px;align-items:center">{links}</div>
<p style="font-size:24px;color:#9FB0D8;margin-top:22px">출처 : {c["src"]}</p>
</div>'''
    return body

def past_html(d):
    # 지난 회차 목록(최근 4개): [["#01","일정 공유·서무·회의록"], ...]
    ps = d.get('past', [])[-4:]
    if not ps: return ''
    row = ''.join(f'<span style="font-size:27px;font-weight:700;color:#DDE7FF;background:rgba(255,255,255,.07);border-radius:999px;padding:8px 20px"><b style="color:#8CE8FF">{n}</b> {x}</span>' for n, x in ps)
    return f'<div style="margin-top:28px"><p style="font-size:26px;font-weight:800;color:#9FB0D8;margin-bottom:12px">지난 회차 다시 보기</p><div style="display:flex;flex-wrap:wrap;gap:12px">{row}</div></div>'

def action(d):
    steps = [('귀찮은 일 하나 고르기', '10분', '매주 하는 취합, 매번 찾는 기준표, 반복되는 문서'),
             ('민감한 정보는 빼고 말하기', '10분', '이름·연락처·주민번호는 지우고, ‘이걸 넣으면 이게 나오게’ 말로 설명'),
             ('틀린 곳 알려 주며 다듬기', '10분~', '다른 곳을 그대로 말하면 고쳐 줍니다. 처음부터 완벽할 필요 없어요')]
    cols = ['#3BE8FF', '#5AA8FF', '#7B6CFF']
    st = ''.join(f'''<div style="display:flex;gap:26px;align-items:flex-start;padding:28px 0;border-top:1px solid rgba(160,190,255,.2)">
<p style="flex:none;width:76px;height:76px;border-radius:22px;border:3px solid {cols[k]};font-size:38px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 18px {cols[k]}66">{k + 1}</p>
<div style="flex:1"><p style="font-size:40px;font-weight:900">{t} <span style="font-size:26px;font-weight:800;color:{cols[k]};border:2px solid {cols[k]};border-radius:999px;padding:2px 14px;margin-left:8px;vertical-align:middle">{m}</span></p>
<p style="font-size:31px;color:#DDE7FF;margin-top:8px;line-height:1.45">{x}</p></div></div>''' for k, (t, m, x) in enumerate(steps))
    rules = [('민감한 정보는 빼고', '개인정보·내부 문서는 지우거나 바꿔서'), ('근거는 원문으로 확인', '법령·수치·연락처는 원문과 대조'), ('최종 판단은 사람이', 'AI 결과는 초안, 결정은 사람이')]
    rl = ''.join(f'<div style="flex:1;border-radius:20px;padding:22px 22px;background:rgba(255,255,255,.06)"><p style="font-size:29px;font-weight:900">{t}</p><p style="font-size:26px;color:#C9D6F5;margin-top:8px;line-height:1.4">{x}</p></div>' for t, x in rules)
    body = f'''<div class="pg" style="--a:#3BE8FF;--b:#3D86FF;--s:#3BE8FF">
<div class="top"><span style="font-size:30px;font-weight:900;color:#06102A;background:linear-gradient(90deg,#3BE8FF,#3D86FF);border-radius:999px;padding:8px 26px">나도 해 보기</span><img src="slogan_white2.png" style="height:52px;margin-left:auto;flex:none"></div>
<div style="display:flex;align-items:flex-end;justify-content:space-between;margin-top:34px">
<p style="font-size:92px;font-weight:900;letter-spacing:-.05em;line-height:1.12">다음 사례의<br>주인공은,<br><span class="g">중랑구 공무원</span>.</p>
<img src="chars/chuk.png" style="width:280px;flex:none;margin-bottom:10px"></div>
<p style="font-size:35px;line-height:1.55;color:#DDE7FF;margin-top:28px">{d.get('action_body', '소개한 사례 모두 <b>현장의 불편 하나</b>를 정확히 짚은 데서 시작했습니다. 우리 구 업무에 맞는 것부터, 30분이면 첫걸음을 뗄 수 있습니다.')}</p>
<div style="margin-top:36px">{st}</div>
<p style="font-size:30px;font-weight:900;color:#8CE8FF;margin-top:30px;margin-bottom:18px">꼭 지킬 것</p><div style="display:flex;gap:14px">{rl}</div>
<div style="margin-top:44px;border-radius:30px;padding:38px 36px;background:linear-gradient(120deg,rgba(59,232,255,.22),rgba(61,134,255,.22));border:2px solid rgba(255,255,255,.35)">
<p style="font-size:40px;font-weight:900;line-height:1.35">“우리 과도 이런 게 있으면 좋겠다”</p>
<p style="font-size:32px;line-height:1.55;color:#EAF0FF;margin-top:12px">떠오르는 업무를 <b>댓글</b>로 남겨 주세요. 다음 사례 선정과 우리 구 AX 과제에 반영합니다.</p></div>
<div style="margin-top:44px;border-radius:30px;padding:30px 36px;border:2px dashed rgba(140,232,255,.6);display:flex;align-items:center;gap:20px">
<p style="font-size:36px;font-weight:900;flex:1">다음 주에 <span style="color:#8CE8FF">{nx(d["next"])}</span>{josa(d["next"])} 이어집니다.</p></div>
{past_html(d)}
<div style="display:flex;align-items:center;justify-content:space-between;margin-top:40px"><p style="font-size:26px;font-weight:700;color:#9FB0D8">{d.get("board", "새올게시판 › 기획예산과")}</p><p style="font-size:26px;font-weight:800;color:#8CE8FF">중랑AI혁신팀</p></div>
</div>'''
    return body

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open(sys.argv[1]))
    pages = [cover(d)] + [case(c, i, d) for i, c in enumerate(d['cases'], 1)] + [action(d)]
    pdfs = []
    for k, body in enumerate(pages, 1):
        png, pdf = render(f'{d["vol"]:02d}_{k}', body); pdfs.append(pdf); print(png)
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in pdfs: w.append(p)
    out = os.path.join(OUT, d.get('pdf_name') or f'AI산책_{d["vol"]:02d}.pdf'); w.write(out); print(out)
