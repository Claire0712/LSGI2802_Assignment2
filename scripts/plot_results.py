import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib import font_manager
from plot_fonts import configure_plot_font
configure_plot_font()
plt.rcParams.update({'font.sans-serif':['Arial','DejaVu Sans'],'axes.unicode_minus':False,'font.size':10,'pdf.fonttype':42,'mathtext.fontset':'custom','mathtext.rm':'Arial','mathtext.it':'Arial:italic','mathtext.bf':'Arial:bold','mathtext.default':'regular'})
import geopandas as gpd,pandas as pd
from matplotlib.patches import Patch
from pathlib import Path
b=pd.read_csv('results/baseline_tpu.csv',dtype={'TPU':str});t=gpd.read_file('data/processed/geography.gpkg',layer='tpu');t=t.merge(b,on='TPU',how='left');t.geometry=t.geometry.simplify(12,preserve_topology=True)
# Same extent; ranks make direction comparable but colour bars state their distinct native measures.
fig,axes=plt.subplots(1,3,figsize=(11,4.5),dpi=300)
for k,ax in zip(['M','C15','G15'],axes):
 t.plot(ax=ax,color='#eeeeee',edgecolor='#bbbbbb',linewidth=.15)
 finite=t[np.isfinite(t[k])].copy()
 if k=='M':
  edges=[0,5,15,30,60,np.inf];labels=['0–5','5–15','15–30','30–60','>60'];colors=['#edf8fb','#b3cde3','#8c96c6','#8856a7','#810f7c']
 elif k=='C15':
  edges=[-.1,0,1,2,4,np.inf];labels=['0','1','2','3–4','≥5'];colors=['#810f7c','#8856a7','#8c96c6','#b3cde3','#edf8fb']
 else:
  # Explicit fixed opportunity-score classes, not fitted quantiles.
  edges=[-.1,.1,.5,1,2,np.inf];labels=['0–0.1','0.1–0.5','0.5–1','1–2','>2'];colors=['#810f7c','#8856a7','#8c96c6','#b3cde3','#edf8fb']
 finite['class']=pd.cut(finite[k],edges,labels=False,include_lowest=True)
 for j,col in enumerate(colors):
  sub=finite[finite['class']==j]
  if len(sub):sub.plot(ax=ax,color=col,edgecolor='white',linewidth=.12)
 inf=t[np.isinf(t[k])]
 if len(inf):inf.plot(ax=ax,color='#333333',edgecolor='white',linewidth=.12)
 ax.set_xlim(800000,865000);ax.set_ylim(800000,848000);ax.set_axis_off()
 title={'M':'a  Nearest time (min)','C15':'b  Clinics within 15 min','G15':'c  Gravity opportunity score'}[k]
 ax.text(.01,1.02,title,transform=ax.transAxes,fontweight='bold')
 handles=[Patch(facecolor=col,label=lab) for col,lab in zip(colors,labels)]+[Patch(facecolor='#eeeeee',label='Unresolved origin')]
 if k=='M':handles.append(Patch(facecolor='#333333',label='No network route'))
 ax.legend(handles=handles,loc='upper left',bbox_to_anchor=(0,-.03),fontsize=8,frameon=False,ncol=2)
 ax.plot([845000,855000],[802000,802000],color='black',lw=1.2);ax.text(850000,803000,'10 km',ha='center',fontsize=7)
 ax.annotate('N',xy=(861000,843000),xytext=(861000,837000),ha='center',arrowprops={'arrowstyle':'->'},fontsize=8)
fig.tight_layout();fig.savefig('figures/accessibility_maps.png',dpi=300,bbox_inches='tight');fig.savefig('figures/accessibility_maps.pdf',dpi=300,bbox_inches='tight');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(8,3.4),dpi=300)
a=b[np.isfinite(b.M)];sc=axes[0].scatter(a.M,a.G15,c=a.C15,cmap='viridis',s=18,alpha=.8,edgecolors='none');axes[0].set_xscale('log');axes[0].set_xlabel('Nearest time (min; log scale)');axes[0].set_ylabel('Gravity opportunity score');fig.colorbar(sc,ax=axes[0],label='Clinics within 15 min')
cases=pd.read_csv('results/disagreement_cases.csv',dtype={'TPU':str})
for r in cases.itertuples():axes[0].annotate(r.TU if hasattr(r,'TU') else r.TPU,(r.M,r.G15),fontsize=8,xytext=(3,4),textcoords='offset points')
s=pd.read_csv('results/accessibility_slow.csv',dtype={'TPU':str});s=s[s.choice==0];s=b.merge(s[['TPU','G15','C15']],on='TPU',suffixes=('_base','_slow'));v=s.G15_base>0
axes[1].scatter(s.loc[v,'G15_base'],s.loc[v,'G15_slow'],s=16,color='#3C5488',alpha=.7);lim=max(s.G15_base.max(),.1);axes[1].plot([0,lim],[0,lim],'--',color='#777777',lw=1);axes[1].set_xlabel('Baseline gravity score');axes[1].set_ylabel('Slow-walking gravity score')
for i,ax in enumerate(axes):
 ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',linestyle='--',alpha=.2);ax.text(0,1.04,chr(97+i),transform=ax.transAxes,fontweight='bold')
fig.tight_layout();fig.savefig('figures/comparison.png',dpi=300,bbox_inches='tight');fig.savefig('figures/comparison.pdf',dpi=300,bbox_inches='tight');plt.close(fig)
# GIS results preserve complete TPU geography with missing values.
t.to_file('output/Accessibility_Results.gpkg',layer='tpu_results',driver='GPKG')
