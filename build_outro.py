"""AI 산책 아웃트로(약 5.5초) — 오프닝의 짝. 로고에서 걷는 사람이 'I' 자리를 떠나 산책길을 따라 걸어 나가고, 카메라가 따라 다가간 뒤 「다음 산책에서 만나요」로 끝난다.
그림·소리 모두 직접 만든 것(외부 영상·음원 사용 없음).
사용: python3 build_outro.py [출력.mp4]
"""
import os, sys, subprocess, wave, importlib.util
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'logo', 'AI산책_아웃트로.mp4')
FPS, T = 30, 5.6
W, H = 1920, 1080

spec = importlib.util.spec_from_file_location('c', os.path.join(HERE, 'logo', 'gen_calm.py'))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
bg, _ = c.svg(W, H, 330, 300, 1260, 480, seed=7, uid='i')

POSES = {
    'A': ['M68 58 L82 84 L100 94', 'M62 58 L46 84 L32 100', 'M60 104 L80 146 L88 184 L104 188', 'M54 104 L40 148 L16 178'],
    'M': ['M68 58 L74 86 L80 102', 'M62 58 L60 86 L58 104', 'M58 104 L62 146 L64 186 L80 188', 'M55 104 L50 146 L44 182'],
    'B': ['M68 58 L56 84 L42 100', 'M62 58 L76 84 L92 94', 'M60 104 L48 146 L28 180', 'M54 104 L70 146 L82 184 L98 186'],
}
WIDTH = [17, 17, 24, 24]

walker = ('<svg id="wk" viewBox="0 0 120 200" style="width: 250px; height: 415px; margin: 0 70px 22px -4px; overflow: visible">'
          '<defs><linearGradient id="wgI" gradientUnits="userSpaceOnUse" x1="20" y1="0" x2="100" y2="200">'
          '<stop offset="0" stop-color="#3BE8FF"></stop><stop offset="1" stop-color="#3D7BFF"></stop></linearGradient></defs>'
          '<g id="wb"><circle cx="72" cy="21" r="19" fill="url(#wgI)"></circle>'
          '<g fill="none" stroke="url(#wgI)" stroke-linecap="round" stroke-linejoin="round">'
          '<path d="M66 52 L56 104" stroke-width="32"></path>'
          + ''.join(f'<path id="p{k}" d="{POSES["A"][k]}" stroke-width="{WIDTH[k]}"></path>' for k in range(4)) +
          '</g></g></svg>')

GT = 'background: linear-gradient(135deg, #3BE8FF 0%, #3D7BFF 100%); -webkit-background-clip: text; background-clip: text; color: transparent'
html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:P;src:url({HERE}/PretendardVariable.woff2) format("woff2");font-weight:100 900}}
body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#0B1A4A;font-family:P}}
#cam{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;transform-origin:0 0}}
#logo{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px}}
.wm{{display:flex;align-items:flex-end;line-height:1}}
.L{{font-size:500px;font-weight:900;display:inline-block}}
#trail{{position:absolute;height:8px;border-radius:4px;background:repeating-linear-gradient(90deg,#3BE8FF 0 6px,transparent 6px 26px);filter:drop-shadow(0 0 8px #3BE8FF)}}
#sweep{{position:absolute;top:0;width:260px;height:{H}px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent);mix-blend-mode:overlay;transform:skewX(-18deg)}}
#fade{{position:absolute;inset:0;background:#0B1A4A}}
</style></head><body>
<div style="position:absolute;inset:0">{bg}</div>
<div id="cam">
 <div id="trail"></div>
 <div id="logo">
  <div class="wm"><span id="lA" class="L" style="letter-spacing:-.04em;{GT}">A</span>{walker}<span id="lS" class="L" style="letter-spacing:-.06em;color:#fff">산책</span></div>
  <p id="sub" style="margin:0;font-size:116px;font-weight:800;letter-spacing:-.02em;color:#DDE7FF">AI, 이렇게 써요</p>
 </div>
