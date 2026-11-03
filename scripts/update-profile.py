"""Atualiza SVGs com dados públicos; não consulta repositórios privados."""
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime,date,timedelta,timezone
import urllib.request,json,html,os,math,shutil
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'assets'
USER=os.environ.get('PROFILE_USERNAME','netooochiico')
class Calendar(HTMLParser):
 def __init__(self):super().__init__();self.days={};self.counts={};self.tip=None;self.parts=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='td' and 'data-date' in a and 'data-level' in a:self.days[a['id']]={'date':a['data-date'],'level':int(a['data-level'])}
  if tag=='tool-tip' and a.get('for','').startswith('contribution-day-'):self.tip=a['for'];self.parts=[]
 def handle_data(self,s):
  if self.tip:self.parts.append(s)
 def handle_endtag(self,tag):
  if tag=='tool-tip' and self.tip:
   import re
   m=re.match(r'([\d,]+) contributions?',''.join(self.parts).strip())
   self.counts[self.tip]=int(m[1].replace(',','')) if m else 0;self.tip=None

def fetch(url,api=False):
 h={'User-Agent':'netooochiico-profile/2','Accept':'application/vnd.github+json' if api else 'text/html'}
 token=os.environ.get('GH_TOKEN')
 if api and token:h['Authorization']='Bearer '+token
 with urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=35) as r:return r.read().decode()
def text(x,y,s,size=14,color='#94a3b8',weight='normal',extra=''):
 return f'<text x="{x}" y="{y}" fill="{color}" font-family="DejaVu Sans,sans-serif" font-size="{size}" font-weight="{weight}" {extra}>{html.escape(str(s))}</text>'
