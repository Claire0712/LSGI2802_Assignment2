import numpy as np,pandas as pd,json
from pathlib import Path
from scipy.sparse.csgraph import dijkstra
from graph_core import sparse_min
import geopandas as gpd
from shapely.geometry import LineString
z=np.load('data/processed/network_arrays.npz');xyz=z['xyz'];n=len(xyz);g=sparse_min(z['u'],z['v'],z['walk']/80+z['fixed'],n)
o=pd.read_csv('data/processed/origins.csv',dtype={'TPU':str});b=pd.read_csv('results/baseline_tpu.csv',dtype={'TPU':str});f=pd.read_csv('data/processed/clinic_connectors.csv');d=pd.read_csv('results/disagreement_cases.csv',dtype={'TPU':str})
valid=b[np.isfinite(b.M)].sort_values('TPU');picked=list(d.TPU)+list(valid.iloc[np.linspace(0,len(valid)-1,20,dtype=int)].TPU);picked=list(dict.fromkeys(picked))[:23]
rows=[];lines=[]
for code in picked:
 r=valid[valid.TPU==code].iloc[0];a=o[(o.TPU==code)&(o.choice==0)].iloc[0];clinic=f[f.OBJECTID==r.nearest_clinic_id].iloc[0]
 dist,pred=dijkstra(g,directed=True,indices=int(a.node),return_predecessors=True);target=int(clinic.node);path=[target]
 while path[-1]!=int(a.node):
  p=int(pred[path[-1]])
  if p<0:raise ValueError('Unreachable audit path')
  path.append(p)
 path=path[::-1];q=xyz[path];geom=LineString(q[:,:2]);straight=float(np.linalg.norm(q[0,:2]-q[-1,:2]));length=float(np.linalg.norm(np.diff(q,axis=0),axis=1).sum())
 assert abs(dist[target]+clinic.connector_m/80-r.M)<1e-6
 item=dict(TPU=code,clinic_id=int(clinic.OBJECTID),clinic=clinic.NameEN,time_min=r.M,path_vertices=len(path),route_length_m=length,straight_m=straight,detour=length/straight if straight else 1,z_min=float(q[:,2].min()),z_max=float(q[:,2].max()),connector_m=float(clinic.connector_m),largest_step_m=float(np.linalg.norm(np.diff(q,axis=0),axis=1).max()),review='geometry audit; entrance legality and indoor hours not field verified')
 rows.append(item);lines.append(geom);print('audit',code,round(r.M,1),flush=True)
pd.DataFrame(rows).to_csv('results/route_audit.csv',index=False);gpd.GeoDataFrame(rows,geometry=lines,crs=2326).to_file('output/Accessibility_Results.gpkg',layer='audit_routes',driver='GPKG')
# Geometric review atlas, using native network vertices in each extent as background.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from plot_fonts import configure_plot_font
configure_plot_font();plt.rcParams.update({'font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'pdf.fonttype':42})
fig,axes=plt.subplots(6,4,figsize=(12,16),dpi=200)
for ax,item,line in zip(axes.flat,rows,lines):
 x,y=line.xy;pad=max(100,(max(x)-min(x)+max(y)-min(y))*.06);bounds=(min(x)-pad,min(y)-pad,max(x)+pad,max(y)+pad)
 mask=(xyz[:,0]>=bounds[0])&(xyz[:,0]<=bounds[2])&(xyz[:,1]>=bounds[1])&(xyz[:,1]<=bounds[3]);ax.scatter(xyz[mask,0],xyz[mask,1],s=.15,color='#bbbbbb');ax.plot(x,y,color='#d2352c',lw=1.2);ax.scatter([x[0]],[y[0]],marker='o',s=18,color='#3C5488');ax.scatter([x[-1]],[y[-1]],marker='^',s=22,color='black');ax.set_aspect('equal');ax.set_axis_off();ax.set_title(f"TPU {item['TPU']} | {item['time_min']:.1f} min | detour {item['detour']:.1f}",fontsize=8)
for ax in axes.flat[len(rows):]:ax.set_visible(False)
fig.tight_layout();fig.savefig('figures/route_audit_atlas.png',dpi=200,bbox_inches='tight');plt.close(fig)
