"""Join only sub-decimetre 3D gaps between disconnected components; preserve audit."""
from pathlib import Path
import shutil,json
import numpy as np,pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import connected_components
from graph_core import sparse_min
p=Path('data/processed/network_arrays.npz');backup=p.with_name('network_exact_xyz.npz')
if not backup.exists():shutil.copy2(p,backup)
z=dict(np.load(backup));xyz=z['xyz'];lab=z['components'];pairs=cKDTree(xyz).query_pairs(.1,output_type='ndarray');pairs=pairs[lab[pairs[:,0]]!=lab[pairs[:,1]]]
dist=np.linalg.norm(xyz[pairs[:,0]]-xyz[pairs[:,1]],axis=1);print('sub-decimetre intercomponent joins',len(pairs),flush=True)
pd.DataFrame({'u':pairs[:,0],'v':pairs[:,1],'distance_m':dist}).to_csv('results/topology_joins.csv',index=False)
for key,vals in [('u',np.r_[pairs[:,0],pairs[:,1]]),('v',np.r_[pairs[:,1],pairs[:,0]]),('walk',np.r_[dist,dist]),('fixed',np.zeros(2*len(pairs))),('cover',np.full(2*len(pairs),3)),('typ',np.full(2*len(pairs),0)),('route',np.full(2*len(pairs),-1))]:z[key]=np.r_[z[key],vals].astype(z[key].dtype)
g=sparse_min(z['u'],z['v'],z['walk']/80+z['fixed'],len(xyz));nc,labels=connected_components(g,directed=True,connection='weak');z['components']=labels
np.savez_compressed(p,**z);print('components',len(np.unique(lab)),'to',nc,flush=True)
