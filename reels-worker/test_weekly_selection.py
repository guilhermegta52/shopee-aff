import ast, json, pathlib, tempfile, unittest, urllib.request
from unittest.mock import patch

SOURCE=pathlib.Path(__file__).with_name('daily.py').read_text(encoding='utf-8')
PRODUCT=next(n for n in ast.parse(SOURCE).body if isinstance(n,ast.FunctionDef) and n.name=='product')

class SelectionTests(unittest.TestCase):
 def test_excludes_generated_even_if_publication_failed(self):
  with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as directory:
   root=pathlib.Path(directory);history=root/'history.json';history.write_text(json.dumps({'published':[],'generated':['tool']}))
   def require(value,message):
    if not value:raise RuntimeError(message)
   import os
   namespace={'os':os,'json':json,'pathlib':pathlib,'urllib':__import__('urllib'),'HISTORY':history,'WORK':root,'require':require}
   exec(compile(ast.Module(body=[PRODUCT],type_ignores=[]),'selection','exec'),namespace)
   class Response:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps({'ok':True,'source':'weekly-observed-offers','observedDays':1,'candidates':[{'itemId':'tool','title':'Already generated'},{'itemId':'home','title':'New item'}]}).encode()
   with patch.dict(os.environ,{},clear=True),patch('urllib.request.urlopen',return_value=Response()):
    self.assertEqual(namespace['product']()['itemId'],'home')
   self.assertTrue((root/'selection.json').exists())

if __name__=='__main__':unittest.main()