</div>
<div id="sweep"></div>

<div id="fade"></div>
<div id="end" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;opacity:0">
 <img src="{HERE}/logo/AI산책_로고_투명.png" style="height:170px">
 <p style="margin:0;font-size:84px;font-weight:900;letter-spacing:-.03em;color:#fff">다음 산책에서 만나요</p>
 <img src="{HERE}/slogan_white2.png" style="height:64px;margin-top:20px;opacity:.9">
</div>
<script>
const P={POSES};
const fl=[...document.querySelectorAll('.fli')].map(e=>({{e,L:parseFloat(getComputedStyle(e).getPropertyValue('--L'))||800,d:parseFloat(e.style.animationDuration)||6,o:parseFloat(e.style.animationDelay)||0}}));
fl.forEach(f=>{{f.e.style.animation='none'}});
const wk=document.getElementById('wk'); const r=wk.getBoundingClientRect();
const WX=r.left+r.width/2, WY=r.top+r.height/2, FOOT=r.bottom-14;
const cl=(x,a,b)=>Math.max(a,Math.min(b,x)); const ease=x=>1-Math.pow(1-cl(x,0,1),3); const eio=x=>{{x=cl(x,0,1);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2}};
function pose(t){{ // 걷기 주기 0.48초: A-M-B-M
  const k=Math.floor(t/0.12)%4; const name=['A','M','B','M'][k];
  for(let i=0;i<4;i++) document.getElementById('p'+i).setAttribute('d',P[name][i]);
}}
function pop(el,t0,t){{ const x=(t-t0)/0.32; if(x<=0){{el.style.opacity=0;el.style.transform='scale(.3)';return}}
  const s=x>=1?1:(x<.6?0.3+0.85*ease(x/.6):1.15-0.15*ease((x-.6)/.4)); el.style.opacity=cl(x*3,0,1); el.style.transform='scale('+s+')'; }}
