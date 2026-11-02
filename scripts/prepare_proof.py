from pathlib import Path
import json,shutil,subprocess
root=Path(__file__).resolve().parents[1];proof=root/'.runtime'/'proof';proof.mkdir(parents=True,exist_ok=True)
for sub in ['assets/vendor','assets/fonts','assets/images','assets/audio','scripts','renders']:(proof/sub).mkdir(parents=True,exist_ok=True)
for sub in ['vendor','fonts','images']:
    for file in (root/'assets'/sub).iterdir():
        if file.is_file():shutil.copy2(file,proof/'assets'/sub/file.name)
for file in ['film.js','shots.json','runtime.json']:shutil.copy2(root/file,proof/file)
shutil.copy2(root/'scripts'/'run.mjs',proof/'scripts'/'run.mjs')
shutil.copy2(root/'assets'/'audio'/'motion-features.json',proof/'assets'/'audio'/'motion-features.json')
ff=Path(json.loads((root/'runtime.json').read_text(encoding='utf-8-sig'))['ffmpegDirectory'])/'ffmpeg.exe'
subprocess.run([str(ff),'-v','error','-y','-ss','275','-i',str(root/'assets'/'audio'/'final-mix.wav'),'-t','8','-c:a','pcm_s24le',str(proof/'assets'/'audio'/'proof.wav')],check=True)
page='''<!doctype html><html><head><meta charset="utf-8"><script src="assets/vendor/gsap.min.js"></script><style>@font-face{font-family:Local;src:url('assets/fonts/sans.woff2')}html,body{margin:0;width:3840px;height:2160px;overflow:hidden;background:#07121d}#root,#world{position:absolute;inset:0;width:3840px;height:2160px}h1{position:absolute;left:256px;top:280px;font:160px Local;color:#fff;width:1900px;text-shadow:0 3px 30px #000}p{position:absolute;left:256px;top:550px;font:60px Local;color:#dae8ed}</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="8" data-width="3840" data-height="2160" data-fps="30"><canvas id="world" data-layout-allow-overflow></canvas><h1>The Shape of Remembering</h1><p>Actual 4K encode proof / local Three.js + original soundtrack</p><audio id="proof-audio" class="clip" data-start="0" data-duration="8" data-track-index="1" src="assets/audio/proof.wav"></audio></div><script type="module">import{initialize,draw}from'./film.js';await initialize();const c={t:0};const tl=gsap.timeline({paused:true});tl.to(c,{t:8,duration:8,ease:'none',onUpdate:()=>draw(275+c.t)},0);window.__timelines=window.__timelines||{};window.__timelines.main=tl;window.addEventListener('hf-seek',e=>draw(275+e.detail.time));draw(275);</script></body></html>'''
(proof/'index.html').write_text(page,encoding='utf-8');print(proof)
