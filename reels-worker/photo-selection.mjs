export function selectProductPhotos(media,fallback){
 const gallery=Array.isArray(media?.images)?[...new Set(media.images.filter(x=>typeof x==='string'&&/^https:\/\//i.test(x)))].slice(0,5):[];
 if(media?.ok&&media?.hasFivePhotos===true&&gallery.length===5)return gallery;
 return typeof fallback==='string'&&/^https:\/\//i.test(fallback)?[fallback]:[];
}
