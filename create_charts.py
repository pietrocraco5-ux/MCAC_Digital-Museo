from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from core import connection,dashboard
ROOT=Path(__file__).resolve().parent
with connection() as db: d=dashboard(db)
(ROOT/'dashboard_metrics.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
fig,ax=plt.subplots(figsize=(11,6.8))
rows=d['by_event']; labels=[r['title'] for r in rows][::-1]
vals=[r['occupancy_percent'] for r in rows][::-1]
bar=ax.barh(labels,vals,color='#3b806d',height=.68)
ax.set_xlim(0,100);ax.set_xlabel('Posti prenotati / capacità (%)');ax.set_title('Occupazione per evento (dataset simulato)',pad=16)
for b,v in zip(bar,vals):ax.text(v+1,b.get_y()+b.get_height()/2,f'{v:.1f}%',va='center',fontsize=9)
fig.subplots_adjust(left=.37,right=.94,top=.89,bottom=.13)
fig.savefig(ROOT/'grafico_occupazione.png',dpi=175);plt.close(fig)
fig,ax=plt.subplots(figsize=(8.5,4.8))
ratings=list(map(int,d['rating_distribution']));vals=list(d['rating_distribution'].values())
bar=ax.bar(ratings,vals,color=['#b9d6c2','#a9ccbb','#7baa93','#4b947a','#176457'],width=.58)
ax.set_xticks(ratings);ax.set_xlabel('Valutazione (1-5)');ax.set_ylabel('Numero feedback');ax.set_ylim(0,max(vals)+2)
ax.set_title('Distribuzione dei feedback (dataset simulato)',pad=15)
for b,v in zip(bar,vals):ax.text(b.get_x()+b.get_width()/2,v+.15,str(v),ha='center')
fig.tight_layout();fig.savefig(ROOT/'grafico_feedback.png',dpi=175);plt.close(fig)
fig,ax=plt.subplots(figsize=(8.5,5.1))
labels=[x['kind'] for x in d['by_kind']];vals=[x['seats'] for x in d['by_kind']]
bar=ax.bar(labels,vals,color=['#1d6155','#4f8979','#9dbfaf','#d1c39b'],width=.62)
for b,v in zip(bar,vals):ax.text(b.get_x()+b.get_width()/2,v+.4,str(v),ha='center')
ax.set_ylabel('Posti prenotati');ax.set_ylim(0,max(vals)+7)
ax.set_title('Domanda per tipologia di servizio (dataset simulato)',pad=15)
fig.tight_layout();fig.savefig(ROOT/'grafico_tipologie.png',dpi=175);plt.close(fig)
print('creati grafici / JSON; KPI:',{k:d[k] for k in ('users','works','events','bookings','seats_booked','total_capacity','occupancy_percent','feedback_count','rating_mean')})