def image(name,w,h,body):
 (ASSETS/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="#0d111b" stroke="#30304a"/>{body}</svg>')
def pending(name,title,line):
 image(name,900,150,text(30,40,title,17,'#c4b5fd','bold')+text(30,82,line,16)+text(30,120,'As métricas são exibidas conforme os dados públicos disponíveis.',12,'#64748b'))
def main():
 stamp=datetime.now(timezone.utc).strftime('%d/%m/%Y')
 cache=ROOT/'.source-calendar.html'
 source=cache.read_text() if os.environ.get('USE_LOCAL_CALENDAR') and cache.exists() else fetch(f'https://github.com/users/{USER}/contributions')
 parser=Calendar();parser.feed(source)
 days=sorted([dict(v,count=parser.counts.get(k,0)) for k,v in parser.days.items()],key=lambda d:d['date'])
 if len(days)<300:raise RuntimeError('Calendário incompatível: as imagens anteriores foram preservadas.')
 total=sum(d['count'] for d in days);streak=best=0
 for d in days:
  streak=streak+1 if d['count'] else 0;best=max(best,streak)
 tail=days[:-1] if days[-1]['count']==0 else days
 current=0
 for d in reversed(tail):
  if not d['count']:break
  current+=1
 today=date.today()
 if (today-date.fromisoformat(tail[-1]['date'])).days>1:current=0
 profile=json.loads(fetch(f'https://api.github.com/users/{USER}',True))
 repos=json.loads(fetch(f'https://api.github.com/users/{USER}/repos?per_page=100&sort=updated',True))
 stars=sum(r['stargazers_count'] for r in repos);forks=sum(r['forks_count'] for r in repos)
 body=text(28,38,'GITHUB STATS',17,'#c4b5fd','bold')
 for i,(label,value) in enumerate([('Repositórios públicos',profile['public_repos']),('Contribuições exibidas',total),('Estrelas recebidas',stars),('Seguidores',profile['followers'])]):
  y=87+i*39;body+=text(30,y,label,16)+text(450,y,value,18,'#67e8f9','bold',extra='text-anchor="end"')
 body+=text(30,273,'Dados públicos · '+stamp,11,'#64748b')
 image('stats.svg',480,294,body)
 body=text(28,38,'CONTRIBUTION STREAK',17,'#c4b5fd','bold')
 for x,n,label,col in [(83,total,'Contribuições','#c4b5fd'),(241,current,'Sequência atual','#67e8f9'),(395,best,'Maior sequência','#c4b5fd')]:
  body+=text(x,130,n,44,col,'bold',extra='text-anchor="middle"')+text(x,171,label,12,extra='text-anchor="middle"')
 body+=text(240,232,'Dias consecutivos com contribuições públicas',11,'#64748b',extra='text-anchor="middle"')+text(240,271,stamp,10,'#64748b',extra='text-anchor="middle"')
 image('streak.svg',480,294,body)
 # Language composition uses byte counts; never substitutes private-project technologies.
 langs={}
 for repo in repos:
  if repo['fork'] or repo['archived']:continue
  for lang,n in json.loads(fetch(repo['languages_url'],True)).items():langs[lang]=langs.get(lang,0)+n
 if not langs:
  pending('languages.svg','TOP LANGUAGES','Ainda não há código público suficiente para calcular a distribuição.')
 else:
  colors=['#a78bfa','#67e8f9','#f472b6','#c4b5fd','#34d399','#fbbf24'];top=sorted(langs.items(),key=lambda p:-p[1])[:6];s=sum(n for _,n in top)
  body=text(30,37,'TOP LANGUAGES',17,'#c4b5fd','bold');x=30
  for i,(lang,n) in enumerate(top):
   w=840*n/s;body+=f'<rect x="{x:.2f}" y="65" width="{w:.2f}" height="12" fill="{colors[i]}"/>';x+=w
   body+=text(30+(i%3)*280,112+(i//3)*28,f'{lang} · {n/s:.1%}',14,colors[i])
  image('languages.svg',900,188,body)
 # Last 31 days: exact daily counts, SVG plot with date and scale.
 last=days[-31:];maxn=max(1,max(d['count'] for d in last));w=1100;h=300
 body=text(30,37,'ACTIVITY GRAPH / ÚLTIMOS 31 DIAS',16,'#c4b5fd','bold')
 left,right,top,bottom=55,1065,65,233
 for k in range(4):
  y=bottom-(bottom-top)*k/3;body+=f'<path d="M{left} {y}H{right}" stroke="#20283b" stroke-dasharray="3 6"/>'+text(42,y+4,round(maxn*k/3,1),10,'#64748b',extra='text-anchor="end"')
 pts=[(left+i*(right-left)/30,bottom-d['count']/maxn*(bottom-top)) for i,d in enumerate(last)]
 coords=' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
 body+=f'<polygon points="{left},{bottom} {coords} {right},{bottom}" fill="#7c3aed" fill-opacity=".10"/><polyline points="{coords}" fill="none" stroke="#67e8f9" stroke-width="2.5" stroke-linejoin="round"/>'
 for i,(x,y) in enumerate(pts):
  body+=f'<circle cx="{x}" cy="{y}" r="3" fill="#c4b5fd"><title>{last[i]["date"]}: {last[i]["count"]}</title></circle>'
  if i%5==0:body+=text(x,260,last[i]['date'][5:],10,'#64748b',extra='text-anchor="middle"')
 body+=text(1065,286,'Atualizado em '+stamp,10,'#64748b',extra='text-anchor="end"');image('activity.svg',w,h,body)
 # Initial contribution snake uses the public grid. The official snk action refreshes it.
 first=date.fromisoformat(days[0]['date']);start=first-timedelta(days=(first.weekday()+1)%7);lastcol=(date.fromisoformat(days[-1]['date'])-start).days//7;columns=lastcol+1
 colors=['#1b2030','#3b2864','#633b98','#9765d7','#bca0f5'];body=''
 for d in days:
  delta=(date.fromisoformat(d['date'])-start).days;col,row=divmod(delta,7);x=25+col*19;y=28+row*19
  idx=col*7+(row if col%2==0 else 6-row);t=(idx+1)/(columns*7+1)
  fade=f'<animate attributeName="opacity" values="1;0.12;1" keyTimes="0;{t:.6f};1" calcMode="discrete" dur="38s" repeatCount="indefinite"/>' if d['count'] else ''
  body+=f'<rect x="{x}" y="{y}" width="13" height="13" rx="3" fill="{colors[d["level"]]}">{fade}<title>{d["date"]}: {d["count"]} contribuições</title></rect>'
 path=[]
 for col in range(columns):
  for row in (range(7) if col%2==0 else reversed(range(7))):path.append((31.5+col*19,34.5+row*19))
 route='M'+' L'.join(f'{x},{y}' for x,y in path)
 for seg in range(5,0,-1):
  body+=f'<rect x="-6" y="-6" width="12" height="12" rx="3" fill="'+('#67e8f9' if seg==1 else '#a78bfa')+f'" opacity="{1-seg*.07}"><animateMotion dur="38s" begin="{seg*.13}s" repeatCount="indefinite" path="{route}"/></rect>'
 image('snake.svg',1060,185,body)
 if not (ASSETS/'trophies.svg').exists():pending('trophies.svg','GITHUB TROPHIES','Sincronização inicial: execute o workflow Profile Update no GitHub Actions.')
 print('SVGs atualizados com dados públicos:',{'contribuicoes':total,'repositorios':profile['public_repos'],'linguagens':len(langs)})
if __name__=='__main__':main()
