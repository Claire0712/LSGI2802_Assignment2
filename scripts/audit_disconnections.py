import numpy as np,pandas as pd,json
from scipy.spatial import cKDTree
from pathlib import Path
z=np.load('data/processed/network_arrays.npz');xyz=z['xyz'];lab=z['components']
b=pd.read_csv('results/baseline_tpu.csv',dtype={'TPU':str});o=pd.read_csv('data/processed/origins.csv',dtype={'TPU':str});rows=[]
for r in b[np.isinf(b.M)].itertuples():
 a=o[(o.TPU==r.TPU)&(o.choice==0)].iloc[0];comp=lab[int(a.node)];members=np.where(lab==comp)[0];outside=np.where(lab!=comp)[0];dd,ii=cKDTree(xyz[outside]).query(xyz[members]);j=int(np.argmin(dd))
 rows.append(dict(TPU=r.TPU,component=int(comp),nodes=len(members),nearest_other_component_3d_m=float(dd[j]),from_node=int(members[j]),to_node=int(outside[ii[j]]),interpretation='model disconnection; not verified real-world isolation'))
pd.DataFrame(rows).to_csv('results/disconnection_audit.csv',index=False)
Path('results/final_network_audit.json').write_text(json.dumps({'source_features':465892,'nodes':len(xyz),'directed_arcs':len(z['u']),'weak_components':len(np.unique(lab)),'sub_decimetre_links':len(pd.read_csv('results/topology_joins.csv')),'baseline_model_disconnections':len(rows)},indent=2))
print('Audited',len(rows),'model-disconnected origins')
