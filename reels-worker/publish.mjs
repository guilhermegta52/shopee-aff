import fs from 'node:fs/promises';
import {put} from '@vercel/blob';
import {resolveAccount} from './instagram-account.mjs';
const [filename,metadata]=process.argv.slice(2);
const token=process.env.BLOB_READ_WRITE_TOKEN,igToken=process.env.INSTAGRAM_TOKEN,igId=process.env.INSTAGRAM_ACCOUNT_ID;
if(process.env.ENABLE_REAL_POSTING!=='true')throw Error('Bloqueado: publicação não autorizada');
if(!token||!igToken||!igId)throw Error('Faltam BLOB_READ_WRITE_TOKEN ou INSTAGRAM_TOKEN ou INSTAGRAM_ACCOUNT_ID');
const details=JSON.parse(await fs.readFile(metadata,'utf8'));
if(!details.affiliateLink)throw Error('Sem link de afiliado');
const account=await resolveAccount();
console.log('INSTAGRAM_ACCOUNT_OK',JSON.stringify({id:account.id,username:account.username,authType:account.authType}));
const body=await fs.readFile(filename);
const safeID=String(details.itemId).replace(/[^\w-]/g,'').slice(0,60);
const path='promo-radar/reels/'+new Date().toISOString().slice(0,10)+'-'+safeID+'.mp4';
const uploaded=await put(path,body,{access:'public',addRandomSuffix:false,contentType:'video/mp4',token});
if(!uploaded?.url?.startsWith('https://'))throw Error('Falha no armazenamento do MP4');
console.log('MEDIA_HOSTED',uploaded.url);
const base=account.base;
async function request(endpoint,data){
 const url=base+'/'+endpoint;
 const options=data?{method:'POST',body:new URLSearchParams(data)}:{};
 const resp=await fetch(url,options);const out=await resp.json();
 if(!resp.ok||out.error)throw Error('Instagram API: '+(out.error?.message||resp.status));
 return out;
}
const caption='🛍️ '+details.title+'\n💰 Preço informado: R$ '+Number(details.price).toFixed(2).replace('.',',')+'\n🔗 Link do produto na bio.'+'\n\n#Shopee #PromoRadar #Achadinhos';
const container=await request(encodeURIComponent(account.id)+'/media',{media_type:'REELS',video_url:uploaded.url,caption,share_to_feed:'true',access_token:igToken});
if(!container.id)throw Error('Instagram não criou o contêiner');
console.log('REEL_CONTAINER_CREATED',container.id);
let ready=false;
for(let i=0;i<32;i++){
 await new Promise(r=>setTimeout(r,5000));
 const status=await request(container.id+'?fields=status_code,status&access_token='+encodeURIComponent(igToken));
 if(status.status_code==='FINISHED'){ready=true;break}
 if(status.status_code==='ERROR'||status.status_code==='EXPIRED')throw Error('Instagram processou vídeo com falha: '+JSON.stringify(status.status||status.status_code));
}
if(!ready)throw Error('Tempo excedido aguardando Instagram processar Reel');
const pub=await request(encodeURIComponent(account.id)+'/media_publish',{creation_id:container.id,access_token:igToken});
if(!pub.id)throw Error('Instagram não retornou ID de publicação');
await fs.writeFile(new URL('./out/publish.json',import.meta.url),JSON.stringify({publishedId:pub.id,itemId:details.itemId,videoUrl:uploaded.url,at:new Date().toISOString()},null,2));
console.log('REEL_PUBLISHED',pub.id);