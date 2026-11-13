import geopandas as gpd,pandas as pd,numpy as np,json
from shapely import points,contains_xy
from scipy.spatial import cKDTree
from pathlib import Path
z=np.load('data/processed/network_arrays.npz');xyz=z['xyz'];surface=z['surface'];xy=xyz[surface,:2];tree=cKDTree(xy)
t=gpd.read_file('data/processed/geography.gpkg',layer='tpu');c=gpd.read_file('data/processed/geography.gpkg',layer='census');c=c[c.t_pop>0].copy();c['density']=c.t_pop/c.area
rows=[]
for r in t.itertuples():
 cand=c.iloc[c.sindex.query(r.geometry,predicate='intersects')].sort_values(['density','ssbg'],ascending=[False,True]); choices=[]
 for s in cand.itertuples():
  area=r.geometry.intersection(s.geometry)
  if area.area<10:continue
  rp=area.representative_point();distance,ix=tree.query([rp.x,rp.y],k=min(1000,len(xy)))
  within=contains_xy(area.buffer(.01),xy[ix,0],xy[ix,1]);valid=np.where(within)[0]
  if len(valid):j=valid[0]
  else:continue
  node=int(surface[ix[j]])
  if node in [x['node'] for x in choices]:continue
  choices.append(dict(TPU=r.TPU,origin_id=f'{r.TPU}_{len(choices)}',choice=len(choices),node=node,x=xyz[node,0],y=xyz[node,1],z=xyz[node,2],census_group=s.ssbg,census_label=s.ssbg_eng,group_population_reference=s.t_pop,group_density_reference=s.density,proxy_shift_m=float(distance[j]),status='census_guided_network_proxy'))
  if len(choices)==3:break
 if not choices:rows.append(dict(TPU=r.TPU,origin_id=f'{r.TPU}_0',choice=0,status='no_supported_network_proxy'))
 else:rows.extend(choices)
o=pd.DataFrame(rows);o.to_csv('data/processed/origins.csv',index=False)
print('origins',len(o),'baseline',len(o[o.choice==0]),o[o.choice==0].status.value_counts().to_dict(),flush=True)
# Clinic connectors are transparent nearest outdoor-network-node approximations, audited separately.
f=gpd.read_file('data/processed/geography.gpkg',layer='clinics');dist,ix=tree.query(np.c_[f.geometry.x,f.geometry.y]);f['node']=surface[ix];f['connector_m']=dist;f['node_x']=xy[ix,0];f['node_y']=xy[ix,1];f['connector_review']=np.where(dist>50,'over_50m_review','short_proxy_not_field_verified')
f.to_file('data/processed/geography.gpkg',layer='clinics_connected',driver='GPKG');f.drop(columns='geometry').to_csv('data/processed/clinic_connectors.csv',index=False)
print('clinic connector distances',pd.Series(dist).describe().to_dict(),flush=True)
