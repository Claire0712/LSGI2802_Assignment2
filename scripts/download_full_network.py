"""Official full-data distribution, preferred over paginated REST for the large network."""
from pathlib import Path
import urllib.request,zipfile
url='https://static.csdi.gov.hk/csdi-webpage/download/d0317d97c6755968809308308a768bcb/fgdb'
p=Path('data/raw/3DPN_full.zip');p.parent.mkdir(parents=True,exist_ok=True)
if not p.exists():
 with urllib.request.urlopen(url,timeout=180) as r, p.with_suffix('.partial').open('wb') as out:
  while chunk:=r.read(1024*1024):out.write(chunk)
 p.with_suffix('.partial').rename(p)
dest=Path('data/raw/network_full').resolve()
with zipfile.ZipFile(p) as z:
 for member in z.namelist():
  if not (dest/member).resolve().is_relative_to(dest):raise ValueError('Unsafe archive path')
 z.extractall(dest)
print(dest)
