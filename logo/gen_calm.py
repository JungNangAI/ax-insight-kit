import random, math, importlib.util
spec=importlib.util.spec_from_file_location('g','/home/claude/logo/gen_bg.py'); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
CY='#3BE8FF'
def svg(W,H,px,py,pw,ph,seed=7,uid='a'):
    rnd=random.Random(seed)
    tr=[t for t in g.traces(W,H,px,py,pw,ph,n=16,seed=seed)]
    # keep at most 2 lines per bundle-ish, cyan only
    tr=tr[::2]
    s=[f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true" style="position: absolute; left: 0; top: 0">',
       f'<defs><radialGradient id="bg{uid}" cx="50%" cy="50%" r="80%"><stop offset="0" stop-color="#10275E"></stop><stop offset="0.6" stop-color="#0B1A4A"></stop><stop offset="1" stop-color="#07123A"></stop></radialGradient>'
       f'<radialGradient id="bl{uid}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#3BE8FF" stop-opacity="0.22"></stop><stop offset="0.5" stop-color="#3D7BFF" stop-opacity="0.10"></stop><stop offset="1" stop-color="#3D7BFF" stop-opacity="0"></stop></radialGradient>'
       f'<radialGradient id="mk{uid}" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#000"></stop><stop offset="0.55" stop-color="#000"></stop><stop offset="1" stop-color="#fff"></stop></radialGradient>'
       f'<mask id="m{uid}"><rect width="{W}" height="{H}" fill="url(#mk{uid})"></rect></mask>'
       f'<filter id="gl{uid}" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"></feGaussianBlur></filter></defs>',
       f'<rect width="{W}" height="{H}" fill="url(#bg{uid})"></rect>',
       f'<ellipse cx="{px+pw/2:.0f}" cy="{py+ph/2:.0f}" rx="{pw*0.75:.0f}" ry="{ph*0.8:.0f}" fill="url(#bl{uid})"></ellipse>']
    base=[];flow=[]
    for k,(pts,c,w,L,dur,delay) in enumerate(tr):
        d='M'+' L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)
        base.append(f'<path d="{d}" stroke="{CY}" stroke-width="1.6" opacity="0.16"></path>')
        if k%4==0:
            sl=rnd.uniform(80,140)
            flow.append(f'<path class="fl{uid}" d="{d}" stroke="{CY}" stroke-width="2.2" stroke-dasharray="{sl:.0f} {L:.0f}" style="--L: {L+sl:.0f}; animation-duration: {dur+3:.1f}s; animation-delay: -{delay:.1f}s"></path>')
    s.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round" mask="url(#m{uid})">{"".join(base)}<g filter="url(#gl{uid})" opacity="0.8">{"".join(flow)}</g>{"".join(flow)}</g>')
    s.append('</svg>')
    css=(f'@keyframes flow{uid}{{from{{stroke-dashoffset:var(--L)}}to{{stroke-dashoffset:0}}}}'
         f'.fl{uid}{{animation-name:flow{uid};animation-timing-function:linear;animation-iteration-count:infinite;animation-direction:reverse}}')
    return '\n'.join(s),css
