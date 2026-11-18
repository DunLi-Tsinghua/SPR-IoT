"""Publication exports with explicit source rows; no missing-to-zero conversion."""
import csv,hashlib,json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures/round4'
COLORS={'B0':'#777777','B1':'#A6761D','B2':'#999999','B3':'#CC79A7','B4':'#0072B2','SPR':'#009E73','B5':'#E69F00'}
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':9,'axes.titlesize':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'legend.frameon':False,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','axes.axisbelow':True})
def rows(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def number(x):
    if x is None or str(x).strip().lower() in ('','na','none','null','nan'):return None
    v=float(x)
    if not math.isfinite(v):return None
    return v
def boolean(x):
    if x in (True,'True','true','1',1):return True
    if x in (False,'False','false','0',0):return False
    return None
def export(fig,name,points,caption,sources):
    OUT.mkdir(parents=True,exist_ok=True)
    from matplotlib.text import Text
    for text in fig.findobj(match=Text):
        if text.get_fontsize()<8:text.set_fontsize(8)
    # Physical size remains fixed; constrained layout resolves panel labels.
    fig.savefig(OUT/(name+'.pdf'))
    fig.savefig(OUT/(name+'.svg'))
    fig.savefig(OUT/(name+'.png'),dpi=300)
    plt.close(fig)
    keys=list(dict.fromkeys(k for p in points for k in p))
    if not keys:raise ValueError('figure has no observed source data')
    with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(points)
    provenance=[]
    for p in sources:
        p=Path(p);provenance.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (OUT/(name+'.json')).write_text(json.dumps({'caption':caption,'sources':provenance,'rows':len(points),'dimensions_mm':[183,fig.get_figheight()*25.4],'font_pt':9,'missing_policy':'NA kept missing; observed zero retained'},indent=2),encoding='utf-8')
def panel(ax,label,title):
    ax.set_title(label+'  '+title,loc='left',pad=8)
def missing(ax,label='Not measured'):
    ax.text(.5,.5,label,transform=ax.transAxes,ha='center',va='center',color='#777777');ax.set_axis_off()
