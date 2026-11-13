from pathlib import Path
import json,pickle,collections
import numpy as np
from scipy.sparse.csgraph import connected_components
from graph_core import node_key,arcs,sparse_min
# Connect identical XYZ vertices at millimetre precision; never planarize XY crossings.
node_ids={};coords=[];surface=set();u=[];v=[];length=[];cover=[];typ=[];route=[];counts=collections.Counter()
def nid(p):
 k=node_key(p)
 if k not in node_ids:node_ids[k]=len(coords);coords.append(k)
 return node_ids[k]
import geopandas as gpd,pandas as pd,hashlib,pyogrio
from access_hours import allowed
source=Path('data/raw/network_full/3DPN_P2.gdb')
net=gpd.read_file(source,layer='PedestrianRoute');assert len(net)==465892
schedule=pyogrio.read_dataframe(source,layer='AccessTime');detail=pyogrio.read_dataframe(source,layer='AccessTimeDetails')
schedule.to_csv('data/processed/AccessTime.csv',index=False);detail.to_csv('data/processed/AccessTimeDetails.csv',index=False)
groups={int(k):v.to_dict('records') for k,v in detail.groupby('AccessTimeID')}
access={int(r.AccessTimeID):allowed(r.AccessTimeType,groups.get(int(r.AccessTimeID),[]),now=1500) for r in schedule.itertuples()}
for idx,a in enumerate(net.itertuples()):
 counts['raw']+=1
 if a.Enabled!=1:counts['disabled']+=1;continue
 if a.Location==3:counts['paid']+=1;continue
 if a.Direction not in (-1,0,1):counts['unknown_direction']+=1;continue
 if pd.notna(a.AccessTimeID):
  state=access.get(int(a.AccessTimeID))
  if state is False:counts['closed_Monday_1500']+=1;continue
  if state is None:counts['unknown_schedule_excluded']+=1;continue
 for part in a.geometry.geoms:
  path=list(part.coords)
  if not path or any(len(p)<3 for p in path):counts['missing_z']+=1;continue
  ns=[nid(p) for p in path]
  if a.Location==1 and a.FeatureType in (1,5,6,7,23,24,25,26,30,31,32,33):surface.update(ns)
  for i in range(len(path)-1):
   dist=float(np.linalg.norm(np.asarray(path[i][:3])-path[i+1][:3]))
   if dist<=0:continue
   for aa,bb in arcs(ns[i],ns[i+1],a.Direction):
    u.append(aa);v.append(bb);length.append(dist);cover.append(a.WeatherProof if pd.notna(a.WeatherProof) else 3);typ.append(a.FeatureType);route.append(a.PedestrianRouteID)
 if idx%50000==0:print(idx,len(coords),len(u),flush=True)
manifest={'source':'https://static.csdi.gov.hk/csdi-webpage/download/d0317d97c6755968809308308a768bcb/fgdb','retrieved':'2026-10-24','revision':'2026-09-16','features':len(net),'sha256':hashlib.sha256(Path('data/raw/3DPN_full.zip').read_bytes()).hexdigest(),'network_reference':'ordinary Monday 15:00, non-public-holiday, static availability'}
Path('data/raw/network_full_manifest.json').write_text(json.dumps(manifest,indent=2))
del net,node_ids
n=len(coords);u=np.asarray(u,np.int32);v=np.asarray(v,np.int32);length=np.asarray(length);typ=np.asarray(typ,np.int16)
# Lift traversal cost uses 60 metres/minute vertical speed, no assumed waiting time.
# Documented deviation from proposal: avoids assigning a repeated fixed wait to segmented lifts.
fixed=np.where(np.isin(typ,[10,18]),length/60,0);walk=np.where(np.isin(typ,[10,18]),0,length)
g=sparse_min(u,v,walk/80+fixed,n);ncomp,labels=connected_components(g,directed=True,connection='weak')
np.savez_compressed('data/processed/network_arrays.npz',xyz=np.asarray(coords),u=u,v=v,walk=walk,fixed=fixed,cover=np.asarray(cover,np.int8),typ=typ,route=np.asarray(route,np.int32),surface=np.array(sorted(surface),np.int32),components=labels)
counts.update(nodes=n,arcs=len(u),weak_components=ncomp);counts['component_sizes']=sorted(np.bincount(labels).tolist(),reverse=True)[:25]
Path('results/network_audit.json').write_text(json.dumps(dict(counts),indent=2));print(counts,flush=True)

import shutil
shutil.copy2("data/processed/network_arrays.npz","data/processed/network_exact_xyz.npz")
