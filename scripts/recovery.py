"""Export reviewed aggregate recovery data or restore it into a fresh clone.

Only allowlisted normalized financial fields are exported. Credentials and raw
provider/customer identifiers never belong in these versioned recovery files.
"""
import argparse
import json
from pathlib import Path
from build_dashboard import ROOT, LABELS, atomic, normalize

META=('period_start','period_end_exclusive','transactions_count','pages_read',
      'provider_last_refreshed_min_utc','provider_last_refreshed_max_utc')

def export():
 staged={}
 for source in LABELS:
  original=json.loads((ROOT/f'work/finance/sources/{source}.json').read_text())
  clean=normalize(source,original)
  result={k:original[k] for k in META if k in original}
  result.update(source=source,checked_at=clean['checked_at'],retrieval_complete=True,
                coverage_note=clean['coverage'],groups=clean['groups'],rows=clean['rows'])
  if source=='stripe':
   result['currency_totals']=original['currency_totals']
   result['account_metadata']={'type':original['account_metadata']['type']}
  if source=='paypal':result['totals_by_currency']=original['totals_by_currency']
  normalize(source,result)
  staged[f'sources/{source}.json']=result
 schedule=json.loads((ROOT/'work/finance/schedule.json').read_text())
 staged['schedule.json']={k:schedule[k] for k in ('active','label','timezone','hour','automation_id','first_scheduled_run_observed') if k in schedule}
 status_path=ROOT/'work/finance/refresh-status.json'
 status=json.loads(status_path.read_text()) if status_path.exists() else {}
 staged['refresh-status.json']={s:{k:v[k] for k in ('ok','attempted_at','message') if k in v} for s,v in status.items() if s in LABELS}
 for path,obj in staged.items():atomic(ROOT/'recovery'/path,obj)
 print('Exported 5 validated aggregate sources and recovery metadata; no credentials.')

def restore():
 pairs=[(ROOT/'recovery'/f'sources/{s}.json',ROOT/'work/finance'/f'sources/{s}.json') for s in LABELS]
 pairs += [(ROOT/'recovery'/name,ROOT/'work/finance'/name) for name in ('schedule.json','refresh-status.json')]
 if any(target.exists() for _,target in pairs):
  raise SystemExit('Local recovery targets already exist. Existing data was not overwritten.')
 objects=[]
 for source_path,target in pairs:
  obj=json.loads(source_path.read_text())
  if source_path.parent.name=='sources':normalize(source_path.stem,obj)
  objects.append((target,obj))
 for target,obj in objects:atomic(target,obj)
 print('Restored last-good aggregate evidence with its original dates. Credentials and scheduled jobs are not installed by this command.')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['export','restore']);args=p.parse_args()
 export() if args.mode=='export' else restore()
