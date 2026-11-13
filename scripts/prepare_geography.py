"""Convert native Esri geometries with ring orientation preserved by GDAL."""
from pathlib import Path
import json,geopandas as gpd,pandas as pd

def layer(name):
 frames=[gpd.read_file(p) for p in sorted(Path('data/raw',name).glob('page_*.json'))]
 return gpd.GeoDataFrame(pd.concat(frames,ignore_index=True),crs=frames[0].crs)
if __name__=='__main__':
 t=layer('tpu');t['TPU']=t.TPU.astype(int).astype(str);t.geometry=t.geometry.make_valid()
 t=t[['TPU','geometry']].dissolve(by='TPU').reset_index();assert len(t)==292
 t.to_file('data/processed/geography.gpkg',layer='tpu',driver='GPKG')
 c=layer('census');c.geometry=c.geometry.make_valid();c.to_file('data/processed/geography.gpkg',layer='census',driver='GPKG')
 f=layer('clinics');f['source_id']=f.OBJECTID
 # North Kwai Chung now co-located with Ha Kwai Chung. Count one destination site, not two capacity units.
 f=f[~f.OBJECTID.isin([1,47,65])].copy();f['location_note']='catalogue coordinate; entrance not field-verified'
 f.loc[f.OBJECTID==28,'location_note']='Ha Kwai Chung site also temporarily hosts North Kwai Chung; counted once'
 f.loc[f.OBJECTID==2,'location_note']='Tung Wah Eastern: temporary relocation within campus; catalogue point retained; exclusion sensitivity required'
 f.to_file('data/processed/geography.gpkg',layer='clinics',driver='GPKG')
 f.drop(columns='geometry').to_csv('data/processed/clinics.csv',index=False)
 print('TPUs',len(t),'census groups',len(c),'clinic sites',len(f),flush=True)
