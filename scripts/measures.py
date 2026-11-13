import numpy as np
def indices(t,tau=15,h=15):
 t=np.asarray(t,dtype=float);missing=np.isnan(t).any(axis=1)
 m=np.min(t,axis=1);c=np.sum(t<=tau,axis=1).astype(float);g=np.sum(np.exp(-np.log(2)*t/h),axis=1)
 for a in (m,c,g):a[missing]=np.nan
 return m,c,g
def low_set(x,q=.2):
 x=np.asarray(x);valid=~np.isnan(x)
 if not valid.any():return set()
 cutoff=np.quantile(x[valid],q,method='inverted_cdf')
 return set(np.where(valid&(x<=cutoff))[0])
