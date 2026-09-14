"""Record a source refresh failure without touching its last-good amounts."""
import argparse,json,datetime as dt
from build_dashboard import ROOT,atomic
p=argparse.ArgumentParser();p.add_argument('source',choices=['stripe','paypal','skool','bill','gusto']);p.add_argument('--message',default='Browser reporting needs sign-in or a page check; last successful amounts retained.');args=p.parse_args()
path=ROOT/'work/finance/refresh-status.json';obj=json.loads(path.read_text()) if path.exists() else {}
obj[args.source]={'ok':False,'attempted_at':dt.datetime.now(dt.timezone.utc).isoformat(),'message':args.message};atomic(path,obj)
