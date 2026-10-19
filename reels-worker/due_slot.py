#!/usr/bin/env python3
import datetime as dt,json,os,pathlib,urllib.request
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
def get_config():
 app=(os.getenv('PROMO_RADAR_API') or 'https://shopee-afiliado-auto.vercel.app').rstrip('/')
 if app!='https://shopee-afiliado-auto.vercel.app':raise RuntimeError('Unrecognized scheduling site')
 with urllib.request.urlopen(app+'/api/publication-schedule',timeout=45) as r:config=json.load(r)
 if not config.get('ok'):raise RuntimeError('Schedule unavailable')
 return config
def choose_due(config,ledger,now=None):
 if config.get('enabled') is not True:return None
 now=now or dt.datetime.now(ZoneInfo('America/Sao_Paulo'))
 now=now.astimezone(ZoneInfo('America/Sao_Paulo'));day=now.date().isoformat()
 slots=[(key,'photo',hour) for key,hour in zip(['photo-lunch','photo-evening','photo-night'],config.get('photo_times',[]))]
 slots.append(('reel','reel',config['reel_time']))
 for slot,kind,hour in sorted(slots,key=lambda x:x[2]):
  at=dt.datetime.combine(now.date(),dt.time.fromisoformat(hour),tzinfo=ZoneInfo('America/Sao_Paulo'))
  age=(now-at).total_seconds()
  if 0<=age<=7200 and day+'/'+slot not in ledger:return slot,kind,hour
 return None
def main():
 config=get_config();file=ROOT/'posting-ledger.json';ledger=json.loads(file.read_text()) if file.exists() else {}
 due=choose_due(config,ledger);slot=due[0] if due else ''
 if os.getenv('GITHUB_OUTPUT'):
  with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('slot='+slot+'\n')
 print('PUBLICATION_DUE '+slot if slot else 'NO_PUBLICATION_DUE')
if __name__=='__main__':main()