function render(t){{
  // 0~0.9초: 완성된 로고, 부제 사라짐
  const sub=document.getElementById('sub'); sub.style.opacity=cl(1-(t-0.5)/0.4,0,1); sub.style.transform='translateY('+(-20*ease((t-0.5)/0.4))+'px)';
  // 0.8~: 'A'·'산책'이 작아지며 사라짐
  for(const [id,t0] of [['lA',0.85],['lS',0.95]]){{ const x=cl((t-t0)/0.3,0,1); const el=document.getElementById(id); el.style.opacity=1-x; el.style.transform='scale('+(1-0.6*ease(x))+')'; }}
  // 1.0~3.6초: 걷는 사람이 오른쪽으로 걸어 나감
  const w0=1.0, w1=3.6; const e=t<w0?0:Math.pow(cl((t-w0)/(w1-w0),0,1),1.35);
  const off=1500*e;
  if(t>w0) pose(t-w0); else pose(0);
  const bob=t>w0? Math.abs(Math.sin((t-w0)*Math.PI/0.24))*-10*e:0;
  wk.style.transform='translate('+off+'px,'+bob+'px)';
  // 카메라: 1.2초부터 걷는 사람을 따라가며 다가감(배율 1 → 3.6)
  const z=eio((t-1.2)/2.4); const s=1+(3.6-1)*z;
  const cx=({W}/2)*(1-z)+(WX+off)*z, cy=({H}/2)*(1-z)+(WY-60)*z;
  document.getElementById('cam').style.transform='translate('+({W}/2-cx*s)+'px,'+({H}/2-cy*s)+'px) scale('+s+')';
  // 지나온 빛길
  const tr=document.getElementById('trail'); const len=Math.max(0,off);
  tr.style.left=(WX)+'px'; tr.style.width=len+'px'; tr.style.top=(FOOT+6)+'px'; tr.style.opacity=t>w0?1:0;
  // 빛 스침(처음)
  const sw=document.getElementById('sweep'); const wx=cl((t-0.15)/0.6,0,1); sw.style.left=(-400+({W}+800)*wx)+'px'; sw.style.opacity=(wx>0&&wx<1)?1:0;
  // 회로 빛 흐름
  fl.forEach(f=>{{const ph=((t+f.o)/f.d)%1; f.e.style.strokeDashoffset=(f.L*ph).toFixed(1)}});
  // 3.4~3.8초 어두워짐 → 마지막 카드 → 끝에서 어둡게
  const fd=document.getElementById('fade'), en=document.getElementById('end');
  if(t<3.4){{fd.style.opacity=0;en.style.opacity=0}}
  else if(t<3.8){{fd.style.opacity=(t-3.4)/0.4;en.style.opacity=0}}
  else {{fd.style.opacity=1; const x=cl((t-3.8)/0.4,0,1); en.style.opacity=t>{T}-0.4?cl(({T}-t)/0.4,0,1):x; en.style.transform='scale('+(0.94+0.06*ease(x))+')'}}
}}
render(0);
</script></body></html>'''


def sound(path):
    sr = 48000; n = int(T * sr); buf = np.zeros(n)
    def add(t, s):
        i = int(t * sr); buf[i:i + len(s)] += s[:max(0, n - i)]
    # 처음 반짝(빛 스침)
    tt = np.arange(int(.6 * sr)) / sr
    add(0.15, .10 * np.sin(2 * np.pi * 2093 * tt) * np.exp(-tt * 6))
    # 글자가 작아지는 '쏙'
    for t0 in (0.85, 0.95):
        tt = np.arange(int(.16 * sr)) / sr; f = 900 - 600 * tt / .16
        add(t0, .28 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 20))
    # 멀어지는 발걸음
    for k in range(11):
        t = 1.06 + k * 0.24
        if t > 3.5: break
        tt = np.arange(int(.09 * sr)) / sr
        add(t, (.22 - .015 * k) * np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 45) + .05 * np.random.randn(len(tt)) * np.exp(-tt * 90))
    # 다가가는 바람 소리
    tt = np.arange(int(2.4 * sr)) / sr
    nz = np.random.randn(len(tt)); k = 400; nz = np.convolve(nz, np.ones(k) / k, mode='same') * 9
    add(1.2, .16 * nz * np.sin(np.pi * np.clip(tt / 2.4, 0, 1)) ** 2)
    # 마무리 '띠링'(내려가는 솔-미-도)
    for j, fr in enumerate([1568.0, 1318.5, 1046.5]):
        tt = np.arange(int(1.6 * sr)) / sr
        tone = np.sin(2 * np.pi * fr * tt) + .3 * np.sin(2 * np.pi * fr * 2 * tt)
        add(3.85 + j * 0.11, .15 * tone * np.exp(-tt * 2.6))
    buf = np.clip(buf, -1, 1); st = np.repeat((buf * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    hp = '/tmp/_outro.html'
    open(hp, 'w').write(html.replace('class="fli', 'class="fli').replace('flowi', 'flowi'))
    raw = '/tmp/_outro_raw.mp4'; wav = '/tmp/_outro.wav'
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = br.new_page(viewport={'width': W, 'height': H}, device_scale_factor=4 / 3)
        pg.goto('file://' + hp); pg.wait_for_timeout(1200)
        if os.environ.get('STILLS'):
            for t in [0.3, 1.0, 1.6, 2.4, 3.2, 3.6, 4.4, 5.2]:
                pg.evaluate(f'render({t})'); pg.screenshot(path=f'/tmp/outro_{t:.1f}.png')
            br.close(); sys.exit()
        ff = subprocess.Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', raw],
                              stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for k in range(int(T * FPS)):
            pg.evaluate(f'render({k / FPS})'); ff.stdin.write(pg.screenshot(type='jpeg', quality=92))
        ff.stdin.close(); ff.wait(); br.close()
    sound(wav)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-ar', '48000', '-shortest', '-movflags', '+faststart', OUT], check=True)
    print(OUT)
