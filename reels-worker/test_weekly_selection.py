import ast, json, os, pathlib, subprocess, tempfile, unittest, urllib.request
from types import SimpleNamespace
from unittest.mock import patch

SOURCE=pathlib.Path(__file__).with_name('daily.py').read_text(encoding='utf-8')
PRODUCT=next(n for n in ast.parse(SOURCE).body if isinstance(n,ast.FunctionDef) and n.name=='product')

class SelectionTests(unittest.TestCase):
 def make_namespace(self,root,history):
  def require(value,message):
   if not value:raise RuntimeError(message)
  return {'os':os,'json':json,'pathlib':pathlib,'urllib':__import__('urllib'),
          'subprocess':subprocess,'HISTORY':history,'WORK':root,'ROOT':root,'require':require}
 def response(self,candidates):
  class Response:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self):return json.dumps({'ok':True,'source':'weekly-observed-offers','observedDays':1,'candidates':candidates}).encode()
  return Response()
 def test_excludes_generated_even_if_publication_failed(self):
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as directory:
   root=pathlib.Path(directory);history=root/'history.json';history.write_text(json.dumps({'published':[],'generated':['tool']}))
   namespace=self.make_namespace(root,history)
   exec(compile(ast.Module(body=[PRODUCT],type_ignores=[]),'selection','exec'),namespace)
   with patch.dict(os.environ,{'PROMO_RADAR_API':''},clear=True),patch('urllib.request.urlopen',return_value=self.response([{'itemId':'tool','title':'Already generated'},{'itemId':'home','title':'New item'}])):
    self.assertEqual(namespace['product']()['itemId'],'home')
   self.assertTrue((root/'selection.json').exists())
 def test_falls_back_to_live_catalog_when_weekly_candidates_are_exhausted(self):
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as directory:
   root=pathlib.Path(directory);history=root/'history.json';history.write_text(json.dumps({'published':['old'],'generated':[]}))
   namespace=self.make_namespace(root,history)
   exec(compile(ast.Module(body=[PRODUCT],type_ignores=[]),'selection','exec'),namespace)
   live={'itemId':'fresh','title':'Current Shopee offer','price':29.9,'rating':4.8,'sales':120,'commissionPct':10,'image':'https://img.susercontent.com/item.jpg','affiliateLink':'https://shopee.com.br/item'}
   completed=SimpleNamespace(stdout=json.dumps(live)+'\n',stderr='',returncode=0)
   with patch.dict(os.environ,{'PROMO_RADAR_API':''},clear=True),patch('urllib.request.urlopen',return_value=self.response([{'itemId':'old','title':'Already published'}])),patch('subprocess.run',return_value=completed) as run:
    selected=namespace['product']()
   self.assertEqual(selected['itemId'],'fresh')
   self.assertIn('old',run.call_args.kwargs['env']['PROMO_RADAR_EXCLUDED_IDS'])
   report=json.loads((root/'selection.json').read_text())
   self.assertEqual(report['source'],'shopee-live-catalog-fallback')

if __name__=='__main__':unittest.main()
