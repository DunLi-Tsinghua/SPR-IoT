"""Three evidence groups from frozen CSV; no solver, broker or new experiment."""
from pathlib import Path
import sys,csv,json,argparse,statistics
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import round4_figure_utils as U
from round4_figure_utils import plt,rows,boolean,number,export
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter,MaxNLocator
S=ROOT/'results/body_results';P=rows(S/'offline_pressure.csv');F=rows(S/'offline_factors.csv');TP=rows(S/'offline_timing_pairs.csv');BP=rows(S/'broker_pairs.csv');BD=rows(S/'broker_e5_delivery.csv');MODEL=rows(ROOT/'figures/final/fig1_catalogue_traps.csv')
METHODS=['Greedy','B4_open','SPR_open'];N=dict(zip(METHODS,['Local Greedy (G)','Direct exact (E)','Exact + contextual quotient (Q)']));C=dict(zip(METHODS,['#BE5A17','#214E80','#007F7F']));LS=dict(zip(METHODS,['-.','-','--']));MK=dict(zip(METHODS,['^','o','s']));GRAY='#737D89';TEXT='#28323D';GRID='#DDE2E7'
plt.rcParams.update({'font.size':9,'axes.labelsize':9,'axes.titlesize':9,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'legend.fontsize':8.5,'text.color':TEXT,'axes.labelcolor':TEXT,'axes.edgecolor':TEXT,'xtick.color':TEXT,'ytick.color':TEXT,'axes.titlecolor':TEXT,'axes.linewidth':.7,'lines.linewidth':1.25,'savefig.facecolor':'white'})
def axes(ax,title,xlabel=None,ylabel=None):
 ax.set_title(title,loc='left',fontweight='bold',pad=9)
 if xlabel:ax.set_xlabel(xlabel)
 if ylabel:ax.set_ylabel(ylabel)
 ax.grid(axis='y',color=GRID,lw=.55);ax.set_axisbelow(True)
