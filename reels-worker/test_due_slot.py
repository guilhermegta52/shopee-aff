import datetime as dt,unittest
from due_slot import choose_due
from zoneinfo import ZoneInfo
TZ=ZoneInfo('America/Sao_Paulo')
class EditableScheduleTests(unittest.TestCase):
 def test_changed_time_pause_and_completed_slots(self):
  config={'enabled':True,'photo_times':['08:00','14:30','20:00'],'reel_time':'18:00'}
  now=dt.datetime(2026,10,20,14,45,tzinfo=TZ)
  self.assertEqual(choose_due(config,{},now),('photo-evening','photo','14:30'))
  self.assertIsNone(choose_due(config,{'2026-10-20/photo-evening':{}},now))
  self.assertIsNone(choose_due({**config,'enabled':False},{},now))
 def test_recovers_a_slot_more_than_two_hours_late(self):
  config={'enabled':True,'photo_times':['12:15','18:15','20:45'],'reel_time':'19:15'}
  now=dt.datetime(2026,10,21,20,25,tzinfo=TZ)
  self.assertEqual(choose_due(config,{},now),('photo-evening','photo','18:15'))
 def test_recovers_night_slot_after_two_hours(self):
  config={'enabled':True,'photo_times':['12:15','18:15','20:45'],'reel_time':'19:15'}
  now=dt.datetime(2026,10,21,22,45,13,tzinfo=TZ)
  ledger={'2026-10-21/photo-lunch':{},'2026-10-21/photo-evening':{},'2026-10-21/reel':{}}
  self.assertEqual(choose_due(config,ledger,now),('photo-night','photo','20:45'))
 def test_does_not_replay_yesterday_after_midnight(self):
  config={'enabled':True,'photo_times':['12:15','18:15','20:45'],'reel_time':'19:15'}
  now=dt.datetime(2026,10,22,1,0,tzinfo=TZ)
  self.assertIsNone(choose_due(config,{},now))
 def test_rejects_slots_more_than_six_hours_late(self):
  config={'enabled':True,'photo_times':['08:00','14:30','20:00'],'reel_time':'18:00'}
  now=dt.datetime(2026,10,20,20,31,tzinfo=TZ)
  self.assertIsNone(choose_due(config,{},now))
if __name__=='__main__':unittest.main()
