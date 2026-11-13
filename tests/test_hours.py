import unittest,sys
sys.path.insert(0,'scripts')
from access_hours import active_interval,allowed
class Hours(unittest.TestCase):
 def test_overnight(self):
  self.assertTrue(active_interval(30,531,101));self.assertTrue(active_interval(1000,531,101));self.assertFalse(active_interval(300,531,101))
 def test_closed(self):
  d=[dict(DayCode='WD',FromTime=900,ToTime=1100)]
  self.assertTrue(allowed('OPEN',d));self.assertFalse(allowed('CLOSE',d));self.assertIsNone(allowed('OPEN',[]))
if __name__=='__main__':unittest.main()
