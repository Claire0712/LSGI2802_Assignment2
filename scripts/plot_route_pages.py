"""Replot the existing 23 audited routes as two A4-portrait appendix figures."""
import numpy as np
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from plot_fonts import configure_plot_font
configure_plot_font()
plt.rcParams.update({'font.sans-serif':['Arial','DejaVu Sans'],'font.size':9,'pdf.fonttype':42})
a=gpd.read_file('output/Accessibility_Results.gpkg',layer='audit_routes')
xyz=np.load('data/processed/network_arrays.npz')['xyz']
for page,start in enumerate([0,12],1):
 fig,axes=plt.subplots(4,3,figsize=(7.1,9.0))
 part=a.iloc[start:start+12]
 for ax,(_,r) in zip(axes.flat,part.iterrows()):
  x,y=r.geometry.xy;pad=max(100,(max(x)-min(x)+max(y)-min(y))*.06)
  mask=(xyz[:,0]>=min(x)-pad)&(xyz[:,0]<=max(x)+pad)&(xyz[:,1]>=min(y)-pad)&(xyz[:,1]<=max(y)+pad)
  ax.scatter(xyz[mask,0],xyz[mask,1],s=.12,color='#bbbbbb')
  ax.plot(x,y,color='#d2352c',lw=1)
  ax.scatter(x[0],y[0],marker='o',s=15,color='#3C5488')
  ax.scatter(x[-1],y[-1],marker='^',s=18,color='black')
  ax.set_aspect('equal');ax.set_axis_off()
  ax.set_title(f"TPU {r.TPU} | {r.time_min:.1f} min\ndetour {r.detour:.1f}",fontsize=8)
 for ax in axes.flat[len(part):]:ax.set_visible(False)
 fig.subplots_adjust(left=.025,right=.975,bottom=.025,top=.945,hspace=.5,wspace=.15)
 fig.savefig(f'figures/route_audit_portrait_page_{page}.png',dpi=300,bbox_inches='tight')
 plt.close(fig)
print('Replotted all',len(a),'routes')