def handles():return [Line2D([],[],color=C[m],ls=LS[m],marker=MK[m],mfc='white' if m=='SPR_open' else C[m],label=N[m],ms=4.5) for m in METHODS]
def modrow(m,prop,dom):return next(r for r in MODEL if r['method']==m and r['obligation']==prop and r['domain']==dom)
def brokerrow(m,prop,dom):return next(r for r in BD if r['task']=='E1_K1_two_namespaces' and r['method']==m and r['label']==prop and r['domain']==dom and r['status']=='executed')
def communication():
 order=['B0','Legacy_exact_patch','Whitelist','Finite_quotient','Greedy','B4_open'];labels=['Original (O)','Exact deny (D)','Whitelist (W)','Finite quotient (F)','Local Greedy (G)','E/Q coincide'];out=[]
 fig=plt.figure(figsize=(183/25.4,94/25.4));gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.20],left=.145,right=.99,bottom=.23,top=.80,wspace=.23);a=fig.add_subplot(gs[0,0]);b=fig.add_subplot(gs[0,1],sharey=a);c=fig.add_subplot(gs[0,2])
 for ax,prop,letter,title in [(a,'required','a','Required delivered'),(b,'forbidden','b','Forbidden blocked')]:
  for i,m in enumerate(order):
   col=C.get(m,GRAY)
   for j,dom in enumerate(['Catalogue','Unseen challenge']):
    r=modrow(m,prop,dom);n=int(r['denominator']);v=int(r['obtained']);good=v if prop=='required' else n-v
    if m=='B4_open':
     q=modrow('SPR_open',prop,dom);assert (r['obtained'],r['denominator'])==(q['obtained'],q['denominator'])
    y=i+(j-.5)*.40
    ax.barh(y,good/n,height=.31,color='white' if j else col,edgecolor=col,lw=.8,hatch='///' if j else None)
    if good==0:ax.plot(0,y,marker='|',color=col,ms=6)
    ax.text(.025 if good==0 else .975,y,f'{good}/{n}',ha='left' if good==0 else 'right',va='center',fontsize=8.5,color=TEXT if j or good==0 else 'white',bbox=dict(facecolor='white' if j or good==0 else col,edgecolor='none',pad=.05))
    out.append(dict(r,panel=letter,fulfilled=good,denominator=n,fraction=good/n,metric='required_delivered' if prop=='required' else 'forbidden_blocked',coincident_raw_file=q.get('raw_file','') if m=='B4_open' else ''))
  ax.set_xlim(0,1.04);ax.set_ylim(5.65,-.65);ax.set_xticks([0,.5,1],['0','50','100']);ax.set_xlabel('Fulfilled (%)');ax.set_yticks(range(6),labels);ax.tick_params(axis='y',length=0);ax.grid(axis='x',color=GRID,lw=.5);ax.set_axisbelow(True);ax.set_title(letter+'  '+title,loc='left',fontsize=9,fontweight='bold',pad=12)
 b.tick_params(labelleft=False)
 # Broker cells retain their separate per-property/domain n=2, not pooled with model n=14.
 c.set_xlim(-1.10,3.5);c.set_ylim(3.2,-1.5);c.axis('off');c.set_title('c  Broker: two branches',loc='left',fontweight='bold',pad=12)
 c.text(.5,-.95,'Required\ndelivered',ha='center',fontsize=8.5);c.text(2.5,-.95,'Forbidden\nblocked',ha='center',fontsize=8.5)
 for j,lab in enumerate(['Cat.','New','Cat.','New']):c.text(j,-.50,lab,ha='center',fontsize=8.5)
 for i,(m,lab) in enumerate([('B0','O'),('Finite_quotient','F'),('B4_open','E/Q')]):
  c.text(-.72,i,lab,ha='center',va='center',fontsize=9)
  for j,(prop,dom) in enumerate([('required','catalog'),('required','challenge'),('forbidden','catalog'),('forbidden','challenge')]):
   r=brokerrow(m,prop,dom);n=int(r['topic_denominator']);v=int(r['topic_obtained']);good=v if prop=='required' else n-v;assert n==2
   if m=='B4_open':q=brokerrow('SPR_open',prop,dom);assert r['topic_obtained']==q['topic_obtained'] and r['topic_denominator']==q['topic_denominator']
   c.text(j,i,f'{good}/{n}',ha='center',va='center',fontsize=9,fontweight='bold' if good==0 else 'normal');out.append(dict(r,panel='c',fulfilled=good,denominator=n,fraction=good/n,metric='required_delivered' if prop=='required' else 'forbidden_blocked'))
  c.plot([-.45,3.45],[i+.5,i+.5],color=GRID,lw=.65)
 c.plot([1.5,1.5],[-.7,2.5],color=GRID,lw=.8)
 c.text(1.3,3.0,'Executed snapshots only;\n2 topics in each domain/property.',ha='center',va='center',fontsize=8.5)
 fig.text(.43,.945,'Model checks: catalogue n=2; challenge n=14 per property',ha='center',fontsize=9)
 from matplotlib.patches import Patch
 fig.legend(handles=[Patch(facecolor=GRAY,edgecolor=GRAY,label='Catalogue'),Patch(facecolor='white',edgecolor=GRAY,hatch='///',label='Challenge')],loc='lower center',bbox_to_anchor=(.38,.03),ncol=2)
 export(fig,'01_communication',out,'Model required-delivered and forbidden-blocked counts use separate catalogue n=2 and challenge n=14 denominators. Bars compare categorical methods without connecting them. Broker panel shows only executed two-branch O/F/E/Q snapshots, each cell n=2; E/Q counts are checked equal before merging. F loses required challenges, while exact-topic Deny misses forbidden descendants in the model. No unexecuted method row is drawn.',[ROOT/'figures/final/fig1_catalogue_traps.csv',S/'broker_e5_delivery.csv'])
