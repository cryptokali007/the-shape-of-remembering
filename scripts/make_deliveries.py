from pathlib import Path
import json,re,subprocess,math
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'renders';FF=Path(json.loads((ROOT/'runtime.json').read_text(encoding='utf-8-sig'))['ffmpegDirectory'])/'ffmpeg.exe'
vtt=(ROOT/'captions.vtt').read_text(encoding='utf-8');cues=[]
def seconds(v):
    h,m,s=v.split(':');return int(h)*3600+int(m)*60+float(s)
for block in re.split(r'\n\s*\n',vtt):
    lines=block.strip().splitlines();k=next((i for i,l in enumerate(lines) if '-->' in l),None)
    if k is None:continue
    a,b=lines[k].split('-->');text=' '.join(lines[k+1:]).strip();cues.append((seconds(a.strip()),seconds(b.strip().split()[0]),text))
assert len(cues)>50 and all(0<=a<b<=300 for a,b,_ in cues)
def stamp(s,ass=False):
    units=round(s*(100 if ass else 1000));base=100 if ass else 1000;h,units=divmod(units,3600*base);m,units=divmod(units,60*base);s,frac=divmod(units,base)
    return f'{h}:{m:02}:{s:02}.{frac:02}' if ass else f'{h:02}:{m:02}:{s:02},{frac:03}'
(ROOT/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{text}' for i,(a,b,text) in enumerate(cues))+'\n',encoding='utf-8')
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Film,Segoe UI,34,&H00FFFFFF,&H00FFFFFF,&H90080E16,&H90080E16,0,0,0,0,100,100,0,0,3,12,0,2,190,190,105,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
ass=header+'\n'.join(f'Dialogue: 0,{stamp(a,True)},{stamp(b,True)},Film,,0,0,0,,{text.replace(chr(10),r"\N")}' for a,b,text in cues)+'\n'
(ROOT/'captions.ass').write_text(ass,encoding='utf-8')
master=R/'The-Shape-of-Remembering-4K.mp4'
jobs=[('The-Shape-of-Remembering-1080p.mp4','scale=1920:1080:flags=lanczos'),('The-Shape-of-Remembering-1080p-Captioned.mp4','scale=1920:1080:flags=lanczos,ass=captions.ass')]
for name,filter_ in jobs:
    subprocess.run([str(FF),'-y','-hide_banner','-loglevel','warning','-hwaccel','cuda','-i',str(master),'-vf',filter_,'-c:v','h264_nvenc','-preset','p6','-rc','vbr','-cq','17','-b:v','0','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(R/name)],cwd=ROOT,check=True)
    print('DELIVERED',name,flush=True)
(ROOT/'evidence'/'CAPTIONS.json').write_text(json.dumps({'cues':len(cues),'first':cues[0],'last':cues[-1],'timing':'Estimated phrase boundaries over measured utterance spans; not forced alignment','burned_style':'Segoe UI34px, boundedbox,105px bottom margin at1080p'},indent=2),encoding='utf-8')
