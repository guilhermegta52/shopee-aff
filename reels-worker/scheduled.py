#!/usr/bin/env python3
"""Three free photos and one daily Reel, with durable publication reservations."""
import datetime as dt, json, os, pathlib, subprocess, sys
from due_slot import get_config,choose_due
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
SLOTS={
 '15 15 * * *':('photo-lunch','photo','12:15'),
 '15 21 * * *':('photo-evening','photo','18:15'),
 '15 22 * * *':('reel','reel','19:15'),
 '45 23 * * *':('photo-night','photo','20:45'),
}
def plan(cron):
 if cron not in SLOTS:raise RuntimeError('Unrecognized schedule')
 return SLOTS[cron]
def git(*args):subprocess.run(['git',*args],cwd=ROOT,check=True)
def persist(files,message):
 git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
 git('config','user.name','github-actions[bot]')
 git('add',*files)
 if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
  git('commit','-m',message);git('push','origin','HEAD:main')
def main():
 day=dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date().isoformat()
 ledger_file=ROOT/'posting-ledger.json'
 ledger=json.loads(ledger_file.read_text()) if ledger_file.exists() else {}
 config=get_config()
 due=choose_due(config,ledger)
 if not due:print('NO_PUBLICATION_DUE');return
 slot,kind,hour=due
 if os.getenv('POST_SLOT') and os.getenv('POST_SLOT')!=slot:print('SCHEDULE_CHANGED_BEFORE_EXECUTION');return
 key=day+'/'+slot
 if key in ledger:print('SLOT_ALREADY_RESERVED',key);return
 if os.getenv('ENABLE_REAL_POSTING')!='true':
  print('SCHEDULE_DRY_RUN',day,slot,kind,hour,'America/Sao_Paulo');return
 ledger[key]={'kind':kind,'time':hour,'state':'reserved-before-publication','run_id':os.getenv('GITHUB_RUN_ID')}
 ledger_file.write_text(json.dumps(ledger,indent=2)+'\n')
 persist(['posting-ledger.json'],'chore: reserve publication '+key)
 try:
  if kind=='photo':
   from daily import product
   p=product()
   out=ROOT/'out';out.mkdir(exist_ok=True)
   meta=out/'photo-product.json';meta.write_text(json.dumps(p,ensure_ascii=False,indent=2))
   subprocess.run(['node',str(ROOT/'publish-photo.mjs'),str(meta)],check=True)
   history_file=ROOT/'history.json';history=json.loads(history_file.read_text())
   history.setdefault('published',[])
   if str(p['itemId']) not in history['published']:history['published'].append(str(p['itemId']))
   history_file.write_text(json.dumps(history,indent=2)+'\n')
  else:
   env=dict(os.environ)
   paid=json.loads((ROOT/'ai-daily-ledger.json').read_text()) if (ROOT/'ai-daily-ledger.json').exists() else {}
   use_ai=bool(env.get('HF_KEY')) and day not in paid
   env.update(PRESENTER_MODE='ai' if use_ai else 'free',DAILY_BUDGET_GUARD='true' if use_ai else 'false',ENABLE_PAID_AI_GENERATION='true' if use_ai else 'false')
   subprocess.run([sys.executable,str(ROOT/'daily.py'),'--publish'],check=True,env=env)
  ledger[key]['state']='published'
  published=ROOT/'out'/'publish.json'
  if published.exists():ledger[key]['publication']=json.loads(published.read_text())
 finally:
  # A confirmed Instagram post stays recorded even if storefront storage failed.
  publication=ROOT/'out'/'publish.json'
  if publication.exists():
   receipt=json.loads(publication.read_text())
   ledger[key]['publication']=receipt
   ledger[key]['state']='published'
   history_file=ROOT/'history.json';history=json.loads(history_file.read_text())
   history.setdefault('published',[])
   if str(receipt['itemId']) not in history['published']:history['published'].append(str(receipt['itemId']))
   history_file.write_text(json.dumps(history,indent=2)+'\n')
  ledger_file.write_text(json.dumps(ledger,indent=2)+'\n')
  persist(['posting-ledger.json','history.json'],'chore: save publication state '+key)
if __name__=='__main__':main()
