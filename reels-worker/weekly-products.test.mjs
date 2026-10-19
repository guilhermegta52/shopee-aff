import {test} from 'node:test';
import assert from 'node:assert/strict';
import {observe,weeklyRanking,fetchBroadOffers} from './weekly-products.mjs';
const product=(id,more={})=>({itemId:id,title:'Oferta real '+id,price:50,rating:4.8,sales:1000,commissionPct:8,discount:20,image:'https://example.com/a.jpg',affiliateLink:'https://shopee.com.br/item',...more});
test('ranking is not dominated by commission times sales or category',()=>{
  const data=observe([], [product('tool',{title:'Ferramenta',rating:4.5,sales:100000,commissionPct:1,discount:0}),product('home',{title:'Produto para casa',rating:5,sales:10000,discount:60,commissionPct:15})],new Date('2026-10-19T12:00:00Z'));
  assert.equal(weeklyRanking(data,[],new Date('2026-10-19T13:00:00Z')).best.itemId,'home');
  assert.equal(weeklyRanking(data,['home'],new Date('2026-10-19T13:00:00Z')).best.itemId,'tool');
});
test('seven day retention, one snapshot/day, stale products and demo exclusion',()=>{
  let data=observe([{at:'2026-10-01T12:00:00Z',offers:[product('old')]}],[product('a'),product('demo',{demo:true})],new Date('2026-10-19T12:00:00Z'));
  data=observe(data,[product('b')],new Date('2026-10-19T14:00:00Z'));
  assert.equal(data.length,1); assert.deepEqual(data[0].offers.map(p=>p.itemId),['b']);
  assert.equal(weeklyRanking(data,[],new Date('2026-10-22T12:00:00Z')).best,null);
});
test('broad query has pagination and no keyword or category filter',async()=>{
  const queries=[];
  await fetchBroadOffers('id','secret',async(url,options)=>{queries.push(JSON.parse(options.body).query);return {ok:true,json:async()=>({data:{productOfferV2:{nodes:[],pageInfo:{hasNextPage:queries.length<3}}}})};});
  assert.equal(queries.length,3); assert.match(queries[2],/page: 3/); assert.ok(queries.every(q=>!q.includes('keyword')));
});
