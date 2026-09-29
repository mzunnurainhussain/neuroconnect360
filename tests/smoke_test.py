import json, subprocess, time, urllib.request, http.cookiejar
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
subprocess.run(['python','-m','app.seed'],cwd=ROOT,check=True)
p=subprocess.Popen(['uvicorn','app.main:app','--host','127.0.0.1','--port','8765'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    time.sleep(1.2)
    health=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/health'))
    assert health['status']=='ok'
    resources=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/resources?language=en'))
    assert len(resources)>=1
    professionals=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/professionals'))
    assert len(professionals)>=1
    print('SMOKE TEST PASSED:', {'health':health['status'],'resources':len(resources),'professionals':len(professionals)})
finally:
    p.terminate(); p.wait(timeout=5)
