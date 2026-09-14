"""Publish only validated aggregate evidence; last-good data remains on failure."""
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
ZONE=ZoneInfo('America/Chicago')
KINDS={'income','financing','deduction','repayment','excluded','review'}
LABELS={
 'stripe':('Stripe','API','Just Jarvis LLC','Charges and financing received; bank payouts are transfers.'),
 'paypal':('PayPal','API','Just Jarvis LLC · account label VS STAFFING LLC','All successful incoming payments, including general and mass payments.'),
 'skool':('Skool','Browser','3 communities','Net community payouts. Fees already withheld by Skool are not deducted again.'),
 'bill':('BILL','Browser','Payments In','Paid receipts by delivery date, including recorded cash; void payments excluded.'),
 'gusto':('Gusto','Browser','Honestly Nevermind LLC','Completed direct deposits from both DealMachine payer profiles.')}

def atomic(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp')
 fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f: json.dump(obj,f,indent=2);f.write('\n')
 os.replace(tmp,path)

def normalize(source,obj):
 assert obj.get('retrieval_complete') is True, 'Incomplete source snapshot'
 checked=obj.get('retrieved_at_utc') or obj.get('checked_at')
 assert checked and dt.datetime.fromisoformat(checked.replace('Z','+00:00')).tzinfo
 assert isinstance(obj.get('rows',obj.get('daily')),list), 'Missing source rows'
 start_date=dt.datetime.fromisoformat(obj['period_start'].replace('Z','+00:00')).astimezone(ZONE).date().isoformat()
 end_date=dt.datetime.fromisoformat(obj['period_end_exclusive'].replace('Z','+00:00')).astimezone(ZONE).date().isoformat()
 rows=[]
 for raw in obj.get('rows',obj.get('daily',[])):
  row={k:raw[k] for k in ['date','currency','kind','amount_minor','fee_minor','net_minor','count']}
  assert row['kind'] in KINDS and row['currency']=='USD', 'New currency requires unit review'
  dt.date.fromisoformat(row['date'])
  assert start_date<=row['date']<=end_date, 'Source row outside reporting period'
  for field in ['amount_minor','fee_minor','net_minor','count']:
   assert type(row[field]) is int and abs(row[field])<2**53
  assert row['count']>0 and row['amount_minor']-row['fee_minor']==row['net_minor']
  assert row['kind']!='income' or row['amount_minor']>=0
  if row['kind']=='financing' and row['amount_minor']<0:row['kind']='repayment'
  row.update(month=row['date'][:7],source=source)
  row['category']=str(raw.get('category',raw.get('code',row['kind'])))
  if raw.get('group'):row['group']=raw['group']
  rows.append(row)
 rows.sort(key=lambda r:(r['date'],r['category'],r.get('group',''),r['kind'],r['amount_minor']))
 name,mode,account,note=LABELS[source]
 return {'id':source,'name':name,'mode':mode,'account':account,'note':note,
  'checked_at':checked,'period_start':obj['period_start'],'period_end_exclusive':obj['period_end_exclusive'],
  'indexed_through':obj.get('indexed_through') or obj.get('provider_last_refreshed_min_utc') or obj.get('last_refreshed_datetime'),
  'status':'current','rows':rows,'record_count':sum(x['count'] for x in rows),
  'coverage':obj.get('coverage_note',f"{obj.get('transactions_count',0):,} records; complete pagination. Provider indexing may lag." if source=='paypal' else f"{obj.get('transactions_count',0):,} balance entries across {obj.get('pages_read',0)} pages; complete YTD retrieval."),'groups':obj.get('groups',[])}

def build():
 now=dt.datetime.now(dt.timezone.utc)
 prior=json.loads((ROOT/'dist/data.json').read_text())
 previous={x['id']:x for x in prior.get('sources',[])}
 sources=[]
 attempts_path=ROOT/'work/finance/refresh-status.json'
 attempts=json.loads(attempts_path.read_text()) if attempts_path.exists() else {}
 for key in LABELS:
  path=ROOT/f'work/finance/sources/{key}.json'
  try: s=normalize(key,json.loads(path.read_text()))
  except Exception:
   if key not in previous: raise ValueError(f'No validated snapshot for {key}') from None
   s=previous[key].copy();s['status']='stale';s['issue']='Latest collection did not validate; showing the last successful report.'
  attempt=attempts.get(key,{})
  if attempt.get('ok') is False:
   s['status']='stale';s['issue']=attempt.get('message','Refresh failed; last successful amounts retained.')
  age=(now-dt.datetime.fromisoformat(s['checked_at'].replace('Z','+00:00'))).total_seconds()
  if age>36*3600:s['status']='stale';s.setdefault('issue','This source has not refreshed within 36 hours.')
  sources.append(s)
 days=[r['date'] for s in sources for r in s['rows']]
 today=now.astimezone(ZONE).date().isoformat()
 year=today[:4]
 start=min([year+'-01-01']+[d for d in days if d>=year+'-01-01'])
 schedule_path=ROOT/'work/finance/schedule.json'
 schedule=json.loads(schedule_path.read_text()) if schedule_path.exists() else {'active':False,'label':'Daily refresh setup in progress'}
 result={'schema_version':2,'prepared_at':now.isoformat(),'timezone':'America/Chicago','currency':'USD',
  'period_start':start,'period_end':today,'sources':sources,'schedule':schedule,
  'basis_note':'Payments and financing received, plus net Skool payouts and completed BILL/Gusto receipts. Bank transfers are not counted a second time. This is incoming activity, not a bank balance or profit.'}
 atomic(ROOT/'dist/data.json',result)
 atomic(ROOT/'outputs/revenue-snapshot.json',result)
 print(json.dumps({'sources':len(sources),'daily_buckets':sum(len(s['rows']) for s in sources),'stale':[s['id'] for s in sources if s['status']=='stale']}))

if __name__=='__main__':build()
