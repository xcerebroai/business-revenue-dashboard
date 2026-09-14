"""Import a complete, sanitized browser report after visible pagination checks.

Input JSON: source, checked_at, period_start/end_exclusive, retrieval_complete,
coverage_note, groups, rows (date/currency/kind/category/count/amount/fee/net_minor).
No credentials, identifiers or customer text belong in this input.
"""
import argparse
import json
from pathlib import Path
from build_dashboard import ROOT, atomic, normalize
p=argparse.ArgumentParser();p.add_argument('input',type=Path);args=p.parse_args()
obj=json.loads(args.input.read_text());source=obj['source']
assert source in {'skool','bill','gusto'}
normalize(source,obj)
assert obj['period_start'][:4]==obj['period_end_exclusive'][:4], 'Import one calendar year at a time'
atomic(ROOT/f'work/finance/sources/{source}.json',obj)
status_path=ROOT/'work/finance/refresh-status.json'
status=json.loads(status_path.read_text()) if status_path.exists() else {}
status[source]={'ok':True,'attempted_at':obj['checked_at']}
atomic(status_path,status)
print(json.dumps({'source':source,'buckets':len(obj['rows']),'imported':True}))
