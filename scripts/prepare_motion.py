from pathlib import Path
import json,numpy as np
root=Path(__file__).resolve().parents[1];a=root/'assets'/'audio'
f=json.loads((a/'score-features.json').read_text(encoding='utf-8'))
out={'feature_rate':f['feature_rate_hz'],'source':'Measured original score band RMS','normalization':{}}
for key in ['low','mid','high']:
    v=np.asarray(f[key+'_rms']);n=float(np.percentile(v,95));out['normalization'][key]=n;out[key]=np.clip(v/max(n,1e-9),0,1.3).round(5).tolist()
(a/'motion-features.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8')
