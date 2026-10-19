import ast, os, pathlib, sys, types, unittest
from unittest.mock import Mock, patch
from scheduled import plan, SLOTS
class ScheduleTests(unittest.TestCase):
 def test_three_photos_one_reel_and_brasilia_times(self):
  self.assertEqual(len(SLOTS),4)
  self.assertEqual(sum(v[1]=='photo' for v in SLOTS.values()),3)
  self.assertEqual([v[2] for v in SLOTS.values()],['12:15','18:15','19:15','20:45'])
  with self.assertRaises(RuntimeError):plan('unexpected')
 def test_paid_failure_falls_back_without_a_second_request(self):
  source=pathlib.Path(__file__).with_name('daily.py').read_text(encoding='utf8')
  main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
  block=next(n for n in main.body if isinstance(n,ast.If) and "PRESENTER_MODE" in ast.unparse(n.test))
  provider=types.ModuleType('presenter')
  provider.generate=Mock(side_effect=RuntimeError('insufficient credits'))
  scope={'os':os,'p':{},'WORK':pathlib.Path('.'),'presenter_clip':None}
  with patch.dict(sys.modules,{'presenter':provider}),patch.dict(os.environ,{'PRESENTER_MODE':'ai','DAILY_BUDGET_GUARD':'false'}):
   exec(compile(ast.Module(body=[block],type_ignores=[]),'fallback','exec'),scope)
  self.assertIsNone(scope['presenter_clip'])
  provider.generate.assert_called_once()
if __name__=='__main__':unittest.main()
