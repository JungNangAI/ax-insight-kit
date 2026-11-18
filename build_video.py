"""중랑AX 인사이트 설명 동영상 (글주임 영상 방식)
사용: python3 build_video.py 회차NN_v2.json 회차NN_video.json  → vout_video/중랑AX인사이트_NN_설명영상.mp4
- 회차NN_v2.json : 카드뉴스 데이터(사례·숫자·예시 화면)
- 회차NN_video.json : 대본(lines: scene/say/cap[/calm]), bgm, keywords
장면 id: hook, intro, c1..cN, mission, safe, where, end
"""
import json, sys, os, re, asyncio, ssl, subprocess, math, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'vout_video')
FPS = 30
HL = [('#3D86FF', '#8CC4FF'), ('#7B6CFF', '#BDB4FF'), ('#27B85A', '#7FEBA2')]

def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode: raise RuntimeError(' '.join(cmd[:3]) + '\n' + r.stderr[-1500:])
    return r.stdout

def dur(p):
    return float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).strip())

# ---------- 1. 목소리 ----------
def tts_all(lines):
    import edge_tts
    ca = os.path.expanduser('~/.ccr/ca-bundle.crt')
    if os.path.exists(ca):
        edge_tts.communicate._SSL_CTX = ssl.create_default_context(cafile=ca)
    async def one(i, ln):
        p = os.path.join(OUT, f'L{i:02d}.mp3')
        rate, pitch = ('+0%', '+8Hz') if ln.get('calm') else ('+14%', '+20Hz')
        words = []
        for attempt in range(4):
            try:
                c = edge_tts.Communicate(ln['say'], 'ko-KR-SunHiNeural', rate=rate, pitch=pitch, boundary='WordBoundary')
                with open(p, 'wb') as f:
                    async for ch in c.stream():
                        if ch['type'] == 'audio': f.write(ch['data'])
                        elif ch['type'] == 'WordBoundary': words.append([ch['offset'] / 1e7, ch['text']])
                break
            except Exception:
                words = []; await asyncio.sleep(2 + attempt * 3)
        else:
            raise RuntimeError(f'TTS 실패: {i}')
        return p, words
    async def run():
        return [await one(i, ln) for i, ln in enumerate(lines, 1)]
    return asyncio.run(run())

# ---------- 2. 시간표 ----------
def timeline(lines, aud):
    t = 0.9; out = []
    for i, (ln, (p, words)) in enumerate(zip(lines, aud)):
        if i:
            t += 0.7 if ln['scene'] != lines[i - 1]['scene'] else 0.2
        d = dur(p)
        out.append({'s': round(t, 3), 'd': round(d, 3), 'scene': ln['scene'], 'w': [round(t + w[0], 3) for w in words]})
        t += d
    total = t + 4.2
    scenes = {}
    for i, L in enumerate(out):
        sc = scenes.setdefault(L['scene'], [L['s'] - 0.35, 0])
        sc[1] = L['s'] + L['d'] + 0.35
    first = out[0]['scene']; scenes[first][0] = 0
    scenes[out[-1]['scene']][1] = total
    return {'lines': out, 'scenes': scenes, 'total': round(total, 3)}

def mix_narr(aud, tl):
    p = os.path.join(OUT, 'narr.wav')
    ins, fl = [], []
    for k, ((a, _), L) in enumerate(zip(aud, tl['lines'])):
        ins += ['-i', a]; ms = int(L['s'] * 1000)
        fl.append(f'[{k}:a]aresample=48000,adelay={ms}|{ms}[a{k}]')
    fl.append(''.join(f'[a{k}]' for k in range(len(aud))) + f'amix=inputs={len(aud)}:normalize=0,apad=whole_dur={tl["total"]}[o]')
    sh(['ffmpeg', '-y', *ins, '-filter_complex', ';'.join(fl), '-map', '[o]', '-ac', '2', '-ar', '48000', '-t', str(tl['total']), p])
    return p

