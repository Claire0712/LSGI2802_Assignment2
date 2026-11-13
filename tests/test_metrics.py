import unittest,numpy as np,sys
sys.path.insert(0,'scripts')
from measures import indices,low_set
class Checks(unittest.TestCase):
 def test_known(self):
  m,c,g=indices(np.array([[5,40,45],[12,13,14],[np.inf,np.inf,np.inf],[np.nan,2,3]]))
  np.testing.assert_equal(m[:3],[5,12,np.inf]);np.testing.assert_equal(c[:3],[1,3,0])
  self.assertGreater(g[1],g[0]);self.assertEqual(g[2],0);self.assertTrue(np.isnan(g[3]))
 def test_ties(self):
  self.assertEqual(low_set(np.array([0,0,0,2,3])),{0,1,2})
 def test_monotonic(self):
  t=np.array([[4,15,22],[14,16,np.inf]])
  m,c,g=indices(t);mm,cc,gg=indices(t*1.6)
  self.assertTrue(np.all(mm>=m));self.assertTrue(np.all(cc<=c));self.assertTrue(np.all(gg<=g))
if __name__=='__main__':unittest.main()
