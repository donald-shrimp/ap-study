export const shuffle=(items,random)=>{const a=[...items];for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
// Largest remainder with a stable ID tie break; the frozen weights are enough
// to validate a saved session after the qualification's topics have changed.
export function weightedQuotas(weights,size){
 const rows=Object.entries(weights).map(([id,weight])=>({id,weight})),total=rows.reduce((n,r)=>n+r.weight,0);
 for(const r of rows){r.exact=size*r.weight/total;r.count=Math.floor(r.exact);}
 let left=size-rows.reduce((n,r)=>n+r.count,0);
 rows.sort((a,b)=>(b.exact-b.count)-(a.exact-a.count)||(a.id<b.id?-1:a.id>b.id?1:0));
 for(const r of rows){if(!left)break;r.count++;left--;}
 return new Map(rows.map(r=>[r.id,r.count]));
}
