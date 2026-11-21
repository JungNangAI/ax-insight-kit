"""Original glowing-circuit background generator (SVG), PCB-style traces radiating from a central plate."""
import random, math, sys

CY = '#3BE8FF'
RED = '#FF3B4E'


def traces(W, H, px, py, pw, ph, n=30, seed=7):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        side = rnd.choice(['t', 'b', 'l', 'r', 'l', 'r'])
        if side in 'tb':
            x = px + rnd.uniform(0.08, 0.92) * pw
            y = py if side == 't' else py + ph
            d = (0, -1) if side == 't' else (0, 1)
        else:
            y = py + rnd.uniform(0.1, 0.9) * ph
            x = px if side == 'l' else px + pw
            d = (-1, 0) if side == 'l' else (1, 0)
        pts = [(x, y)]
        cx, cy = x, y
        dx, dy = d
        for seg in range(rnd.randint(3, 5)):
            L = rnd.uniform(30, 160)
            cx += dx * L
            cy += dy * L
            pts.append((cx, cy))
            # bend 45 degrees away from center, or back to orthogonal
            if dx == 0 or dy == 0:
                sgn = rnd.choice([-1, 1])
                if dx == 0:
                    dx, dy = sgn * 0.7071, dy * 0.7071
                else:
                    dx, dy = dx * 0.7071, sgn * 0.7071
            else:
                if rnd.random() < 0.5:
                    dx, dy = (1 if dx > 0 else -1), 0
                else:
                    dx, dy = 0, (1 if dy > 0 else -1)
        # run off-frame
        cx += dx * 900
        cy += dy * 900
        pts.append((cx, cy))
        length = sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1))
        color = RED if rnd.random() < 0.16 else CY
        w = rnd.choice([1.6, 2.2, 2.2, 3])
        nb = rnd.choice([1, 2, 3, 3, 4, 5])
        sp = rnd.choice([7, 9, 11])
        px_, py_ = (-d[1], d[0])
        for b in range(nb):
            o = (b - (nb - 1) / 2) * sp
            q = [(a + px_ * o, c + py_ * o) for a, c in pts]
            cc = color if rnd.random() > 0.12 else (RED if color == CY else CY)
            out.append((q, cc, w if b == 0 else max(1.2, w - 0.6), length, rnd.uniform(2.2, 6.0), rnd.uniform(0, 6)))
    return out


def svg(W, H, px, py, pw, ph, seed=7, uid='a', plate=True):
    tr = traces(W, H, px, py, pw, ph, seed=seed)
    rnd = random.Random(seed + 1)
    s = []
    s.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true" style="position: absolute; left: 0; top: 0">')
    s.append(f'<defs><radialGradient id="bg{uid}" cx="50%" cy="50%" r="75%"><stop offset="0" stop-color="#0C2148"></stop><stop offset="0.55" stop-color="#061230"></stop><stop offset="1" stop-color="#020611"></stop></radialGradient>'
             f'<filter id="gl{uid}" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5"></feGaussianBlur></filter>'
             f'<filter id="bk{uid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"></feGaussianBlur></filter></defs>')
    s.append(f'<rect width="{W}" height="{H}" fill="url(#bg{uid})"></rect>')
    # bokeh
    for _ in range(14):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(10, 40)
        c = RED if rnd.random() < 0.2 else CY
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{c}" opacity="{rnd.uniform(.06,.16):.2f}" filter="url(#bk{uid})"></circle>')
    far = traces(W, H, px - 120, py - 60, pw + 240, ph + 120, n=22, seed=seed + 5)
    s.append(f'<g fill="none" stroke-linecap="round" opacity="0.45" filter="url(#bk{uid})">' + ''.join(
        '<path d="M' + ' L'.join(f'{x:.0f} {y:.0f}' for x, y in p) + f'" stroke="{c}" stroke-width="{w*3:.0f}"></path>' for p, c, w, *_ in far) + '</g>')
    base, glow, flow = [], [], []
    for k, (pts, c, w, L, dur, delay) in enumerate(tr):
        dpath = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts)
        base.append(f'<path d="{dpath}" stroke="{c}" stroke-width="{w}" opacity="0.42"></path>')
        glow.append(f'<path d="{dpath}" stroke="{c}" stroke-width="{w*3:.1f}" opacity="0.4"></path>')
        seglen = rnd.uniform(70, 160)
        flow.append(f'<path class="fl{uid}" d="{dpath}" stroke="{c}" stroke-width="{w+0.6:.1f}" stroke-dasharray="{seglen:.0f} {L:.0f}" style="--L: {L+seglen:.0f}; animation-duration: {dur:.1f}s; animation-delay: -{delay:.1f}s"></path>')
        # pad at start
        x0, y0 = pts[0]
    s.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">{"".join(base)}</g>')
    s.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" filter="url(#gl{uid})">{"".join(glow)}</g>')
    s.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">{"".join(flow)}</g>')
    s.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" filter="url(#gl{uid})">{"".join(flow)}</g>')
    s.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.85">{"".join(f.replace(chr(34)+CY+chr(34), chr(34)+"#E8FDFF"+chr(34)).replace(chr(34)+RED+chr(34), chr(34)+"#FFD0D4"+chr(34)) for f in flow)}</g>')
    if plate:
        s.append(f'<radialGradient id="sh{uid}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#020611" stop-opacity="0.92"></stop><stop offset="0.6" stop-color="#020611" stop-opacity="0.7"></stop><stop offset="1" stop-color="#020611" stop-opacity="0"></stop></radialGradient>')
        s.append(f'<ellipse cx="{px+pw/2:.0f}" cy="{py+ph/2:.0f}" rx="{pw*0.62:.0f}" ry="{ph*0.62:.0f}" fill="url(#sh{uid})"></ellipse>')
    s.append('</svg>')
    css = (f'@keyframes flow{uid}{{from{{stroke-dashoffset:var(--L)}}to{{stroke-dashoffset:0}}}}'
           f'.fl{uid}{{animation-name:flow{uid};animation-timing-function:linear;animation-iteration-count:infinite;animation-direction:reverse}}')
    return '\n'.join(s), css


if __name__ == '__main__':
    W, H, px, py, pw, ph = 1200, 600, 230, 120, 740, 360
    body, css = svg(W, H, px, py, pw, ph)
    open('/home/claude/logo/bgtest.html', 'w').write(
        f'<!doctype html><html><head><meta charset="utf-8"><style>body{{margin:0}}{css}</style></head><body><div style="position:relative;width:{W}px;height:{H}px">{body}</div></body></html>')