# ---------- 3. 장면 페이지 ----------
CSS = """
@font-face{font-family:'P';src:url(PretendardVariable.woff2) format('woff2');font-weight:100 900;}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;overflow:hidden;background:#0C1844}
body{font-family:'P',sans-serif;-webkit-font-smoothing:antialiased;word-break:keep-all;color:#F1F5FF}
.bg{position:absolute;inset:0;background:radial-gradient(ellipse 60% 45% at 92% 0%,rgba(80,140,255,.32),transparent 70%),
 radial-gradient(ellipse 50% 40% at 0% 100%,rgba(61,134,255,.16),transparent 70%),
 repeating-linear-gradient(0deg,rgba(140,180,255,.05) 0 1px,transparent 1px 64px),
 repeating-linear-gradient(90deg,rgba(140,180,255,.05) 0 1px,transparent 1px 64px),linear-gradient(180deg,#14275F,#0C1844)}
.scene{position:absolute;inset:0;opacity:0}
.a{will-change:transform,opacity}
.g{background:linear-gradient(90deg,var(--a),var(--b));-webkit-background-clip:text;background-clip:text;color:transparent}
.brand{font-size:38px;font-weight:900;color:#06102A;background:linear-gradient(90deg,#3BE8FF,#3D86FF);padding:8px 24px;border-radius:16px}
.slog{position:absolute;right:80px;top:56px;height:50px}
.hdr{position:absolute;left:80px;top:52px;display:flex;align-items:center;gap:16px}
.tile{border-radius:28px;padding:26px 20px;text-align:center}
.cardx{border-radius:28px;padding:34px 34px;background:rgba(255,255,255,.07);border:2px solid rgba(160,190,255,.3)}
"""

ENGINE = r"""
const TL = __TL__;
function cl(x){return x<0?0:x>1?1:x}
function ease(x){return 1-Math.pow(1-x,3)}
function back(x){const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)}
function tOf(spec){
  const m=/L(\d+)(?:w(\d+))?(?:f([\d.]+))?/.exec(spec); const L=TL.lines[+m[1]-1];
  if(m[2]){const w=L.w; if(!w.length) return L.s; return w[Math.min(+m[2],w.length)-1];}
  return L.s + (m[3]?+m[3]:0)*L.d;
}
const ELS=[...document.querySelectorAll('[data-a]')].map(e=>{const [ty,sp]=e.dataset.a.split('@');return {e,ty,t0:tOf(sp),out:e.dataset.out?tOf(e.dataset.out):null}});
function render(t){
  for(const s of document.querySelectorAll('.scene')){
    const r=TL.scenes[s.id]; const op=Math.min(cl((t-r[0])/0.5),cl((r[1]-t)/0.5)); s.style.opacity=op; s.style.display=op>0?'block':'none';
  }
  for(const o of ELS){
    const e=o.e; let p=(t-o.t0)/(o.ty==='type'?1.4:o.ty==='strike'?0.5:0.55); p=cl(p);
    let tr='',op=1;
    if(o.ty==='pop'){op=cl(p*3); const s=p<=0?0.5:0.5+0.5*back(p); tr=`scale(${s})`}
    else if(o.ty==='stamp'){op=cl(p*4); tr=`scale(${1+0.7*(1-ease(p))}) rotate(${-6*(1-ease(p))}deg)`}
    else if(o.ty==='up'){op=ease(p); tr=`translateY(${50*(1-ease(p))}px)`}
    else if(o.ty==='left'){op=ease(p); tr=`translateX(${-90*(1-ease(p))}px)`}
    else if(o.ty==='right'){op=ease(p); tr=`translateX(${90*(1-ease(p))}px)`}
    else if(o.ty==='fade'){op=ease(p)}
    else if(o.ty==='type'){e.style.clipPath=`inset(0 ${100-100*p}% 0 0)`; op=p>0?1:0}
    else if(o.ty==='strike'){e.style.setProperty('--sw',(p*100)+'%'); op=1}
    if(o.out!==null){const q=cl((t-o.out)/0.4); op*=1-q}
    if(t<o.t0 && o.ty!=='strike'){op=0}
    e.style.opacity=op; if(tr) e.style.transform=tr;
  }
  for(const f of document.querySelectorAll('.float')){const k=+(f.dataset.k||0); f.style.transform=`translateY(${Math.sin(t*2.2+k)*10}px) rotate(${Math.sin(t*1.6+k)*2}deg)`}
}
window.render=render; render(0);
"""

def L(n, w=None, f=None):
    s = f'L{n}'
    if w: s += f'w{w}'
    if f is not None: s += f'f{f}'
    return s

def scene_lines(lines, sid):
    return [i for i, l in enumerate(lines, 1) if l['scene'] == sid]

def mock(c, w=820):
    sys.path.insert(0, HERE)
    import build_v2
    html = build_v2.MOCK[c['mock']](c)
    return f'<div style="width:936px;zoom:{w/936:.3f}">{html}</div>'


