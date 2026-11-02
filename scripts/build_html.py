from pathlib import Path
import json,html
root=Path(__file__).resolve().parents[1]
shots=json.loads((root/'shots.json').read_text(encoding='utf-8'))
clips=[]
for i,s in enumerate(shots):
    esc=lambda x:html.escape(x).replace('\n','<br>')
    evidence=f'<div class="evidence">{esc(s["evidence"])}</div>' if s.get('evidence') else ''
    clips.append(f'''<section id="shot-{i}" class="clip shot {s['tone']} {s['layout']}" data-start="{s['start']}" data-duration="{s['end']-s['start']}" data-track-index="1" data-track-kind="graphics"><div class="ink"><p class="chapter">{esc(s['chapter'])}</p><h2>{esc(s['title'])}</h2><p class="detail">{esc(s['detail'])}</p>{evidence}</div></section>''')
body='\n'.join(clips)
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=3840, height=2160"><title>The Shape of Remembering</title>
<script src="assets/vendor/gsap.min.js"></script>
<style>
@font-face{font-family:Manrope;src:url('assets/fonts/sans.woff2');font-weight:100 900;font-display:block}*{box-sizing:border-box}html,body{margin:0;width:3840px;height:2160px;overflow:hidden;background:#070f19}#root{position:relative;width:3840px;height:2160px;overflow:hidden}#world{position:absolute;inset:0;width:3840px;height:2160px}#editorial{position:absolute;left:0;top:0;width:1920px;height:1080px;transform:scale(2);transform-origin:top left;pointer-events:none;font-family:Manrope,sans-serif}.shot{position:absolute;inset:0;color:#f4f8fb}.ink{position:absolute;left:128px;top:174px;width:830px}.chapter{font-size:22px;font-weight:650;line-height:1.5;letter-spacing:3px;margin:0 0 30px;color:#a9ced7}h2{font-size:86px;line-height:1.08;letter-spacing:-4px;font-weight:650;margin:0 0 35px}.detail{font-size:28px;line-height:1.55;font-weight:450;max-width:760px;margin:0;color:#ced9df}.light{color:#152b3b}.light .chapter{color:#245f67}.light .detail{color:#294b59}.blue .chapter{color:#b8e9ff}.blue .detail{color:#daeaff}.copper .chapter{color:#ffd8ad}.copper .detail{color:#f1dfca}.hero .ink{top:600px;width:1040px}.hero h2{font-size:92px}.hero .detail{font-size:26px}.evidence .ink,.quote .ink{top:160px;width:1040px}.evidence h2{font-size:76px}.evidence .evidence{margin-top:35px;font-size:28px;line-height:1.65;color:#c8e1e6;border-left:3px solid #d8b486;padding-left:25px;width:810px}.quote h2{font-size:75px}.quote .evidence{font-size:34px;line-height:1.5;margin-top:42px;max-width:900px;color:#f0d8af}.blob .ink{top:150px;width:1160px}.blob h2{font-size:76px}.blob .evidence{font-size:25px;line-height:1.9;overflow-wrap:anywhere;width:1080px;border-top:1px solid #879fa5;margin-top:35px;padding-top:25px}.end .ink{top:174px;width:1250px}.end h2{font-size:104px}.end .detail{font-size:27px}.end .evidence{font-size:22px;line-height:1.7;color:#b9ccd1;margin-top:35px}.bar{position:absolute;left:0;right:0;height:42px;background:#080f16}.bar.top{top:0}.bar.bottom{bottom:0}#progress{position:absolute;left:128px;bottom:63px;height:2px;width:0;background:#c6aa82;opacity:.65}#folio{position:absolute;right:128px;bottom:60px;color:#9bb0b9;font-size:17px;letter-spacing:2px}
</style></head><body><main id="root" data-composition-id="main" data-start="0" data-duration="300" data-width="3840" data-height="2160" data-fps="30"><canvas id="world" class="clip" data-start="0" data-duration="300" data-track-index="0" data-track-kind="graphics" data-layout-allow-overlap></canvas><div id="editorial">'''+body+'''<div class="bar top"></div><div class="bar bottom"></div><div id="progress"></div><span id="folio">WALRUS / MEMORY / MOTION</span></div><audio id="film-mix" class="clip" data-start="0" data-duration="300" data-track-index="2" data-track-kind="audio" src="assets/audio/final-mix.wav" data-volume="1"></audio></main>
<script type="module">
import {initialize,draw} from './film.js';
await initialize();
const clock={t:0};const tl=gsap.timeline({paused:true});
tl.to(clock,{t:300,duration:300,ease:'none',onUpdate:()=>draw(clock.t)},0);
const shots=window.filmShots;
for(let i=0;i<shots.length;i++){const s=shots[i];const selector='#shot-'+i+' .ink';tl.fromTo(selector,{opacity:0,x:i%3===0?-35:0,y:i%3===1?25:0},{opacity:1,x:0,y:0,duration:.8,ease:'power3.out'},s.start+.45);if(i<shots.length-1)tl.to(selector,{opacity:0,duration:.35,ease:'power1.in'},s.end-.4);}
tl.to('#progress',{width:1664,duration:300,ease:'none'},0);
window.__timelines=window.__timelines||{};window.__timelines.main=tl;
window.addEventListener('hf-seek',e=>draw(e.detail.time));draw(0);
</script></body></html>'''
page=page.replace('</style>', '''.shot::before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(3,12,21,.82),rgba(3,12,21,.5) 32%,rgba(3,12,21,0) 62%)}.shot.light::before{background:linear-gradient(90deg,rgba(235,243,245,.9),rgba(235,243,245,.58) 35%,rgba(235,243,245,0) 65%)}.shot.hero::before{background:linear-gradient(90deg,rgba(3,12,21,.7),transparent 70%),linear-gradient(0deg,rgba(3,12,21,.8),transparent 75%)}.ink{z-index:1}.hero .ink{top:530px}.end::before{background:linear-gradient(90deg,rgba(3,12,21,.93),rgba(3,12,21,.7) 47%,transparent 78%)}.chapter{font-size:28px}.hero .detail,.end .detail{font-size:28px}.blob .evidence{font-size:28px}.end .evidence{font-size:28px;line-height:1.5}
</style>''')
page=page.replace('<span id="folio">WALRUS / MEMORY / MOTION</span>','')
page=page.replace('data-layout-allow-overlap></canvas>','data-layout-allow-overlap data-layout-allow-overflow></canvas>')
(root/'index.html').write_text(page,encoding='utf-8')
print('Built',len(shots),'editable shot overlays')
