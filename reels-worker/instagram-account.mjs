import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
export async function resolveAccount(env=process.env,fetcher=fetch){
  const token=env.INSTAGRAM_TOKEN;
  if(!token)throw Error('INSTAGRAM_TOKEN ausente');
  const facebook=env.INSTAGRAM_AUTH_TYPE==='facebook'||token.startsWith('EAA');
  const host=facebook?'https://graph.facebook.com':'https://graph.instagram.com';
  const version=env.IG_GRAPH_VERSION||'v24.0';
  const base=host+'/'+version;
  async function get(path,fields){
    const q=new URLSearchParams({access_token:token,...(fields?{fields}:{})});
    const response=await fetcher(base+'/'+path+'?'+q,{signal:AbortSignal.timeout(30000)});
    const data=await response.json();
    if(!response.ok||data.error)throw Error('Instagram: '+(data.error?.message||response.status));
    return data;
  }
  let account;
  if(facebook){
    // Facebook Login uses the Instagram business account, not a Page or App ID.
    const pages=await get('me/accounts','instagram_business_account{id,username}');
    const accounts=(pages.data||[]).map(p=>p.instagram_business_account).filter(Boolean);
    account=accounts.find(a=>String(a.id)===String(env.INSTAGRAM_ACCOUNT_ID));
    if(!account&&accounts.length===1)account=accounts[0];
    if(!account)throw Error('Nenhuma conta profissional única acessível pelo Facebook Login; reconecte a conta correta');
  }else{
    const me=await get('me','id,user_id,username');
    const id=me.user_id||me.id;
    if(!id)throw Error('O token não identificou uma conta Instagram');
    account={id:String(id),username:me.username||''};
  }
  // Verify publishing access BEFORE generating or uploading a new paid video.
  const quota=await get(encodeURIComponent(account.id)+'/content_publishing_limit','quota_usage,config');
  const limits=quota.data||[];
  if(!Array.isArray(limits)||!limits.length)throw Error('Instagram não confirmou acesso à publicação');
  for(const limit of limits){
    if(Number.isFinite(limit.config?.quota_total)&&Number(limit.quota_usage)>=limit.config.quota_total)throw Error('Limite de publicação do Instagram atingido');
  }
  return {...account,base,configuredIdMatches:String(account.id)===String(env.INSTAGRAM_ACCOUNT_ID),authType:facebook?'facebook':'instagram'};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  resolveAccount().then(a=>console.log('INSTAGRAM_PREFLIGHT_OK',JSON.stringify(a))).catch(e=>{console.error(e.message);process.exitCode=1;});
}
