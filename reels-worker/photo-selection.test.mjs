import test from 'node:test';
import assert from 'node:assert/strict';
import {selectProductPhotos} from './photo-selection.mjs';

test('uses five unique verified gallery photos when available',()=>{
 const images=Array.from({length:5},(_,i)=>`https://cf.shopee.com.br/file/photo-${i}`);
 assert.deepEqual(selectProductPhotos({ok:true,hasFivePhotos:true,images},'https://cf.shopee.com.br/file/main'),images);
});

test('falls back to the catalog photo when a full verified gallery is unavailable',()=>{
 const fallback='https://cf.shopee.com.br/file/main';
 assert.deepEqual(selectProductPhotos({ok:true,hasFivePhotos:false,images:[fallback]},fallback),[fallback]);
 assert.deepEqual(selectProductPhotos({ok:true,hasFivePhotos:true,images:[fallback,fallback]},fallback),[fallback]);
 assert.deepEqual(selectProductPhotos(null,fallback),[fallback]);
});