def mechanisms():
 # A compact accounting matrix replaces three three-point, coincident curves.
 fig,ax=plt.subplots(figsize=(183/25.4,79/25.4));fig.subplots_adjust(left=.015,right=.99,bottom=.09,top=.88);ax.set_xlim(0,1);ax.set_ylim(-.5,11.8);ax.invert_yaxis();ax.axis('off');out=[]
 xs=[.005,.215,.335,.465,.58,.70,.815,.94]
 headers=['Condition','Slot\noptions','Cap-bounded\nassignments','Invalid\nassignments','Language\nchecks','Not\nvisited','Exact\nedits','G\noutcome']
 for x,h in zip(xs,headers):ax.text(x,.05,h,ha='left' if x==xs[0] else 'center',va='center',fontsize=8.5,fontweight='bold')
 ax.plot([0,1],[.75,.75],color=TEXT,lw=.8)
 y=1.3
 for axis,name,levels in [('edit_cap','Edit cap',[1,2,3]),('inert_rule_atoms','Inert rule atoms',[0,2,4]),('overlap_density','Overlap level',[1,2,3])]:
  ax.text(.005,y,name,fontsize=9,fontweight='bold',va='center');ax.plot([.18,1],[y,y],color=GRID,lw=.65);y+=.80
  for level in levels:
   e=next(r for r in F if r['experiment']=='E3S' and r['axis']==axis and r['level']==str(level) and r['method']=='B4_open');q=next(r for r in F if r['task']==e['task'] and r['method']=='SPR_open');g=next(r for r in F if r['task']==e['task'] and r['method']=='Greedy')
   keys=['full_alternatives','full_combinations_with_cap','invalid_combinations','checks','cost_operations','status'];assert all(e[k]==q[k] for k in keys)
   total=int(e['full_combinations_with_cap']);rejected=int(e['invalid_combinations']);checked=int(e['checks']);notvisited=total-rejected-checked;assert notvisited>=0
   vals=[str(level),e['full_alternatives'],str(total),str(rejected),str(checked),str(notvisited),e['cost_operations'] if e['joint']=='True' else 'Infeasible','Complete' if g['joint']=='True' else 'Stalled']
   for j,(x,v) in enumerate(zip(xs,vals)):ax.text(x+(.10 if j==0 else 0),y,v,ha='left' if j==0 else 'center',va='center',fontsize=9,color=C['Greedy'] if j==7 else C['B4_open'] if j==4 else TEXT,fontweight='bold' if j==4 else 'normal')
   for m,r in [('B4_open',e),('SPR_open',q),('Greedy',g)]:out.append(dict(r,panel=axis,plotted_workload=checked if m!='Greedy' else '',metric='checked_deployable_policies' if m!='Greedy' else 'outcome_only',unvisited_assignments=notvisited if m!='Greedy' else '',derivation='full_combinations_with_cap - invalid_combinations - checks' if m!='Greedy' else ''))
   y+=.84
 ax.plot([0,1],[y-.30,y-.30],color=TEXT,lw=.8)
 fig.text(.5,.97,'Direct exact (E) / Exact + contextual quotient (Q): counts and optima coincide',ha='center',va='top',fontsize=9)
 fig.text(.5,.015,'Assignments = invalid + checked + not visited; all assignments are still generated and sorted.',ha='center',va='bottom',fontsize=8.5)
 export(fig,'02_mechanisms',out,'Search accounting on nine frozen conditions in three independent families. Slot options include unchanged/absent choices. Cap-bounded assignments partition into deployment-rejected, language-checked and not-yet-visited assignments; search stops at the first optimal feasible assignment or exhausts the declared space. E/Q counters and optima coincide. Infeasible is not zero cost; G outcomes are separate from its incomparable score count. Template completion totals remain in the text.',[S/'offline_factors.csv'])

def ecdf(ax,values,label,color=GRAY,ls='-',mk='o'):
 xs=sorted(values);ys=np.arange(1,len(xs)+1)/len(xs);ax.step([xs[0]]+xs,[0]+list(ys),where='post',color=color,ls=ls,lw=1.2,label=label);ax.plot(xs,ys,ls='none',marker=mk,ms=4,mfc='white',mec=color)
