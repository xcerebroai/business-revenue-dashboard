export const paymentCategories=new Set(['charge','refund','dispute','dispute_reversal','fee']);
export function summarize(rows){
 if(rows===null)return null;
 const r={gross:0,refunds:0,disputes:0,reversals:0,processing:0,otherFees:0,fees:0,net:0,count:0};
 for(const b of rows){const c=b.category;
  if(c==='charge'){r.gross+=b.amount_minor;r.count+=b.count;r.processing+=b.fee_minor;}
  if(c==='refund')r.refunds-=b.amount_minor;
  if(c==='dispute')r.disputes-=b.amount_minor;
  if(c==='dispute_reversal')r.reversals+=b.amount_minor;
  if(paymentCategories.has(c)){r.net+=b.net_minor;if(c==='fee')r.otherFees-=b.net_minor;else if(c!=='charge')r.otherFees+=b.fee_minor;}
 }
 r.fees=r.processing+r.otherFees;
 if(r.gross-r.refunds-r.disputes+r.reversals-r.fees!==r.net)throw Error('Reconciliation failed');
 return r;
}
export function filterRows(rows,start,end,currency){return rows===null?null:rows.filter(r=>r.month>=start&&r.month<=end&&r.currency===currency);}
export function monthList(start,end){const out=[];let [y,m]=start.split('-').map(Number);while(`${y}-${String(m).padStart(2,'0')}`<=end){out.push(`${y}-${String(m).padStart(2,'0')}`);if(++m>12){m=1;y++;}}return out;}
