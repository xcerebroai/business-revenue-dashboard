export const includedKinds=new Set(['income','financing','deduction','repayment']);
export function summarize(rows){
 const r={income:0,financing:0,incoming:0,fees:0,adjustments:0,repayments:0,afterDeductions:0,net:0,count:0,review:0};
 for(const b of rows){
  if(!Number.isSafeInteger(b.amount_minor)||!Number.isSafeInteger(b.fee_minor)||b.amount_minor-b.fee_minor!==b.net_minor)throw Error('Invalid source arithmetic');
  if(b.kind==='review'){r.review+=Math.max(0,b.amount_minor);continue;}
  if(!includedKinds.has(b.kind))continue;
  r.net+=b.net_minor;
  if(b.kind==='income'||b.kind==='financing'){r[b.kind]+=b.amount_minor;r.fees+=b.fee_minor;r.count+=b.count;}
  if(b.kind==='deduction')r.adjustments-=b.net_minor;
  if(b.kind==='repayment')r.repayments-=b.net_minor;
 }
 r.incoming=r.income+r.financing;
 r.afterDeductions=r.incoming-r.fees-r.adjustments;
 if(r.afterDeductions-r.repayments!==r.net)throw Error('Cash-in reconciliation failed');
 return r;
}
export function filterRows(rows,start,end,currency){return rows.filter(r=>r.date>=start&&r.date<=end&&r.currency===currency);}
export function monthList(start,end){const out=[];let [y,m]=start.split('-').map(Number);while(`${y}-${String(m).padStart(2,'0')}`<=end){out.push(`${y}-${String(m).padStart(2,'0')}`);if(++m>12){m=1;y++;}}return out;}
export function sourceStatus(source,now=Date.now()){return source.status==='stale'||now-Date.parse(source.checked_at)>36*3600000?'stale':'current';}
