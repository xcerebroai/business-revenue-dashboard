"""Refresh API sources independently; preserve each last-good snapshot on failure."""
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
from build_dashboard import atomic, normalize
ROOT=Path(__file__).resolve().parents[1]
def collect(source,cutoff):
 target=ROOT/f'work/finance/sources/{source}.json'
 candidate=target.with_suffix('.candidate.json')
 result=subprocess.run([sys.executable,str(ROOT/f'scripts/collect_{source}.py'),'--cutoff',cutoff,'--output',str(candidate)],capture_output=True,text=True)
 try:
  if result.returncode:raise ValueError('collector failed')
  obj=json.loads(candidate.read_text());normalize(source,obj)
  os.replace(candidate,target)
  return source,{'ok':True,'attempted_at':cutoff}
 except Exception:
  candidate.unlink(missing_ok=True)
  return source,{'ok':False,'attempted_at':cutoff,'message':'API refresh failed. Last successful report retained; reporting access needs a check.'}
def main():
 cutoff=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
 status_path=ROOT/'work/finance/refresh-status.json'
 status=json.loads(status_path.read_text()) if status_path.exists() else {}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for key,result in pool.map(lambda s:collect(s,cutoff),['stripe','paypal']):status[key]=result
 atomic(status_path,status)
 print(json.dumps({k:status[k] for k in ['stripe','paypal']}))
 return 0 if all(status[k]['ok'] for k in ['stripe','paypal']) else 1
if __name__=='__main__':raise SystemExit(main())
