import {put,list} from '@vercel/blob';
const PREFIX='published-products/';
export function publicProduct(p,publication={}){
 const itemId=String(p.itemId||'');
 if(!/^\d+$/.test(itemId)||!p.title||!p.image||!p.affiliateLink||!(Number(p.price)>0))throw Error('Produto publicado incompleto para a vitrine');
 for(const value of [p.image,p.affiliateLink])if(new URL(value).protocol!=='https:')throw Error('Link não seguro');
 return {itemId,title:String(p.title).slice(0,250),price:Number(p.price),image:p.image,affiliateLink:p.affiliateLink,
  publishedAt:publication.at||new Date().toISOString(),instagramId:String(publication.publishedId||publication.mediaId||''),kind:publication.kind||'post'};
}
export async function savePublishedProduct(p,publication={}){
 const record=publicProduct(p,publication);
 await put(PREFIX+record.itemId+'.json',JSON.stringify(record),{access:'public',allowOverwrite:true,addRandomSuffix:false,cacheControlMaxAge:60,contentType:'application/json'});
 return record;
}
export async function publishedProducts(){
 const found=await list({prefix:PREFIX,limit:1000});
 const records=await Promise.all(found.blobs.map(async b=>{
  const r=await fetch(b.url+'?t='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(10000)});
  if(!r.ok)throw Error('Vitrine temporariamente indisponível');
  return r.json();
 }));
 return records.sort((a,b)=>String(b.publishedAt).localeCompare(String(a.publishedAt)));
}
