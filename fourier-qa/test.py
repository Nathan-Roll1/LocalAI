import json
import re
import time
import os
from pathlib import Path
import requests
base='http://127.0.0.1:8080'
def post(path,**kwargs):
    r=requests.post(base+path,**kwargs)
    print(path,r.status_code,r.text[:650],flush=True)
    r.raise_for_status()
    return r.json()
job=post('/models/apply',json={'id':'oruk@oruk-fourier-2b'},timeout=50)['uuid']
for i in range(240):
    status=requests.get(base+'/models/jobs/'+job,timeout=15).json()
    if status.get('error'): raise RuntimeError(status)
    if status.get('processed'): break
    time.sleep(2)
else: raise RuntimeError(status)
models=requests.get(base+'/v1/models', timeout=30).json()['data']
assert any(m['id']=='oruk-fourier-2b' for m in models), models
print('Named install complete',status.get('message'),flush=True)
outputs={}
for filename,kind,match in [('jfk.wav','audio/wav','ask not what your country can do for you'),('sample_10s.wav','audio/wav','librivox')]:
    with open(filename,'rb') as audio:
        r=post('/v1/audio/transcriptions',files={'file':(filename,audio,kind)},data={'model':'oruk-fourier-2b','response_format':'json','language':'en'},timeout=220)
    text=r['text']
    compare=re.sub(r'[^a-z]','',text.lower())
    assert re.sub(r'[^a-z]','',match) in compare,text
    outputs[filename]=text
Path('result.json').write_text(json.dumps({'LocalAI':'v5.0.1','stock_cpu_image':'quay.io/go-skynet/local-ai-backends@sha256:0ae184f09dfa0c76c509e39800121bef4d046c44a3e5c3b393b3483e9ef6d57e','native_files_revision':'8c2a8871f1304aa2f634da4fb95e24438c4945b9','gallery_id':'oruk@oruk-fourier-2b','downloaded_files':{p.name:p.stat().st_size for p in Path('models/Oruk-Fourier-2B').glob('*') if p.is_file()},'backend_install':'local-ai backends install <pinned OCI image> cpu-audio-cpp audio-cpp','http':'POST /v1/audio/transcriptions, multipart PCM WAV, loopback','transcripts':outputs,'run':'https://github.com/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID']},indent=2)+'\n')
