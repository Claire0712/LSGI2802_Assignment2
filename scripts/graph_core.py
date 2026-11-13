import numpy as np
from scipy.sparse import csr_matrix
def node_key(p):
 if len(p)<3:raise ValueError('Z required')
 return tuple(round(float(x),3) for x in p[:3])
def arcs(u,v,direction):
 if direction==1:return [(u,v)]
 if direction==-1:return [(v,u)]
 if direction==0:return [(u,v),(v,u)]
 raise ValueError('unknown direction')
def sparse_min(u,v,w,n):
 key=u.astype(np.int64)*n+v;order=np.argsort(key);key=key[order];w=w[order]
 first=np.r_[0,np.flatnonzero(np.diff(key))+1];weights=np.minimum.reduceat(w,first);key=key[first]
 return csr_matrix((weights,(key//n,key%n)),shape=(n,n))
