import fs from 'node:fs/promises';
import {savePublishedProduct} from './storefront.mjs';
import {resolveAccount} from './instagram-account.mjs';
const [metadata]=process.argv.slice(2);
if(process.env.ENABLE_REAL_POSTING!=='true')throw Error('Publicação não autorizada');
const p=JSON.parse(await fs.readFile(metadata,'utf8'));
if(!p.image||!p.affiliateLink||!p.itemId)throw Error('Produto incompleto');
const app=(process.env.PROMO_RADAR_API||'https://shopee-afiliado-auto.vercel.app').replace(/\/$/,'');
let images=[];
try{
 const url=app+'/api/weekly-product-media?'+new URLSearchParams({itemId:String(p.itemId)});
 const response=await fetch(url,{signal:AbortSignal.timeout(45000)});
 const media=await response.json();
 const gallery=[...new Set((Array.isArray(media.images)?media.images:[]).filter(x=>typeof x==='string'&&/^https:\/\//i.test(x)))].slice(0,5);
 if(response.ok&&media.ok&&media.hasFivePhotos&&gallery.length===5)images=gallery;
 else console.log('PRODUCT_GALLERY_NOT_AVAILABLE',p.itemId,Number(media.photoCount)||gallery.length,'using one verified catalog photo');
}catch(error){console.log('PRODUCT_GALLERY_LOOKUP_FAILED',p.itemId,String(error.message||error).slice(0,160),'using one catalog photo');}
if(images.length!==5)images=[p.image];
const account=await resolveAccount();
const imageUrls=images.map(src=>app+'/api/instagram/media?'+new URLSearchParams({src,v:'product-photo-2'}));
for(const image of imageUrls){
 const check=await fetch(image,{signal:AbortSignal.timeout(60000)});
 if(!check.ok||!check.headers.get('content-type')?.startsWith('image/'))throw Error('Uma foto do produto está indisponível');
}
const theme=p.niche?'🎯 Tema: '+String(p.niche).slice(0,60)+'\n':'';
const caption='🛍️ '+p.title+'\n'+theme+'💰 Preço informado: R$ '+Number(p.price).toFixed(2).replace('.',',')+'\n🔗 Link do produto na bio.\nPreço e disponibilidade podem mudar.\n#Shopee #PromoRadar #Achadinhos';
async function request(path,data){
 const url=account.base+'/'+path;
 const r=await fetch(url,data?{method:'POST',body:new URLSearchParams({...data,access_token:process.env.INSTAGRAM_TOKEN})}:{signal:AbortSignal.timeout(30000)});
 const out=await r.json();if(!r.ok||out.error)throw Error('Instagram: '+(out.error?.message||r.status));return out;
}
async function waitReady(id,label){
 for(let i=0;i<30;i++){
  const q=new URLSearchParams({fields:'status_code',access_token:process.env.INSTAGRAM_TOKEN});
  const status=await request(id+'?'+q);
  if(status.status_code==='FINISHED')return;
  if(['ERROR','EXPIRED'].includes(status.status_code))throw Error('Falha no processamento de '+label);
  await new Promise(r=>setTimeout(r,3000));
 }
 throw Error(label+' não ficou pronto; publicação não repetida automaticamente');
}
let created;
if(images.length===5){
 const children=[];
 for(const image of imageUrls){
  const child=await request(account.id+'/media',{image_url:image,is_carousel_item:'true'});
  if(!child.id)throw Error('Instagram não retornou contêiner de foto');
  await waitReady(child.id,'uma foto do carrossel');children.push(child.id);
 }
 created=await request(account.id+'/media',{media_type:'CAROUSEL',children:children.join(','),caption});
 if(!created.id)throw Error('Instagram não criou o carrossel');
}else{
 created=await request(account.id+'/media',{image_url:imageUrls[0],caption});
 if(!created.id)throw Error('Instagram não retornou contêiner de foto');
}
await waitReady(created.id,images.length===5?'o carrossel':'a foto');
const published=await request(account.id+'/media_publish',{creation_id:created.id});
if(!published.id)throw Error('Publicação sem confirmação');
const kind=images.length===5?'carousel':'photo';
const receipt={publishedId:published.id,itemId:p.itemId,kind,photos:images.length,at:new Date().toISOString()};
const receiptPath=new URL('./out/publish.json',import.meta.url);
await fs.mkdir(new URL('./out/',import.meta.url),{recursive:true});
await fs.writeFile(receiptPath,JSON.stringify(receipt,null,2));
console.log(images.length===5?'INSTAGRAM_CAROUSEL_PUBLISHED':'PHOTO_PUBLISHED',published.id,p.itemId,images.length);
if(images.length===5){
 if(process.env.CRON_SECRET){
  try{
   const response=await fetch(app+'/api/tiktok/automation/photo',{method:'POST',headers:{Authorization:'Bearer '+process.env.CRON_SECRET,'Content-Type':'application/json'},body:JSON.stringify({itemId:String(p.itemId)}),signal:AbortSignal.timeout(40000)});
   const result=await response.json();
   if(!response.ok||!result.ok)throw Error(result.error||'TikTok HTTP '+response.status);
   receipt.tiktok={status:result.status,publishId:result.publishId,photos:result.photoCount,draft:true};
   console.log('TIKTOK_PHOTO_DRAFT_QUEUED',result.publishId,result.photoCount);
  }catch(error){receipt.tiktok={status:'error',error:String(error.message||error).slice(0,250)};console.error('TIKTOK_DRAFT_FAILED',receipt.tiktok.error);}
 }else{
  receipt.tiktok={status:'not_configured',error:'CRON_SECRET ausente no GitHub Actions'};
  console.error('TIKTOK_DRAFT_SKIPPED: CRON_SECRET não configurado');
 }
}else receipt.tiktok={status:'skipped_insufficient_gallery',photos:images.length};
await fs.writeFile(receiptPath,JSON.stringify(receipt,null,2));
await savePublishedProduct(p,{publishedId:published.id,kind});
console.log('STOREFRONT_UPDATED',p.itemId);
