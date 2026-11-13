from pathlib import Path
import json,itertools,hashlib
import numpy as np,pandas as pd
from scipy.sparse.csgraph import dijkstra
from scipy.stats import spearmanr,rankdata
from graph_core import sparse_min
from measures import indices,low_set
z=np.load('data/processed/network_arrays.npz');n=len(z['xyz']);o=pd.read_csv('data/processed/origins.csv',dtype={'TPU':str});f=pd.read_csv('data/processed/clinic_connectors.csv');valid=o.node.notna();nodes=o.loc[valid,'node'].astype(int).to_numpy()
fingerprint=hashlib.sha256()
for fp in ['data/processed/network_arrays.npz','data/processed/origins.csv','data/processed/clinic_connectors.csv','scripts/measures.py','scripts/graph_core.py','scripts/analyse.py']:
 fingerprint.update(Path(fp).read_bytes())
signature=fingerprint.hexdigest()
summary={};baseline=None
for name,speed,alpha,unknown in [('baseline',80,0,0),('slow',50,0,0),('uncovered25',80,.25,0),('uncovered50',80,.5,0),('uncovered50_upper',80,.5,1)]:
 out=Path(f'results/od_{name}.npy')
 meta=out.with_suffix('.sha256')
 if out.exists() and meta.exists() and meta.read_text()==signature:od=np.load(out)
 else:
  exposed=(z['cover']==2)|((z['cover']==3)&bool(unknown))
  graph=sparse_min(z['u'],z['v'],z['walk']/speed*(1+alpha*exposed)+z['fixed'],n).T.tocsr()
  od=np.full((len(o),len(f)),np.nan)
  for j,r in enumerate(f.itertuples()):
   dist=dijkstra(graph,directed=True,indices=int(r.node));od[valid,j]=dist[nodes]+r.connector_m/speed
   if j%10==0:print(name,j,'/',len(f),flush=True)
  np.save(out,od);meta.write_text(signature)
 m,c,g=indices(od);frame=o[['TPU','origin_id','choice','status']].copy();frame['M']=m;frame['C15']=c;frame['G15']=g
 frame['nearest_clinic_id']=np.where(np.isfinite(m),f.OBJECTID.to_numpy()[np.nanargmin(np.where(np.isnan(od),np.inf,od),axis=1)],np.nan)
 frame.to_csv(f'results/accessibility_{name}.csv',index=False)
 base=frame[frame.choice==0].copy();summary[name]={'TPUs':len(base),'resolved':int(base.M.notna().sum()),'reachable':int(np.isfinite(base.M).sum()),'disconnected':int(np.isinf(base.M).sum()),'C15_zero':int((base.C15==0).sum()),'median_M_finite':float(base.loc[np.isfinite(base.M),'M'].median()),'median_C15':float(base.C15.median()),'median_G15':float(base.G15.median())}
 if name=='baseline':baseline=base;baseline_od=od
 else:
  bo=pd.read_csv('results/accessibility_baseline.csv');assert np.all(m[valid]>=bo.M.to_numpy()[valid]-1e-7);assert np.all(c[valid]<=bo.C15.to_numpy()[valid]);assert np.all(g[valid]<=bo.G15.to_numpy()[valid]+1e-9)
  summary[name]['lost_all_C15']=int(((baseline.C15.to_numpy()>0)&(base.C15.to_numpy()==0)).sum())
  summary[name]['median_G_loss_pct']=float(np.median(100*(1-base.loc[baseline.G15>0,'G15'].to_numpy()/baseline.loc[baseline.G15>0,'G15'].to_numpy())))
# Common reachable sample for correlations; complete origins incl disconnected for sets.
b=baseline.reset_index(drop=True);x={'M':-b.M.to_numpy(),'C15':b.C15.to_numpy(),'G15':b.G15.to_numpy()};common=np.isfinite(b.M)&b.C15.notna()&b.G15.notna();rows=[]
sets={k:low_set(v) for k,v in x.items()}
for a,bb in itertools.combinations(x,2):
 rho=float(spearmanr(x[a][common],x[bb][common]).statistic);union=sets[a]|sets[bb]
 rows.append(dict(measure_a=a,measure_b=bb,n=int(common.sum()),spearman=rho,low_a=len(sets[a]),low_b=len(sets[bb]),jaccard=len(sets[a]&sets[bb])/len(union) if union else np.nan))
pd.DataFrame(rows).to_csv('results/comparison.csv',index=False)
# Percentile ranks among common reachable origins; full ties retained.
ranks=pd.DataFrame({k:pd.Series(v).where(common).rank(pct=True,method='average') for k,v in x.items()});b['rank_range']=ranks.max(axis=1)-ranks.min(axis=1)
b.sort_values(['rank_range','TPU'],ascending=[False,True]).head(3).to_csv('results/disagreement_cases.csv',index=False)
for k,s in sets.items():b['low_'+k]=b.index.isin(s)
b.to_csv('results/baseline_tpu.csv',index=False)
# Threshold, decay and origin sensitivity, reusing unchanged OD.
mask=o.choice.to_numpy()==0;param=[]
for tau in (10,15,20,30):
 _,cc,_=indices(baseline_od,tau=tau);param.append(dict(type='threshold',value=tau,zero_TPUs=int((cc[mask]==0).sum()),median=float(np.nanmedian(cc[mask]))))
for h in (10,15,20):
 _,_,gg=indices(baseline_od,h=h);param.append(dict(type='half_life',value=h,zero_TPUs=int((gg[mask]==0).sum()),median=float(np.nanmedian(gg[mask]))))
pd.DataFrame(param).to_csv('results/parameter_sensitivity.csv',index=False)
a=pd.read_csv('results/accessibility_baseline.csv',dtype={'TPU':str});origin=a.groupby('TPU').agg(n_origins=('M','count'),min_M=('M','min'),max_M=('M','max'),min_C15=('C15','min'),max_C15=('C15','max'),min_G15=('G15','min'),max_G15=('G15','max'));origin['crosses_C15_zero']=(origin.min_C15==0)&(origin.max_C15>0);origin.to_csv('results/origin_sensitivity.csv')
summary['origin_sensitivity']={'TPUs_with_alternatives':int((origin.n_origins>1).sum()),'cross_zero':int(origin.crosses_C15_zero.sum())}
# Within-campus relocation uncertainty and connector tolerance.
checks=[]
for name,keep in [('exclude_Tung_Wah_Eastern',f.OBJECTID!=2),('connectors_at_most_50m',f.connector_m<=50),('connectors_at_most_100m',f.connector_m<=100)]:
 mm,cc,gg=indices(baseline_od[:,keep]);checks.append(dict(scenario=name,sites=int(keep.sum()),zero_C15=int((cc[mask]==0).sum()),median_M=float(np.nanmedian(np.where(np.isinf(mm[mask]),np.nan,mm[mask]))),median_G15=float(np.nanmedian(gg[mask]))))
pd.DataFrame(checks).to_csv('results/facility_sensitivity.csv',index=False)
assert np.all((b.C15.to_numpy()==0)[b.M.notna()]==(b.M.to_numpy()>15)[b.M.notna()])
Path('results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True);print(pd.DataFrame(rows),flush=True)
