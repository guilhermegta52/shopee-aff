#!/usr/bin/env python3
"""Promo Radar unattended daily Reels worker. Dry-run by default; no publication unless --publish."""
import argparse, datetime, hashlib, json, math, os, pathlib, re, shutil, subprocess, sys, time, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT=pathlib.Path(__file__).resolve().parent
WORK=ROOT/'out'
HISTORY=ROOT/'history.json'
FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','C:/Windows/Fonts/arialbd.ttf']
def font(size):
 for f in FONTS:
  if pathlib.Path(f).exists():return ImageFont.truetype(f,size)
 return ImageFont.load_default()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def txt(draw,s,y,size=64,color='white',maxw=930,center=False):
 f=font(size); words=str(s).split();lines=[];line=''
 for word in words:
  test=(line+' '+word).strip()
  if draw.textbbox((0,0),test,font=f)[2]>maxw and line:lines.append(line);line=word
  else:line=test
 if line:lines.append(line)
 for l in lines[:3]:
  w=draw.textbbox((0,0),l,font=f)[2]
  draw.text(((1080-w)/2 if center else 75,y),l,font=f,fill=color,stroke_width=1,stroke_fill='#14252a');y+=size*1.27
 return y
def overlay(prod,img,idx,path):
 bg=Image.new('RGB',(1080,1920),'#081b2b');g=ImageDraw.Draw(bg)
 for y in range(1920):
  k=y/1920;g.line((0,y,1080,y),fill=(int(10+15*k),int(28+34*k),int(43+15*k)))
 g.rounded_rectangle((50,55,1030,163),radius=30,fill='#153744')
 txt(g,'PROMO RADAR',88,46,'#ffffff',850)
 g.rounded_rectangle((50,220,1030,1245),radius=50,fill='#ffffff')
 photo=Image.open(img).convert('RGB');photo.thumbnail((900,880),Image.Resampling.LANCZOS)
 bg.paste(photo,(540-photo.width//2,720-photo.height//2))
 # Flat branded overlay; movements and fades are added by FFmpeg after compositing.
 g=ImageDraw.Draw(bg)
 sections=['ACHADINHO DA SHOPEE','OLHA OS DETALHES','OFERTA EM DESTAQUE','CONFIRA A OFERTA']
 g.rounded_rectangle((80,250,770,333),radius=24,fill='#ff6622')
 txt(g,sections[idx],271,37,'#ffffff',880)
 name=prod['title'].strip()
 txt(g,name,1300,55,maxw=930)
 if idx in (2,3):
  g.rounded_rectangle((50,1550,1030,1710),radius=30,fill='#ff6622')
  txt(g,'PREÇO INFORMADO',1560,36)
  txt(g,'R$ '+format(float(prod['price']),'.2f').replace('.',','),1620,69)
 elif idx==0:txt(g,'ENCONTREI ESSA OFERTA!',1565,57,center=True)
 else:
  if float(prod.get('discount',0))>0:txt(g,f"DESCONTO INFORMADO: {round(float(prod['discount']))}%",1570,48)
  else:txt(g,'VEJA AS FOTOS DO PRODUTO',1570,44)
 txt(g,'CONFIRA O LINK NA LEGENDA',1810,41,center=True)
 bg.save(path,quality=91)
def run(cmd,**kwargs):
 subprocess.run(list(map(str,cmd)),check=True,**kwargs)
def probe(ffmpeg,path):
 cmd=[ffmpeg,'-hide_banner','-i',str(path),'-f','null',os.devnull]
 r=subprocess.run(cmd,capture_output=True,text=True)
 require(r.returncode==0,'MP4 inválido: '+r.stderr[-600:])
 require('Video: h264' in r.stderr and 'Audio: aac' in r.stderr,'Faltou H264 ou AAC')
 require('1080x1920' in r.stderr,'Dimensões incorretas')
def voice(script,wav):
 if os.getenv('TEST_WAV'):
  shutil.copyfile(os.getenv('TEST_WAV'),wav);return
 piper=shutil.which('piper')
 require(piper,'Piper indisponível; instale piper-tts no runner')
 name=os.getenv('PIPER_VOICE','pt_BR-faber-medium')
 run([piper,'--model',name,'--output_file',wav],input=script.encode('utf-8'))
def product():
 if os.getenv('TEST_PRODUCT'):
  data=json.loads(pathlib.Path(os.getenv('TEST_PRODUCT')).read_text(encoding='utf8'))
  return data
 app=os.getenv('PROMO_RADAR_API','https://shopee-afiliado-auto.vercel.app').rstrip('/')
 require(app.startswith('https://'),'Fonte de ofertas deve usar HTTPS')
 req=urllib.request.Request(app+'/api/weekly-best',headers={'User-Agent':'PromoRadarDailyWorker/2.0'})
 with urllib.request.urlopen(req,timeout=120) as resp:data=json.load(resp)
 require(data.get('ok') and data.get('source')=='weekly-observed-offers','Ranking semanal indisponível; não usar seleção antiga')
 history=json.loads(HISTORY.read_text('utf8')) if HISTORY.exists() else {}
 used={str(x) for x in history.get('published',[])+history.get('generated',[])}
 products=[p for p in data.get('candidates',[]) if str(p.get('itemId')) not in used]
 require(products,'Nenhuma oferta inédita e completa no ranking dos últimos 7 dias')
 chosen=products[0]
 WORK.mkdir(exist_ok=True)
 report={'source':data['source'],'windowDays':7,'observedDays':data.get('observedDays'),
         'methodology':data.get('methodology'),'selected':chosen,
         'excludedCount':len(used),'topCandidates':products[:10]}
 (WORK/'selection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print('WEEKLY_PRODUCT_SELECTED',chosen['itemId'],chosen['title'],chosen.get('selectionScore'),flush=True)
 return chosen

def download_photo(prod):
 src=str(prod.get('image',''))
 if os.getenv('TEST_IMAGE'):return pathlib.Path(os.getenv('TEST_IMAGE'))
 url=urllib.parse.urlparse(src)
 require(url.scheme=='https' and (url.hostname or '').endswith(('susercontent.com','shopee.com.br')),'Imagem de origem não permitida')
 req=urllib.request.Request(src,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=25) as r:content=r.read(10*1024*1024)
 require(len(content)>2000,'Imagem vazia')
 target=WORK/'product.jpg';target.write_bytes(content)
 return target
def synth_script(p):
 amount=f"R$ {float(p['price']):.2f}".replace('.',',')
 return ('Olha essa oferta da Shopee! '+str(p['title'])[:85]+
         '. O preço informado é '+amount+
         '. Confira fotos, detalhes e disponibilidade no link da legenda antes de comprar.')
def render(prod,ffmpeg,image,wav,dest,presenter_clip=None):
 slides=[]
 for i in range(4):
  path=WORK/f'cena-{i+1}.jpg';overlay(prod,image,i,path);slides.append(path)
 # Four scenes at 30 fps. Allow time for the narration to finish.
 probe_wav=subprocess.run([ffmpeg,'-hide_banner','-i',str(wav)],capture_output=True,text=True).stderr
 match=re.search(r'Duration: (\d+):(\d+):([\d.]+)',probe_wav)
 wav_seconds=(int(match[1])*3600+int(match[2])*60+float(match[3])) if match else 15
 require(wav_seconds<=43,'Narração maior que 43 segundos: reduza o roteiro')
 total=max(16,math.ceil(wav_seconds+1.5))
 segment=total/4
 clips=[]
 for i,s in enumerate(slides):
  path=WORK/f'clip-{i}.mp4'
  vf=("scale=1130:2010:force_original_aspect_ratio=increase,"
      "crop=1080:1920:x='(in_w-1080)/2+14*sin(n/18)':y='(in_h-1920)/2+16*cos(n/23)',"
      f"fade=t=in:st=0:d=0.35,fade=t=out:st={segment-.4}:d=0.4,setsar=1,format=yuv420p")
  if i==0 and presenter_clip:
   ai_vf=("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          f"fade=t=in:st=0:d=0.35,fade=t=out:st={segment-.4}:d=0.4,setsar=1,format=yuv420p")
   run([ffmpeg,'-y','-stream_loop','-1','-i',presenter_clip,'-t',str(segment),'-vf',ai_vf,
        '-an','-r','30','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',path],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  else:
   run([ffmpeg,'-y','-loop','1','-framerate','30','-i',s,'-t',str(segment),'-vf',vf,'-an','-r','30','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',path],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  clips.append(path)
 concat=WORK/'concat.txt';concat.write_text(''.join("file '"+p.resolve().as_posix()+"'\n" for p in clips),encoding='utf8')
 run([ffmpeg,'-y','-f','concat','-safe','0','-i',concat,'-i',wav,'-map','0:v','-map','1:a',
      '-t',str(total),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-r','30',
      '-c:a','aac','-b:a','160k','-ar','48000','-af','apad','-movflags','+faststart',dest],
      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 probe(ffmpeg,dest)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');args=parser.parse_args()
 require(not args.publish or os.getenv('ENABLE_REAL_POSTING')=='true','Publicação desabilitada por segurança')
 WORK.mkdir(exist_ok=True)
 ffmpeg=os.getenv('FFMPEG_BIN') or shutil.which('ffmpeg')
 if not ffmpeg:
  import imageio_ffmpeg
  ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
 p=product();require(p.get('title') and float(p.get('price') or 0)>0,'Produto inválido')
 image=download_photo(p);wav=WORK/'narracao.wav';voice(synth_script(p),wav)
 presenter_clip=None
 if os.getenv('PRESENTER_MODE')=='ai':
  from presenter import generate
  presenter_clip=generate(p,WORK/'presenter.mp4')
 dest=WORK/'promo-reel.mp4';render(p,ffmpeg,image,wav,dest,presenter_clip)
 metadata={'itemId':str(p['itemId']),'title':p['title'],'affiliateLink':p.get('affiliateLink'),'price':p['price'],
           'video':str(dest),'date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'publish':args.publish}
 (WORK/'result.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf8')
 if not os.getenv('TEST_PRODUCT'):
  hist=json.loads(HISTORY.read_text('utf8')) if HISTORY.exists() else {'published':[]}
  hist.setdefault('generated',[])
  if str(p['itemId']) not in hist['generated']:hist['generated'].append(str(p['itemId']))
  HISTORY.write_text(json.dumps(hist,indent=2),encoding='utf8')
 print('VIDEO_OK',dest,round(dest.stat().st_size/1024/1024,2),'MB')
 if args.publish:
  require(p.get('affiliateLink'),'Link de afiliado obrigatório')
  run(['node',str(ROOT/'publish.mjs'),str(dest),str(WORK/'result.json')])
  hist=json.loads(HISTORY.read_text('utf8')) if HISTORY.exists() else {'published':[]}
  hist['published'].append(str(p['itemId']))
  HISTORY.write_text(json.dumps(hist,indent=2),encoding='utf8')
  print('PUBLISHED',p['itemId'])
 else:print('DRY_RUN: nenhuma publicação foi feita')
if __name__=='__main__':
 try: main()
 except Exception as exc:print('ERROR',str(exc),file=sys.stderr);sys.exit(1)