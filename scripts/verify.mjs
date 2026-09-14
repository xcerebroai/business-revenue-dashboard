import assert from 'node:assert/strict';
import fs from 'node:fs';
import {summarize,filterRows,monthList,sourceStatus} from '../dist/model.mjs';
const data=JSON.parse(fs.readFileSync(new URL('../dist/data.json',import.meta.url)));
assert.equal(data.schema_version,2);
assert.deepEqual(data.sources.map(s=>s.id),['stripe','paypal','skool','bill','gusto']);
const all=data.sources.flatMap(s=>s.rows),months=monthList(data.period_start.slice(0,7),data.period_end.slice(0,7));
const totals=summarize(all);
for(const start of months)for(const end of months.filter(m=>m>=start)){
 const rows=filterRows(all,start+'-01',end+'-31','USD');
 const result=summarize(rows);
 const individual=data.sources.map(s=>summarize(filterRows(s.rows,start+'-01',end+'-31','USD')));
 for(const field of Object.keys(result))assert.equal(result[field],individual.reduce((n,s)=>n+s[field],0));
}
for(const s of data.sources){
 const original=JSON.parse(fs.readFileSync(new URL(`../work/finance/sources/${s.id}.json`,import.meta.url)));
 const rows=original.rows||original.daily;
 assert.equal(s.rows.reduce((n,r)=>n+r.count,0),rows.reduce((n,r)=>n+r.count,0));
 for(const field of ['amount_minor','fee_minor','net_minor'])assert.equal(s.rows.reduce((n,r)=>n+r[field],0),rows.reduce((n,r)=>n+r[field],0));
 if(s.id==='stripe'){const t=original.currency_totals.USD;assert.equal(summarize(s.rows).incoming,t.incoming_minor);assert.equal(summarize(s.rows).net,t.after_deductions_minor);assert.equal(original.account_metadata.type,'standard');}
 if(s.id==='paypal'){const t=original.totals_by_currency.USD;assert.equal(summarize(s.rows).incoming,t.cash_in_minor);assert.equal(summarize(s.rows).net,t.net_cash_activity_minor);assert.equal(s.indexed_through,original.provider_last_refreshed_min_utc);}
}
const sample=(kind,amount,fee=0)=>({kind,amount_minor:amount,fee_minor:fee,net_minor:amount-fee,count:1,date:'2026-01-01',currency:'USD'});
assert.equal(summarize([sample('income',10000,300),sample('financing',20000),sample('repayment',-4000),sample('deduction',-1000),sample('deduction',200),sample('excluded',700000)]).net,24900);
assert.equal(summarize([sample('repayment',200)]).incoming,0);
assert.equal(summarize([sample('review',500)]).incoming,0);
assert.equal(summarize([]).incoming,0);
assert.equal(sourceStatus({status:'current',checked_at:'2026-01-01T00:00:00Z'},Date.parse('2026-01-03T00:00:00Z')),'stale');
assert.equal(sourceStatus({status:'stale',checked_at:data.prepared_at}),'stale');
assert.deepEqual(monthList('2026-12','2027-02'),['2026-12','2027-01','2027-02']);
assert.throws(()=>summarize([{...sample('income',1),net_minor:2}]));
const privateData=JSON.stringify(data);
assert(!/rk_live_|sk_live_|Bearer |PAYPAL_CLIENT_SECRET|transaction_id|bank_account|@/.test(privateData));
assert(all.every(r=>Number.isSafeInteger(r.amount_minor)&&r.currency==='USD'));
console.log(JSON.stringify({passed:true,sources:5,monthRanges:months.length*(months.length+1)/2,incoming:totals.incoming,financing:totals.financing,afterDeductions:totals.net,sourceTotals:Object.fromEntries(data.sources.map(s=>[s.id,summarize(s.rows).incoming]))}));