def case_long(d, c, i, lines, hdr, slog):
    a, b = HL[(i - 1) % 3]; S = []
    pill = (f'<span style="font-size:34px;font-weight:900;color:#06102A;background:linear-gradient(90deg,{a},{b});'
            f'border-radius:999px;padding:8px 26px">{c.get("label", f"사례 {i}")}</span><span style="font-size:38px;font-weight:800">{c["org_short"]} · {c["tool"]}</span>'
            + (f'<span style="font-size:30px;font-weight:900;color:#FFD666;border:3px solid #FFD666;border-radius:999px;padding:4px 20px">{c["tag"]}</span>' if c.get("tag") else ''))
    def spread(h, n, start=1):
        rest = h[start:] or h
        out = []
        for k in range(n):
            pos = k * len(rest) / n; j = rest[int(pos)]; fr = round(pos - int(pos), 2)
            out.append(L(j, f=max(0.08, fr)))
        return out
    title = c['title'].replace('<em>', f'<span style="color:{b}">').replace('</em>', '</span>')
    # a: 무엇이 불편했나
    h = scene_lines(lines, f'c{i}a')
    if h:
        bl = c.get('before_v', c['before']); at = spread(h, len(bl))
        bf = ''.join(
            f'<div class="a cardx" data-a="left@{at[k]}" style="display:flex;gap:24px;align-items:center;margin-top:22px">'
            f'<span style="font-size:44px;font-weight:900;color:#8D99B8">–</span>'
            f'<span style="font-size:44px;font-weight:700;color:#DDE7FF">{x}</span></div>'
            for k, x in enumerate(bl))
        S.append(
            f'<div class="scene" id="c{i}a">{hdr}{slog}'
            f'<div style="position:absolute;left:100px;top:170px;right:520px">'
            f'<div class="a" data-a="left@{L(h[0], f=0)}" style="display:flex;align-items:center;gap:18px">{pill}</div>'
            f'<p class="a" data-a="up@{L(h[0], f=0.1)}" style="font-size:92px;font-weight:900;letter-spacing:-.045em;line-height:1.12;margin-top:24px">{title}</p>'
            f'<p class="a" data-a="fade@{L(h[0], f=0.7)}" style="font-size:36px;font-weight:900;color:#8D99B8;margin-top:44px;letter-spacing:.04em">이런 게 불편했어요</p>{bf}</div>'
            f'<div class="float" data-k="{i}" style="position:absolute;right:120px;top:300px">'
            f'<img class="a" data-a="pop@{L(h[0], f=0.5)}" src="{c["char"]}" style="width:360px"></div></div>')
    # b: 어떻게 만들었나
    h = scene_lines(lines, f'c{i}b')
    if h:
        ml = c.get('made_v', c['made']); at = spread(h, len(ml), start=0)
        md = ''.join(
            f'<div class="a" data-a="left@{at[k]}" style="display:flex;gap:22px;align-items:flex-start;margin-top:30px">'
            f'<span style="flex:none;width:64px;height:64px;border-radius:18px;background:linear-gradient(135deg,{a},{b});color:#06102A;'
            f'font-size:32px;font-weight:900;display:flex;align-items:center;justify-content:center">{k + 1}</span>'
            f'<span style="font-size:42px;font-weight:800;line-height:1.35;padding-top:6px">{x}</span></div>'
            for k, x in enumerate(ml))
        S.append(
            f'<div class="scene" id="c{i}b">{hdr}{slog}'
            f'<div style="position:absolute;left:100px;top:170px;width:820px">'
            f'<div style="display:flex;align-items:center;gap:18px">{pill}</div>'
            f'<p class="a" data-a="up@{L(h[0], f=0)}" style="font-size:62px;font-weight:900;letter-spacing:-.04em;margin-top:26px">AX 포인트 · <span style="color:{b}">이렇게 만들었습니다</span></p>'
            f'<p class="a" data-a="fade@{L(h[0], f=0.05)}" style="font-size:36px;font-weight:800;color:#C9D6F5;margin-top:14px">만든 사람 · {c["who"]}</p>{md}</div>'
            f'<div class="a" data-a="right@{L(h[0], f=0.3)}" style="position:absolute;right:90px;top:330px">{mock(c, 860)}</div></div>')
    # c: 성과
    h = scene_lines(lines, f'c{i}c')
    if h:
        gl = c.get('good_v', c['good']); at = spread(h, len(gl), start=0); four = len(gl) > 3
        tiles = ''.join(
            f'<div class="a tile" data-a="pop@{at[k]}" style="flex:{"0 0 calc(50% - 15px)" if four else "1"};background:{a}26;border:3px solid {a};padding:{"28px" if four else "40px"} 20px">'
            f'<p class="g" style="--a:{a};--b:{b};font-size:{(72 if four else 96) if len(v_) <= 6 else (64 if four else 76)}px;font-weight:900;letter-spacing:-.03em;line-height:1.1">{v_}</p>'
            f'<p style="font-size:36px;font-weight:700;color:#DDE7FF;margin-top:16px">{l_}</p></div>'
            for k, (v_, l_) in enumerate(gl))
        S.append(
            f'<div class="scene" id="c{i}c">{hdr}{slog}'
            f'<div style="position:absolute;left:100px;right:100px;top:170px">'
            f'<div style="display:flex;align-items:center;gap:18px">{pill}</div>'
            f'<p class="a" data-a="up@{L(h[0], f=0)}" style="font-size:66px;font-weight:900;letter-spacing:-.04em;margin-top:26px">이렇게 <span style="color:{b}">좋아졌습니다</span></p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:30px;margin-top:{36 if four else 50}px">{tiles}</div></div></div>')
    # d: 우리 구라면
    h = scene_lines(lines, f'c{i}d')
    if h:
        jt = re.sub(r'</?b>', '', c['jungnang'])
        side = ''; right = 100
        if c.get('site'):
            import qrcode
            q = os.path.join(OUT, f'site{i}.png')
            qq = qrcode.QRCode(border=1, box_size=12); qq.add_data(c['site']); qq.make(fit=True); qq.make_image().save(q)
            side = (f'<div class="a" data-a="pop@{L(h[0], f=0.4)}" style="position:absolute;right:120px;top:330px;text-align:center">'
                    f'<img src="{q}" style="width:340px;border-radius:24px;border:12px solid #fff">'
                    f'<p style="font-size:38px;font-weight:900;color:{b};margin-top:18px">{c.get("site_label", "바로 보기")}</p>'
                    f'<p style="font-size:32px;color:#DDE7FF;margin-top:6px">{c.get("site_text", "")}</p></div>')
            right = 640
        S.append(
            f'<div class="scene" id="c{i}d">{hdr}{slog}'
            f'<div style="position:absolute;left:100px;right:{right}px;top:170px">'
            f'<div style="display:flex;align-items:center;gap:18px">{pill}</div>'
            f'<p class="a" data-a="up@{L(h[0], f=0)}" style="font-size:76px;font-weight:900;letter-spacing:-.04em;margin-top:26px">따라 만들기 · <span style="color:{b}">우리 구라면?</span></p>'
            f'<p class="a" data-a="up@{L(h[-1], f=0.05)}" style="font-size:42px;font-weight:700;line-height:1.5;color:#EAF0FF;margin-top:30px">{jt}</p>'
            f'<div class="a" data-a="type@{L(h[-1], f=0.35)}" style="margin-top:30px;border-radius:30px 30px 30px 10px;background:#fff;color:#0B1638;padding:26px 34px;font-size:34px;font-weight:700;line-height:1.5">'
            f'<span style="display:block;font-size:28px;color:#B07A00;font-weight:900;margin-bottom:6px">오늘 5분 미션</span>{c["prompt"]}</div></div>{side}</div>')
    return S

