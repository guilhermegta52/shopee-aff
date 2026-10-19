import fs from 'node:fs/promises';
import {savePublishedProduct} from './storefront.mjs';
import {resolveAccount} from './instagram-account.mjs';
const [metadata]=process.argv.slice(2);
if(process.env.ENABLE_REAL_POSTING!=='true')throw Error('Publicação não autorizada');
const p=JSON.parse(await fs.readFile(metadata,'utf8'));
if(!p.image||!p.affiliateLink||!p.itemId)throw Error('Produto incompleto');
const account=await resolveAccount();
const app=(process.env.PROMO_RADAR_API||'https://shopee-afiliado-auto.vercel.app').replace(/\/$/,'');
const image=app+'/api/instagram/media?'+new URLSearchParams({src:p.image,v:'product-photo-2'});
// Check the very same corrected photo URL Instagram will fetch.
const check=await fetch(image,{signal:AbortSignal.timeout(60000)});
if(!check.ok||!check.headers.get('content-type')?.startsWith('image/'))throw Error('Foto do produto indisponível');
const caption='🛍️ '+p.title+'\n💰 Preço informado: R$ '+Number(p.price).toFixed(2).replace('.',',')+'\n🔗 Link do produto na bio.\nPreço e disponibilidade podem mudar.\n#Shopee #PromoRadar #Achadinhos';
async function request(path,data){
 const url=account.base+'/'+path;
 const r=await fetch(url,data?{method:'POST',body:new URLSearchParams({...data,access_token:process.env.INSTAGRAM_TOKEN})}:{signal:AbortSignal.timeout(30000)});
 const out=await r.json();if(!r.ok||out.error)throw Error('Instagram: '+(out.error?.message||r.status));return out;
}
const created=await request(account.id+'/media',{image_url:image,caption});
if(!created.id)throw Error('Instagram não retornou contêiner');
let ready=false;
for(let i=0;i<30;i++){
 const q=new URLSearchParams({fields:'status_code',access_token:process.env.INSTAGRAM_TOKEN});
 const status=await request(created.id+'?'+q);
 if(status.status_code==='FINISHED'){ready=true;break;}
 if(['ERROR','EXPIRED'].includes(status.status_code))throw Error('Falha no processamento da foto');
 await new Promise(r=>setTimeout(r,3000));
}
if(!ready)throw Error('Foto não ficou pronta; publicação não repetida automaticamente');
const published=await request(account.id+'/media_publish',{creation_id:created.id});
if(!published.id)throw Error('Publicação sem confirmação');
await fs.writeFile(new URL('./out/publish.json',import.meta.url),JSON.stringify({publishedId:published.id,itemId:p.itemId,kind:'photo',at:new Date().toISOString()},null,2));
console.log('PHOTO_PUBLISHED',published.id,p.itemId);

await savePublishedProduct(p,{publishedId:published.id,kind:'photo'});
console.log('STOREFRONT_UPDATED',p.itemId);