def cost():
 fig,ax=plt.subplots(1,3,figsize=(183/25.4,97/25.4));fig.subplots_adjust(left=.09,right=.985,bottom=.27,top=.83,wspace=.31);out=[]
 for m in METHODS:
  rr=sorted([r for r in P if r['method']==m and r['joint']=='True'],key=lambda r:float(r['parent_wall_seconds']));xs=[float(r['parent_wall_seconds'])*1000 for r in rr];ys=np.arange(1,len(rr)+1)/36
  ax[0].step([0]+xs,[0]+list(ys),where='post',color=C[m],ls=LS[m],lw=1.4);ax[0].plot(xs,ys,ls='none',marker=MK[m],ms=2.7,mfc='white' if m=='SPR_open' else C[m],mec=C[m])
  for r,y in zip(rr,ys):out.append(dict(r,panel='a',metric='complete_fraction',fraction=float(y),denominator=36,parent_ms=float(r['parent_wall_seconds'])*1000))
 ax[0].set_xticks([0,2000,4000],['0','2,000','4,000']);axes(ax[0],'a  Observed completion','Full parent time (ms)','Complete repairs / 36');ax[0].text(.02,.96,'G: 30/36\nE/Q: 34/36',transform=ax[0].transAxes,va='top',fontsize=8.5)
 for task,name,ls,mk in [('E1_K1_two_namespaces','Branches (5)','-','o'),('E3_s1_n2_seed17','Overlap (5)','--','s'),('E4_nested_3','Demand (5)',':','D')]:
  rr=[r for r in TP if r['task']==task and r['complete_pair']=='True'];assert len(rr)==5;ecdf(ax[1],[1000*float(r['parent_difference_seconds']) for r in rr],name,ls=ls,mk=mk)
  for r in rr:out.append(dict(r,panel='b',metric='Q_minus_E_parent_ms',difference=1000*float(r['parent_difference_seconds'])))
 axes(ax[1],'b  Q − E computation','Time difference (ms)','Fraction of complete pairs');ax[1].set_xticks([-20,0,20,40,60]);ax[1].axvline(0,color=TEXT,ls=':',lw=.7);ax[1].legend(loc='lower right',fontsize=8.5,handlelength=1.3)
 for task,name,ls,mk in [('E1_K1_two_namespaces','Branches (5)','-','o'),('E3_s1_n2_seed17','Overlap (5)','--','s')]:
  rr=[r for r in BP if r['task']==task and r['complete_business_pair']=='True'];assert len(rr)==5;ecdf(ax[2],[float(r['delta_latency_median_ms']) for r in rr],name,ls=ls,mk=mk)
  for r in rr:out.append(dict(r,panel='c',metric='repaired_minus_original_run_median_delay_ms',difference=float(r['delta_latency_median_ms'])))
 axes(ax[2],'c  Broker: repair − original','Median-delay change (ms)');ax[2].set_xticks([-.05,0,.1],['−0.05','0','0.10']);ax[2].axvline(0,color=TEXT,ls=':',lw=.7);ax[2].legend(loc='lower right',fontsize=8.5,handlelength=1.3)
 for a in ax:a.set_ylim(0,1.025);a.set_yticks([0,.5,1]);a.yaxis.set_major_formatter(PercentFormatter(1))
 fig.legend(handles=handles(),loc='upper center',bbox_to_anchor=(.53,.995),ncol=3)
 ax[1].text(.5,-.36,f"15 pairs; median {statistics.median(1000*float(r['parent_difference_seconds']) for r in TP if r['complete_pair']=='True'):+.3f} ms",transform=ax[1].transAxes,ha='center',fontsize=8.5);ax[2].text(.5,-.36,f"10 pairs; median {statistics.median(float(r['delta_latency_median_ms']) for r in BP if r['complete_business_pair']=='True'):+.5f} ms",transform=ax[2].transAxes,ha='center',fontsize=8.5)
 export(fig,'03_complete_cost',out,'Observed historical completion fractions retain denominator 36, not hypothetical budget reruns. The offline ECDFs use all fifteen complete paired Q−E parent differences (three representatives, five each); five both-timeout pairs have no values. Broker ECDFs use ten complete original/repaired pairs (two representatives, five each); per-run median delays summarize nested messages. Original policies have weaker safety, and unmatched originals are excluded from differences. All curves are empirical unsmoothed steps.',[S/'offline_pressure.csv',S/'offline_timing_pairs.csv',S/'broker_pairs.csv'])
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'figures/redesign_20261103');args=ap.parse_args();U.OUT=args.output.resolve();communication();mechanisms();cost()
