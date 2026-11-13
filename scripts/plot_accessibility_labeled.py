"""Restyle the existing accessibility map, preserving data and class boundaries."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import geopandas as gpd
import pandas as pd
from matplotlib import font_manager
from plot_fonts import configure_plot_font
from matplotlib.patches import Patch, Rectangle
ROOT = Path(__file__).resolve().parents[1]
configure_plot_font()
plt.rcParams.update({'font.sans-serif':['Arial','DejaVu Sans'], 'axes.unicode_minus':False,
 'font.size':10, 'pdf.fonttype':42, 'svg.fonttype':'none', 'mathtext.fontset':'custom',
 'mathtext.rm':'Arial', 'mathtext.it':'Arial:italic', 'mathtext.bf':'Arial:bold', 'mathtext.default':'regular'})
b = pd.read_csv(ROOT/'results/baseline_tpu.csv',dtype={'TPU':str})
t = gpd.read_file(ROOT/'data/processed/geography.gpkg',layer='tpu').merge(b,on='TPU',how='left')
t.geometry = t.geometry.simplify(12,preserve_topology=True)
warm = ['#f7ecd9','#edc994','#dba065','#bb7045','#88432e']
cool = ['#e6efed','#b8d5d0','#7eb4b0','#438c91','#205e6c']
specs = [
 ('M','Nearest clinic','Travel time (min)',[0,5,15,30,60,np.inf],['0–5','5–15','15–30','30–60','>60'],warm),
 ('C15','Clinics within reach','Number within 15 min',[-.1,0,1,2,4,np.inf],['0','1','2','3–4','≥5'],cool),
 ('G15','Gravity accessibility','Opportunity score',[-.1,.1,.5,1,2,np.inf],['0–0.1','0.1–0.5','0.5–1','1–2','>2'],cool)]

from matplotlib import patheffects
from pyproj import Transformer
blue = ['#dfebf3','#accbe0','#73a7ca','#397daa','#14517c']
transformer=Transformer.from_crs('EPSG:4326',t.crs,always_xy=True)
for style in ['paper_labels']:
 atlas=style=='atlas'
 ink='#243d50'
 fig=plt.figure(figsize=(13.2,4.65 if not atlas else 5.2),dpi=300,facecolor='white')
 for i,(key,title,subtitle,edges,labels,_) in enumerate(specs):
  left=.025+i*.329
  colors=blue[::-1] if key=='M' else blue
  ax=fig.add_axes([left,.22,.31,.66])
  if atlas:
   ax.set_facecolor('#edf2f3')
   ax.tick_params(left=False,bottom=False,labelleft=False,labelbottom=False)
   for spine in ax.spines.values():spine.set_visible(False)
  t.plot(ax=ax,color='#d9d9d6',edgecolor='#b8c2c7',linewidth=.15)
  finite=t[np.isfinite(t[key])].copy()
  finite['class']=pd.cut(finite[key],edges,labels=False,include_lowest=True)
  for j,col in enumerate(colors):
   sub=finite[finite['class']==j]
   if len(sub):sub.plot(ax=ax,color=col,edgecolor='#fafcfd',linewidth=.18)
  inf=t[np.isinf(t[key])]
  if len(inf):inf.plot(ax=ax,color='#88939a',edgecolor='white',linewidth=.2,hatch='////' if atlas else None)
  ax.set_xlim(800000,865000);ax.set_ylim(800000,848000)
  ax.set_xlabel('');ax.set_ylabel('')
  if not atlas:ax.set_axis_off()
  if True:
   for name,lon,lat in [('NEW TERRITORIES',114.12,22.46),('KOWLOON',114.18,22.33),('HONG KONG ISLAND',114.20,22.25),('LANTAU ISLAND',113.96,22.25)]:
    x,y=transformer.transform(lon,lat)
    ax.text(x,y,name,ha='center',va='center',fontsize=6.5,color='#354955',weight='medium',path_effects=[patheffects.withStroke(linewidth=2.8,foreground='white',alpha=.9)])
   x,y=transformer.transform(114.27,22.19)
   ax.text(x,y,'South China Sea',fontsize=7,color='#8a9da6',style='italic',ha='center')
  fig.text(left,.94,chr(97+i),fontsize=12,weight='bold',color=ink)
  fig.text(left+.021,.94,title,fontsize=11.5,weight='bold',color=ink)
  fig.text(left+.021,.895,subtitle,fontsize=9,color='#75838b')
  ax.annotate('',xy=(861000,843000),xytext=(861000,840000),arrowprops={'arrowstyle':'-|>','color':ink,'lw':.7})
  ax.text(861000,844000,'N',ha='center',fontsize=7,color=ink)
  ax.plot([845000,855000],[802000,802000],color=ink,lw=.9)
  ax.text(850000,803200,'10 km',ha='center',fontsize=7,color=ink)
  leg=fig.add_axes([left+.01,.115,.29,.07]);leg.set_axis_off()
  for j,(col,label) in enumerate(zip(colors,labels)):
   leg.add_patch(Rectangle((j/5,.54),.197,.32,facecolor=col,edgecolor='none'))
   leg.text((j+.49)/5,.12,label,ha='center',va='center',fontsize=8,color=ink)
 handles=[Patch(facecolor='#d9d9d6',label='Unresolved origin'),Patch(facecolor='#88939a',hatch='////' if atlas else None,label='No network route (travel time)')]
 fig.legend(handles=handles,loc='lower left',bbox_to_anchor=(.025,.006),ncol=2,frameon=False,fontsize=8,labelcolor='#75838b',handlelength=1.3,columnspacing=2)
 fig.text(.97,.04,'Darker blue = better accessibility',ha='right',fontsize=8,color='#526f83')
 for ext in ['png','pdf','svg']:
  fig.savefig(ROOT/f'figures/accessibility_maps_{style}_v2.{ext}',dpi=300,bbox_inches='tight',pad_inches=.13)
 plt.close(fig)
 print('Saved',style)
