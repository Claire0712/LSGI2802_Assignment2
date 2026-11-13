import unittest,sys,numpy as np
sys.path.insert(0,'scripts')
from graph_core import node_key,arcs,sparse_min
from scipy.sparse.csgraph import dijkstra
class GraphChecks(unittest.TestCase):
 def test_levels(self):self.assertNotEqual(node_key([0,0,0]),node_key([0,0,5]))
 def test_direction(self):
  self.assertEqual(arcs(0,1,1),[(0,1)]);self.assertEqual(arcs(0,1,-1),[(1,0)]);self.assertEqual(len(arcs(0,1,0)),2)
 def test_parallel_not_sum(self):
  a=sparse_min(np.array([0,0,1]),np.array([1,1,2]),np.array([2.,5.,3.]),3)
  d=dijkstra(a,directed=True,indices=0);self.assertEqual(d[2],5)
  self.assertTrue(np.isinf(dijkstra(a,directed=True,indices=2)[0]))
if __name__=='__main__':unittest.main()
