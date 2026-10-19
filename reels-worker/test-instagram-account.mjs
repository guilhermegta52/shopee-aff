import {test} from 'node:test';
import assert from 'node:assert/strict';
import {resolveAccount} from './instagram-account.mjs';
test('uses token user_id rather than stale configured ID and verifies publication access',async()=>{
  const requests=[];
  const account=await resolveAccount({INSTAGRAM_TOKEN:'IG-test',INSTAGRAM_ACCOUNT_ID:'wrong'},async url=>{requests.push(url);return {ok:true,json:async()=>requests.length===1?{id:'app-scope',user_id:'correct',username:'test'}:{data:[{quota_usage:1,config:{quota_total:100}}]}};});
  assert.equal(account.id,'correct');assert.equal(account.configuredIdMatches,false);assert.ok(requests[1].includes('/correct/content_publishing_limit'));
});
test('permission failure blocks before any generation or media creation',async()=>{
  await assert.rejects(resolveAccount({INSTAGRAM_TOKEN:'IG-test'},async url=>({ok:!url.includes('content_publishing_limit'),json:async()=>url.includes('content_publishing_limit')?{error:{message:'Missing permissions'}}:{user_id:'correct'}})),/Missing permissions/);
});
