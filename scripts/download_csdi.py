"""Snapshot CSDI REST layers, preserving native HK1980 geometry and Z."""
import urllib.request,urllib.parse,json,time,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('data/raw'); ROOT.mkdir(parents=True,exist_ok=True)
LAYERS={'clinics':('fhb_rcd_1637050485482_89683',0),'tpu':('pland_rcd_1634022783366_65050',0),'census':('censtatd_rcd_1635933365202_19171',0),'network':('landsd_rcd_1637222018065_52265',0)}
def get(url,params):
 u=url+'?'+urllib.parse.urlencode(params)
 for attempt in range(5):
  try:
   with urllib.request.urlopen(u,timeout=120) as r: d=json.load(r)
   if 'error' in d: raise ValueError(d['error'])
   return d
  except Exception:
   if attempt==4: raise
   time.sleep(2**attempt)
def download(name):
 sid,layer=LAYERS[name];base=f'https://portal.csdi.gov.hk/server/rest/services/common/{sid}/MapServer/{layer}'
 folder=ROOT/name;folder.mkdir(exist_ok=True)
 schema=get(base,{'f':'json'});(folder/'schema.json').write_text(json.dumps(schema))
 count=get(base+'/query',{'f':'json','where':'1=1','returnCountOnly':'true'})['count']
 batch=min(schema.get('maxRecordCount',3000),3000)
 ids=set(); manifest={'source':base,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'expected_count':count,'files':[]}
 for offset in range(0,count,batch):
  p=folder/f'page_{offset:07d}.json'
  if p.exists(): d=json.loads(p.read_text())
  else:
   d=get(base+'/query',dict(f='json',where='1=1',outFields='*',returnGeometry='true',returnZ='true',resultOffset=offset,resultRecordCount=batch,orderByFields='OBJECTID'))
   p.write_text(json.dumps(d,separators=(',',':')))
  rows=d.get('features',[])
  assert len(rows)==min(batch,count-offset),(name,offset,len(rows))
  for x in rows:
   oid=x['attributes']['OBJECTID'];assert oid not in ids;ids.add(oid)
  manifest['files'].append({'path':str(p),'records':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  print(name,offset+len(rows),'/',count,flush=True)
 assert len(ids)==count
 manifest['observed_count']=len(ids);(folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':
 import sys
 for n in sys.argv[1:] or LAYERS: download(n)