def build_scenes(d, v):
    lines = v['lines']; vol = d['vol']
    hdr = f'<div class="hdr"><span class="brand">중랑AX 인사이트</span><span style="font-size:44px;font-weight:900">#{vol:02d}</span></div>'
    slog = '<img class="slog" src="slogan_white2.png">'
    HK1 = v.get('hook1', 'AI로 바뀐 행정,')
    HK2 = v.get('hook2', '<span style="color:#3BE8FF">무엇이</span> 달라졌을까요?')
    HK3 = v.get('hook3', '다른 기관은 이미 <b style="color:#fff">성과</b>를 내고 있습니다.')
    ML = v.get('mission_lead', '소개한 사례 모두, <b style="color:#fff">현장의 불편 하나</b>에서 시작했습니다.')
    S = []
    # hook
    h = scene_lines(lines, 'hook')
    if h:
        S.append(f'''<div class="scene" id="hook">{slog}
    <div style="position:absolute;left:150px;top:250px">
    <p class="a" data-a="up@{L(h[0],f=0)}" style="font-size:44px;font-weight:800;color:#8CE8FF">중랑AX 인사이트 #{vol:02d}</p>
    <p class="a" data-a="up@{L(h[0],f=0.05)}" style="font-size:118px;font-weight:900;letter-spacing:-.05em;line-height:1.15;margin-top:24px">{HK1}</p>
    <p class="a" data-a="up@{L(h[0],f=0.35)}" style="font-size:118px;font-weight:900;letter-spacing:-.05em;line-height:1.15">{HK2}</p>{('<p class="a" data-a="up@' + L(h[-1], f=0.1) + '" style="font-size:52px;font-weight:800;color:#DDE7FF;margin-top:40px">' + HK3 + '</p>') if len(h) > 1 else ''}</div>
    <div class="float" style="position:absolute;right:170px;top:330px"><img class="a" data-a="pop@{L(h[0],f=0.5)}" src="chars/main.png" style="width:420px"></div></div>''')
    # intro
    h = scene_lines(lines, 'intro')
    if h:
        chips = ''
    for i, c in enumerate(d['cases'], 1):
        a, b = HL[(i - 1) % 3]
        chips += f'''<div class="a tile" data-a="up@{L(h[-1], f=round(0.35 + 0.15 * i, 2))}" style="flex:1;background:{a}26;border:3px solid {a}">
<p style="font-size:34px;font-weight:800;color:#C9D6F5">{c["org_short"]}</p><p style="font-size:50px;font-weight:900;margin-top:6px;color:{b}">{c["tool"]}</p></div>'''
    S.append(f'''<div class="scene" id="intro">{slog}
<div style="position:absolute;left:150px;right:150px;top:170px;text-align:center">
<div class="a" data-a="stamp@{L(h[0],f=0)}" style="display:inline-flex;align-items:center;gap:26px"><span class="brand" style="font-size:92px;padding:14px 44px;border-radius:30px">중랑AX 인사이트</span><span style="font-size:110px;font-weight:900">#{vol:02d}</span></div>
<p class="a" data-a="up@{L(h[-1],f=0)}" style="font-size:64px;font-weight:900;margin-top:50px;letter-spacing:-.03em">{d.get("intro_text") or ('공무원이 <span style="color:#3BE8FF">AI로 직접</span> 만든 업무 도구 <span style="color:#3BE8FF">' + str(len(d["cases"])) + '</span>')}</p>
<div style="display:flex;gap:30px;margin-top:50px">{chips}</div></div></div>''')
    # cases
    for i, c in enumerate(d['cases'], 1):
        if scene_lines(lines, f'c{i}a'):
            S += case_long(d, c, i, lines, hdr, slog); continue
        if not scene_lines(lines, f'c{i}'):
            continue
        a, b = HL[(i - 1) % 3]; sid = f'c{i}'; h = scene_lines(lines, sid)
        stat_at = []
        rest = h[1:] or h
        for k in range(len(c['good'])):
            j = rest[min(k * len(rest) // len(c['good']), len(rest) - 1)]
            stat_at.append(L(j, f=0.15 if len(rest) >= len(c['good']) else round(0.15 + 0.3 * k, 2)))
        tiles = ''.join(f'''<div class="a tile" data-a="pop@{stat_at[k]}" style="flex:1;background:{a}26;border:3px solid {a}">
<p class="g" style="--a:{a};--b:{b};font-size:{72 if len(v_) <= 6 else 60}px;font-weight:900;letter-spacing:-.03em;line-height:1.1">{v_}</p>
<p style="font-size:30px;font-weight:700;color:#DDE7FF;margin-top:10px">{l_}</p></div>''' for k, (v_, l_) in enumerate(c['good']))
        title = c['title'].replace('<em>', f'<span style="color:{b}">').replace('</em>', '</span>')
        S.append(f'''<div class="scene" id="{sid}">{hdr}{slog}
<div style="position:absolute;left:80px;top:170px;width:820px">
<div class="a" data-a="left@{L(h[0],f=0)}" style="display:flex;align-items:center;gap:16px"><span style="font-size:36px;font-weight:900;color:#06102A;background:linear-gradient(90deg,{a},{b});border-radius:999px;padding:8px 28px">사례 {i}</span><span style="font-size:40px;font-weight:800">{c["org_short"]}</span></div>
<p class="a" data-a="left@{L(h[0],f=0.1)}" style="font-size:76px;font-weight:900;letter-spacing:-.045em;line-height:1.15;margin-top:26px">{title}</p>
<p class="a" data-a="left@{L(h[0],f=0.3)}" style="font-size:34px;font-weight:800;color:{b};margin-top:20px">만든 사람 · {c["who"]}</p></div>
<div class="a" data-a="right@{L(h[0],f=0.4)}" style="position:absolute;right:80px;top:180px">{mock(c, 860)}</div>
<div style="position:absolute;left:80px;right:80px;top:620px;display:flex;gap:26px">{tiles}</div>
<div class="float" data-k="{i}" style="position:absolute;left:560px;top:372px"><img class="a" data-a="pop@{L(h[0],f=0.6)}" src="{c["char"]}" style="width:230px"></div></div>''')
    # mission
    h = scene_lines(lines, 'mission'); c0 = d['cases'][0]
    if h:
        steps = ['귀찮은 일 하나 고르기', '구에서 허용한 AI에게 말로 부탁', '틀린 곳 알려 주며 다듬기']
        st = ''.join(f'<div class="a cardx" data-a="up@{L(h[-1], f=round(0.1 + 0.2 * k, 2))}" style="flex:1;display:flex;align-items:center;gap:20px"><span style="flex:none;width:70px;height:70px;border-radius:20px;border:3px solid #3BE8FF;font-size:38px;font-weight:900;display:flex;align-items:center;justify-content:center">{k + 1}</span><span style="font-size:36px;font-weight:800">{s}</span></div>' for k, s in enumerate(steps))
        S.append(f'''<div class="scene" id="mission">{hdr}{slog}
    <div style="position:absolute;left:150px;right:150px;top:170px">
    {('<p class="a" data-a="up@' + L(h[0], f=0) + '" style="font-size:44px;font-weight:800;color:#DDE7FF;margin-bottom:10px">' + ML + '</p>') if len(h) > 2 else ''}
    <p class="a" data-a="stamp@{L(h[-2] if len(h) > 1 else h[0],f=0.2)}" style="font-size:110px;font-weight:900;letter-spacing:-.05em">오늘 <span style="color:#FFD666">5분</span> 미션</p>
    <div class="a" data-a="type@{L(h[-2] if len(h) > 1 else h[0],f=0.55)}" style="margin-top:30px;border-radius:30px 30px 30px 10px;background:#fff;color:#0B1638;padding:32px 40px;font-size:40px;font-weight:700;line-height:1.5">{c0["prompt"]}</div>
    <div style="display:flex;gap:24px;margin-top:40px">{st}</div></div></div>''')
    # safe
    h = scene_lines(lines, 'safe')
    if h:
        rules = [('01', '개인정보는 넣지 않기', '주민·직원 정보는 지우거나 가짜로'), ('02', '구에서 허용한 AI로만', '업무 자료는 보안 지침 확인 후'), ('03', '최종 판단은 사람이', 'AI 결과는 초안, 근거는 직접 확인')]
        rl = ''.join(f'<div class="a cardx" data-a="pop@{L(h[0], f=round(0.05 + 0.3 * k, 2))}" style="flex:1;text-align:center;padding:50px 30px"><p style="font-size:64px;font-weight:900;color:#3BE8FF">{ic}</p><p style="font-size:48px;font-weight:900;margin-top:20px">{t}</p><p style="font-size:32px;color:#C9D6F5;margin-top:14px">{x}</p></div>' for k, (ic, t, x) in enumerate(rules))
        S.append(f'''<div class="scene" id="safe">{hdr}{slog}
    <div style="position:absolute;left:150px;right:150px;top:180px"><p class="a" data-a="up@{L(h[0],f=0)}" style="font-size:80px;font-weight:900;letter-spacing:-.04em">꼭 지킬 것 <span style="color:#3BE8FF">3가지</span></p>
    <div style="display:flex;gap:30px;margin-top:50px">{rl}</div></div></div>''')
    # where
    h = scene_lines(lines, 'where')
    if h:
        crumbs = ['새올게시판', '기획예산과', '중랑AX 인사이트']
        cr = ' <span style="color:#8CE8FF">›</span> '.join(f'<span class="a" data-a="up@{L(h[0], f=round(0.35 + 0.15 * k, 2))}" style="display:inline-block">{x}</span>' for k, x in enumerate(crumbs))
        S.append(f'''<div class="scene" id="where">{hdr}{slog}
    <div style="position:absolute;left:150px;right:150px;top:230px;text-align:center">
    <div class="cardx" style="display:inline-block;padding:44px 64px;font-size:68px;font-weight:900;letter-spacing:-.03em">{cr}</div>
    <p class="a" data-a="stamp@{L(h[-1],f=0.1)}" style="margin-top:70px;font-size:96px;font-weight:900;letter-spacing:-.04em">매주 <span style="color:#3BE8FF">목요일</span></p></div></div>''')
    # end
    h = scene_lines(lines, 'end')
    if h:
        S.append(f'''<div class="scene" id="end">
    <div style="position:absolute;left:150px;top:200px">
    <p class="a" data-a="up@{L(h[0],f=0)}" style="font-size:96px;font-weight:900;letter-spacing:-.05em;line-height:1.15">다음 사례의<br>주인공은,</p>
    <p class="a" data-a="stamp@{L(h[0],f=0.55)}" style="font-size:120px;font-weight:900;letter-spacing:-.05em;line-height:1.2;margin-top:10px;color:#3BE8FF">바로 여러분.</p></div>
    <div class="float" style="position:absolute;right:220px;top:220px"><img class="a" data-a="pop@{L(h[0],f=0.3)}" src="chars/chuk.png" style="width:460px"></div>
    <img class="a" data-a="fade@{L(h[0],f=0.9)}" src="slogan_white2.png" style="position:absolute;right:180px;top:720px;height:80px"></div>''')
    return S

def page(d, v, tl):
    S = build_scenes(d, v)
    js = ENGINE.replace('__TL__', json.dumps(tl))
    html = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="bg"></div>{"".join(S)}<script>{js}</script></body></html>'
    p = os.path.join(HERE, f'_video_{d["vol"]:02d}.html'); open(p, 'w').write(html)
    return p

# ---------- 4. 찍기 ----------
def capture(html, tl, out, t0=0, t1=None, still=None):
    from playwright.sync_api import sync_playwright
    t1 = t1 or tl['total']
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = br.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=4 / 3)
        pg.goto('file://' + html); pg.wait_for_timeout(1200)
        if still is not None:
            for t in still:
                pg.evaluate(f'render({t})'); pg.screenshot(path=os.path.join(OUT, f'still_{t:05.1f}.png'))
            br.close(); return
        ff = subprocess.Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', out],
                              stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        n = int(round((t1 - t0) * FPS))
        for k in range(n):
            pg.evaluate(f'render({t0 + k / FPS})')
            ff.stdin.write(pg.screenshot(type='jpeg', quality=92))
        ff.stdin.close(); ff.wait(); br.close()

# ---------- 5. 자막 ----------
def ass(v, tl):
    kw = sorted(v.get('keywords', []), key=len, reverse=True)
    def fmt(t):
        t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f'{h}:{m:02d}:{s:05.2f}'
    hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 2560
PlayResY: 1440
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: K,Noto Sans CJK KR Black,92,&H00FFFFFF,&H00B4B4B4,&H00401A0C,&H96000000,0,0,0,0,100,100,0,0,1,7,2,2,120,120,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    items = []
    for ln, T in zip(v['lines'], tl['lines']):
        cap = ln['cap']
        if len(cap) <= 34:
            items.append((cap, T['s'], T['d'])); continue
        mid = len(cap) / 2; cands = [m.end() for m in re.finditer(r'[,.] ', cap)]
        cut = min(cands, key=lambda x: abs(x - mid)) if cands else cap.rfind(' ', 0, int(mid) + 1) + 1
        p1, p2 = cap[:cut].strip(), cap[cut:].strip(); r = len(p1) / (len(p1) + len(p2))
        items.append((p1, T['s'], T['d'] * r)); items.append((p2, T['s'] + T['d'] * r, T['d'] * (1 - r)))
    for cap, s0, d0 in items:
        T = {'s': s0, 'd': d0}; words = cap.split(' ')
        # 20자 넘으면 두 줄
        brk = None
        if len(cap) > 20:
            acc = 0; best = None
            for k, w in enumerate(words[:-1]):
                acc += len(w) + 1
                if best is None or abs(acc - len(cap) / 2) < abs(best[1] - len(cap) / 2): best = (k, acc)
            brk = best[0]
        tot = sum(len(w) for w in words); dd = T['d'] * 0.95
        parts = []
        for k, w in enumerate(words):
            cs = max(1, int(round(dd * 100 * len(w) / tot)))
            ww = w
            for key in kw:
                if key in ww:
                    ww = ww.replace(key, '{\\1c&H0066D6FF&}' + key + '{\\1c&H00FFFFFF&}', 1); break
            parts.append(f'{{\\kf{cs}}}{ww}' + ('\\N' if k == brk else ' '))
        txt = '{\\fad(120,120)\\t(0,140,\\fscx104\\fscy104)\\t(140,260,\\fscx100\\fscy100)}' + ''.join(parts).rstrip()
        ev.append(f'Dialogue: 0,{fmt(T["s"] - 0.05)},{fmt(T["s"] + T["d"] + 0.02)},K,,0,0,0,,{txt}')
    p = os.path.join(OUT, 'cap.ass'); open(p, 'w').write(hdr + '\n'.join(ev) + '\n')
    return p

# ---------- 6. 효과음 ----------
def sfx(html_path, tl):
    html = open(html_path).read()
    sr = 48000; n = int(tl['total'] * sr) + sr; buf = np.zeros(n)
    def tof(spec):
        m = re.match(r'L(\d+)(?:w(\d+))?(?:f([\d.]+))?', spec); Lr = tl['lines'][int(m.group(1)) - 1]
        if m.group(2) and Lr['w']: return Lr['w'][min(int(m.group(2)), len(Lr['w'])) - 1]
        return Lr['s'] + (float(m.group(3)) if m.group(3) else 0) * Lr['d']
    def pop():
        t = np.arange(int(.12 * sr)) / sr; f = 520 + 900 * t / .12
        return .32 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 30)
    def thud():
        t = np.arange(int(.25 * sr)) / sr
        return .55 * np.sin(2 * np.pi * (95 - 40 * t) * t) * np.exp(-t * 14) + .08 * np.random.randn(len(t)) * np.exp(-t * 40)
    last = -1
    for ty, spec in re.findall(r'data-a="(pop|stamp)@([^"]+)"', html):
        t = tof(spec)
        if t - last < 0.12: continue
        last = t; s = pop() if ty == 'pop' else thud(); i = int(t * sr); buf[i:i + len(s)] += s[:max(0, n - i)]
    buf = np.clip(buf, -1, 1); st = np.repeat((buf * 32767).astype(np.int16)[:, None], 2, axis=1)
    p = os.path.join(OUT, 'sfx.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())
    return p


def bgm_chain(first, total):
    """첫 곡부터 시작해, 곡이 끝나면 반복하지 않고 다음 번호 곡으로 넘어간다(3초 겹쳐 넘김)."""
    d0 = os.path.dirname(first); m = re.search(r'(\d+)\.mp3$', first)
    files = sorted(f for f in os.listdir(d0) if re.fullmatch(r'\d+\.mp3', f))
    k = files.index(os.path.basename(first)) if m and os.path.basename(first) in files else 0
    seq, acc = [], 0.0
    while acc < total + 1 and len(seq) < len(files):
        f = os.path.join(d0, files[(k + len(seq)) % len(files)]); seq.append(f)
        acc += dur(f) - (3 if len(seq) > 1 else 0)
    out = os.path.join(OUT, 'bgm_chain.wav')
    if len(seq) == 1:
        sh(['ffmpeg', '-y', '-i', seq[0], '-ar', '48000', '-ac', '2', out]); return out, seq
    ins = sum([['-i', f] for f in seq], [])
    fl = []; prev = '[0:a]'
    for j in range(1, len(seq)):
        o = f'[x{j}]'; fl.append(f'{prev}[{j}:a]acrossfade=d=3:c1=tri:c2=tri{o}'); prev = o
    sh(['ffmpeg', '-y', *ins, '-filter_complex', ';'.join(fl), '-map', prev, '-ar', '48000', '-ac', '2', out])
    return out, seq

# ---------- 7. 섞기 ----------
def final(video, narr, sfxw, bgm, capf, tl, out):
    T = tl['total']
    fc = (f'[3:a]aresample=48000,atrim=0:{T},volume=0.55,afade=t=in:d=1,afade=t=out:st={T - 3}:d=3[m];'
          f'[1:a]asplit=2[n1][n2];[m][n2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];'
          f'[n1][md][2:a]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]')
    sh(['ffmpeg', '-y', '-i', video, '-i', narr, '-i', sfxw, '-i', bgm, '-filter_complex', fc,
        '-map', '0:v', '-map', '[a]', '-vf', f'ass={capf}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', str(T), '-movflags', '+faststart', out])

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open(sys.argv[1])); v = json.load(open(sys.argv[2]))
    mode = sys.argv[3] if len(sys.argv) > 3 else 'all'
    tlp = os.path.join(OUT, 'tl.json')
    if mode in ('all', 'audio'):
        aud = tts_all(v['lines']); tl = timeline(v['lines'], aud)
        json.dump({'tl': tl, 'aud': aud}, open(tlp, 'w'), ensure_ascii=False)
        mix_narr(aud, tl)
    else:
        tl = json.load(open(tlp))['tl']
    html = page(d, v, tl)
    if mode == 'stills':
        ts = [L_['s'] + L_['d'] * .8 for L_ in tl['lines']]
        capture(html, tl, None, still=ts); print('stills ok'); sys.exit()
    if mode == 'remix':
        capf = ass(v, tl); sx = sfx(html, tl)
        bg, seq = bgm_chain(os.path.join(HERE, v['bgm']), tl['total'])
        print('BGM:', ' → '.join(os.path.basename(s) for s in seq))
        out = os.path.join(OUT, v.get('out') or f'중랑AX인사이트_{d["vol"]:02d}_설명영상.mp4')
        final(os.path.join(OUT, 'raw.mp4'), os.path.join(OUT, 'narr.wav'), sx, bg, capf, tl, out); print(out); sys.exit()
    if mode in ('all', 'video'):
        raw = os.path.join(OUT, 'raw.mp4'); capture(html, tl, raw)
        capf = ass(v, tl); sx = sfx(html, tl)
        out = os.path.join(OUT, v.get('out') or f'중랑AX인사이트_{d["vol"]:02d}_설명영상.mp4')
        bg, seq = bgm_chain(os.path.join(HERE, v['bgm']), tl['total'])
        print('BGM:', ' → '.join(os.path.basename(s) for s in seq))
        final(raw, os.path.join(OUT, 'narr.wav'), sx, bg, capf, tl, out)
        print(out, round(tl['total'], 1), 's')
