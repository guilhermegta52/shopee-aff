import crypto from 'node:crypto';

const DAY = 86400000;
export function offerScore(p) {
  return 40 * Math.min(1, Math.log1p(Math.max(0, Number(p.sales)||0))/Math.log1p(100000)) +
    25 * Math.max(0, Math.min(1, ((Number(p.rating)||0)-4)/1)) +
    20 * Math.min(1, Math.max(0, Number(p.discount)||0)/70) +
    15 * Math.min(1, Math.max(0, Number(p.commissionPct)||0)/20);
}
export function eligible(p) {
  return p && !p.demo && p.source !== 'demo' && p.itemId && p.title &&
    Number(p.price)>0 && Number(p.rating)>=4.5 && Number(p.sales)>=20 &&
    Number(p.commissionPct)>0 && /^https:\/\//.test(p.image||'') && /^https:\/\//.test(p.affiliateLink||'');
}
export function observe(previous, offers, now = new Date()) {
  const at = now.toISOString(), day = at.slice(0,10), cutoff = now.getTime()-7*DAY;
  return [...(Array.isArray(previous)?previous:[]).filter(s=>Date.parse(s.at)>=cutoff && s.at.slice(0,10)!==day),
    {at, offers: offers.filter(eligible)}];
}
export function weeklyRanking(snapshots, excluded = [], now = new Date()) {
  const cutoff = now.getTime()-7*DAY, latest = new Map(), excludedIDs = new Set(excluded.map(String));
  const recent = snapshots.filter(s=>Date.parse(s.at)>=cutoff && Date.parse(s.at)<=now.getTime()).sort((a,b)=>Date.parse(a.at)-Date.parse(b.at));
  for (const snapshot of recent) for (const p of snapshot.offers||[]) {
    if (eligible(p)) latest.set(String(p.itemId), {...p, observedAt:snapshot.at});
  }
  const candidates = [...latest.values()].filter(p=>!excludedIDs.has(String(p.itemId)) && Date.parse(p.observedAt)>=now.getTime()-2*DAY)
    .map(p=>({...p, selectionScore:Math.round(offerScore(p)*100)/100,
      selectionReason:`Demanda ${p.sales}; avaliação ${p.rating}/5; desconto ${p.discount||0}%; comissão ${p.commissionPct}%.`}))
    .sort((a,b)=>b.selectionScore-a.selectionScore || String(a.itemId).localeCompare(String(b.itemId)));
  return {ok:true, source:'weekly-observed-offers', windowDays:7,
    observedDays:new Set(recent.map(s=>s.at.slice(0,10))).size, candidates,
    best:candidates[0]||null,
    methodology:'40% demanda informada, 25% avaliação, 20% desconto e 15% comissão. Sem filtro por categoria. Vendas são o indicador informado pela Shopee, não vendas comprovadas dos últimos 7 dias.'};
}
export async function fetchBroadOffers(appId, secret, fetcher = fetch) {
  if (!appId || !secret) throw Error('Credenciais da Shopee ausentes');
  const offers = new Map();
  for (let page=1;page<=5;page++) {
    const query=`{ productOfferV2(sortType: 5, page: ${page}, limit: 50) { nodes { itemId productName priceMin priceMax priceDiscountRate commissionRate imageUrl productLink offerLink sales ratingStar } pageInfo { hasNextPage } } }`;
    const body=JSON.stringify({query}), timestamp=String(Math.floor(Date.now()/1000));
    const signature=crypto.createHash('sha256').update(appId+timestamp+body+secret).digest('hex');
    const response=await fetcher('https://open-api.affiliate.shopee.com.br/graphql',{method:'POST',
      headers:{'Content-Type':'application/json',Authorization:`SHA256 Credential=${appId}, Timestamp=${timestamp}, Signature=${signature}`},body,signal:AbortSignal.timeout(15000)});
    const data=await response.json();
    if (!response.ok || data.errors?.length) throw Error(data.errors?.[0]?.message||'Consulta Shopee indisponível');
    const result=data.data?.productOfferV2;
    for (const x of result?.nodes||[]) {
      const p={itemId:String(x.itemId),title:x.productName,price:Number(x.priceMin||x.priceMax),
        discount:Number(x.priceDiscountRate)||0,commissionPct:(Number(x.commissionRate)||0)*100,
        rating:Number(x.ratingStar)||0,sales:Number(x.sales)||0,image:x.imageUrl,
        affiliateLink:x.offerLink||x.productLink,source:'shopee'};
      offers.set(p.itemId,p);
    }
    if (!result?.pageInfo?.hasNextPage) break;
  }
  return [...offers.values()];
}
