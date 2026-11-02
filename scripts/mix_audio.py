from pathlib import Path
import json,re,subprocess,hashlib
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1];A=ROOT/'assets'/'audio';SR=48000;N=300*SR
FF=Path(json.loads((ROOT/'runtime.json').read_text(encoding='utf-8-sig'))['ffmpegDirectory'])/'ffmpeg.exe'
score,sr=sf.read(A/'score.wav',always_2d=True,dtype='float64');assert sr==SR and score.shape==(N,2)
manifest=json.loads((A/'voice-manifest.json').read_text(encoding='utf-8'))
voice=np.zeros(N,dtype=np.float64);duck=np.ones(N,dtype=np.float64)
for item in manifest['clips']:
    file=A/item['file'];p=subprocess.run([str(FF),'-v','error','-i',str(file),'-af','aresample=48000:resampler=soxr','-ar','48000','-ac','1','-f','f32le','pipe:1'],capture_output=True,check=True)
    clip=np.frombuffer(p.stdout,dtype='<f4').astype(np.float64)
    rms=float(np.sqrt(np.mean(clip**2)));clip*=min(10**(-20/20)/max(rms,1e-9),.80/max(np.max(np.abs(clip)),1e-9))
    at=round(item['start_seconds']*SR);end=at+len(clip);assert end<N
    voice[at:end]+=clip
    lo=max(0,at-round(.35*SR));hi=min(N,end+round(.65*SR));tt=np.arange(lo,hi)/SR
    attack=np.clip((tt-(at/SR-.35))/.35,0,1);release=np.clip((end/SR+.65-tt)/.65,0,1)
    shape=np.minimum(attack*attack*(3-2*attack),release*release*(3-2*release));duck[lo:hi]=np.minimum(duck[lo:hi],1-.79*shape)
sf.write(A/'narration.wav',voice,SR,subtype='PCM_24')
raw=score*(.72*duck[:,None])+voice[:,None];sf.write(A/'mix-raw.wav',raw,SR,subtype='FLOAT')
cmd=[str(FF),'-hide_banner','-i',str(A/'mix-raw.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-']
p=subprocess.run(cmd,capture_output=True,text=True,check=True);m=json.loads(re.findall(r'\{[^{}]+\}',p.stderr)[-1])
f=f"loudnorm=I=-16:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json"
p=subprocess.run([str(FF),'-y','-hide_banner','-i',str(A/'mix-raw.wav'),'-af',f,'-ar',str(SR),'-c:a','pcm_s24le',str(A/'final-mix.wav')],capture_output=True,text=True,check=True)
final,sr=sf.read(A/'final-mix.wav',always_2d=True);assert final.shape==(N,2) and np.isfinite(final).all() and np.max(np.abs(final))<.99
report={'duration':300,'sample_rate':sr,'channels':2,'voice_clips':len(manifest['clips']),'voice_end':max(c['end_seconds'] for c in manifest['clips']),'first_pass':m,'final_pass':json.loads(re.findall(r'\{[^{}]+\}',p.stderr)[-1]),'peak_dbfs':float(20*np.log10(np.max(np.abs(final)))),'ducking':'smooth0.35s attack/0.65s release,21percent music during voice','narration_resampling':'FFmpeg soxr24k to48k','sha256':hashlib.sha256((A/'final-mix.wav').read_bytes()).hexdigest()}
(ROOT/'evidence'/'MIX_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
