import datetime as dt,unittest
from due_slot import choose_due
from zoneinfo import ZoneInfo
class EditableScheduleTests(unittest.TestCase):
 def test_changed_time_pause_and_completed_slots(self):
  config={'enabled':True,'photo_times':['08:00','14:30','20:00'],'reel_time':'18:00'}
  now=dt.datetime(2026,10,20,14,45,tzinfo=ZoneInfo('America/Sao_Paulo'))
  self.assertEqual(choose_due(config,{},now),('photo-evening','photo','14:30'))
  self.assertIsNone(choose_due(config,{'2026-10-20/photo-evening':{}},now))
  self.assertIsNone(choose_due({**config,'enabled':False},{},now))
 def test_not_early_and_not_older_than_two_hours(self):
  config={'enabled':True,'photo_times':['08:00','14:30','20:00'],'reel_time':'18:00'}
  self.assertIsNone(choose_due(config,{},dt.datetime(2026,10,20,14,0,tzinfo=ZoneInfo('America/Sao_Paulo'))))
if __name__=='__main__':unittest.main()
