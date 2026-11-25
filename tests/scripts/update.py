"""Status-only aggregator. Never downloads game binaries or project source code."""
import os,json,re,hashlib,urllib.request,urllib.parse,datetime,concurrent.futures,pathlib,html,copy
from bs4 import BeautifulSoup
import audit
ROOT=pathlib.Path(__file__).resolve().parents[1]; DATA=ROOT/'site/data/state.json'
RACE='https://vuyp.github.io/gta6-pc-race/'
PORT='https://portwatch-vi.xyz/data/tracker.json'
PORT_FALLBACK='https://raw.githubusercontent.com/4lwayz/portwatch-vi/main/data/tracker.json'
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
def key(s):
 s=re.sub(r'[^a-z0-9]','',str(s).lower()); return {'zettrox':'ztrx','victorygta6':'victoryfork','fivestarrecomp':'fivestarrecomp','marvis':'victory'}.get(s,s)
def safeurl(s):
 if not isinstance(s,str):return ''
 try:
  u=urllib.parse.urlsplit(s);return s if u.scheme in ('https','http') and u.hostname and not u.username and not u.password else ''
 except ValueError:return ''
def fetch(u):
 h={'User-Agent':'PC-Radar-Status/4.0','Accept':'application/json' if 'api.github.com' in u else '*/*'}
 if u.startswith('https://api.github.com/') and os.getenv('GITHUB_TOKEN'): h['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
 with urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=18) as r: return r.read(8_000_001).decode('utf-8')
def api(path): return json.loads(fetch('https://api.github.com/'+path))
def project_key(projects,k,item):
 repo=item.get('repo','').lower()
 if repo:
  matches=[x for x,v in projects.items() if v.get('repo','').lower()==repo]
  if matches:return matches[0]
  if k in projects and projects[k].get('repo') and projects[k]['repo'].lower()!=repo:return k+'-'+ident(repo)[:10]
 return k
def ghrepo(u):
 m=re.fullmatch(r'https://github\.com/([\w.-]+/[\w.-]+)/?',u or ''); return m.group(1) if m else ''
def ident(*args): return hashlib.sha256('|'.join(map(str,args)).encode()).hexdigest()[:20]
def event(source,title,when='',url='',project='',category='动态',note='',eid=None):
 return dict(id=eid or ident(source,project,title),source=source,title=str(title)[:360],when=when or NOW,url=safeurl(url),project=project,category=category,note=note)
def category(t):
 for pattern,name in [(r'dmca|takedown|copyright|下架','版权动态'),(r'crash|stability|hang|稳定','稳定性'),(r'fps|performance|帧率|optim','性能'),(r'shader|render|lighting|texture|渲染','图形'),(r'mission|gameplay|controller|input|任务','玩法'),(r'boot|loader|menu|启动','启动')]:
  if re.search(pattern,t,re.I):return name
 return '开发动态'
def port_reference_score(e):
 # Reimplementation of publicly documented PortWatch scoring, not our own index.
 g=e.get('gta') or {}; gw=e.get('groundwork') or {}
 def clamp(v):
  try:
   x=float(v);return min(1,max(0,x)) if __import__('math').isfinite(x) else 0
  except (ValueError,TypeError):return 0
 value=10*sum(w*clamp(gw.get(k)) for k,w in [('loader',.2),('shaders',.28),('graphics',.32),('proven',.2)])
 complete=True
 for j,k in enumerate(('loads','boots','menu','world','playable'),1):
  f=clamp(g.get(k));value=max(value,value+f*(j*10-value))
  if f<1:complete=False;break
 if complete:value=50+50*(.35*clamp(g.get('story'))+.25*clamp(g.get('render'))+.2*clamp((audit.number(g.get('fps'),100000) or 0)/30)+.2*(audit.stability_fraction(g.get('stability')) or 0))
 if type(e.get('manualScore')) in (int,float) and __import__('math').isfinite(e['manualScore']):value=min(100,max(0,e['manualScore']))
 return round(value+1e-10,1)

def port_rankings(efforts):
 entries=[e for e in efforts if e.get('tier')=='tracked' and not e.get('nuked') and isinstance(e.get('repo'),str) and '/' in e['repo']]
 entries.sort(key=lambda e:(-port_reference_score(e),-(audit.number((e.get('stats') or {}).get('stars'),10**9) or 0)))
 return {str(e.get('id')):i+1 for i,e in enumerate(entries)}

def port_parse(data):
 if not isinstance(data.get('efforts'),list):raise ValueError('PortWatch schema changed')
 p={}; ev=[]; ranks=port_rankings(data['efforts'])
 for e in data['efforts']:
  name=e.get('name') or e.get('id'); k=key(name); g=e.get('gta') or {}; repo=e.get('repo') or ''
  if not name:continue
  stage=6 if g.get('world')==1 or g.get('playable')==1 else 5 if g.get('menu')==1 else 2 if g.get('boots')==1 else 1 if g.get('loads')==1 else 0
  repo=repo if isinstance(repo,str) and re.fullmatch(r'[\w.-]+/[\w.-]+',repo) else ''
  k=project_key(p,k,{'repo':repo});p[k]=dict(name=name,repo=repo,port=dict(stage=stage,assessment=e.get('assessedAt') or data.get('updated'),verification=e.get('verification','unknown'),fps=g.get('fps'),world=g.get('world'),playable=g.get('playable'),gpu=[x for x in (e.get('gpu') or []) if x in ('AMD','NVIDIA','Intel')],reference_score=port_reference_score(e),reference_rank=ranks.get(str(e.get('id'))),archived=bool((e.get('stats') or {}).get('archived')),unavailable=bool(e.get('nuked') or (e.get('stats') or {}).get('missing')),story=g.get('story'),render=g.get('render'),stability=g.get('stability'),tier=e.get('tier'),basedOn=e.get('basedOn',[]),url='https://portwatch-vi.xyz/#effort-'+str(e.get('id','')),note=str(e.get('summary') or e.get('evidence') or '')[:1500]))
 for n in data.get('news',[]):
  title=n.get('title',''); detail=str(n.get('summary') or n.get('description') or n.get('body') or ''); ev.append(event('PortWatch',title,n.get('date'), 'https://portwatch-vi.xyz/',category=category(title+' '+detail),note=detail[:1500],eid=ident('port-news',n.get('id') or title,detail)))
 for n in data.get('dmca',[]):ev.append(event('PortWatch','公开版权通知',n.get('date'),n.get('url'),category='版权动态',eid=ident('dmca',n.get('path'))))
 return p,ev,data.get('updated')
def race_metrics(text,stage):
 out={'fps':None,'fps_basis':None,'control':None,'minutes':None,'note':'Conservative extraction; not a joint-test verification.'}
 if stage<6:return out
 text=' '.join(text.split());text=re.split(r'Source:',text,flags=re.I)[0]
 text=re.sub(r'^.*?\d+ steps? short of the playable bar\s*','',text,flags=re.I)
 averages=[]; ranges=[]
 for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z])',text):
  # Avoid attribution to another project/build and unconfirmed proposals.
  if re.search(r'pull request|contributor.s report|candidate build|other builds|reports built on|earlier build|another project',sentence,re.I):continue
  gameplay=bool(re.search(r'gameplay|game world|open world|in the world|opening mission|prison scene|opening scenes|first room|play session|free roam|driving|walking|under player control',sentence,re.I))
  if gameplay and not re.search(r'target|expected|aims? for|could reach|not yet|hypothetical|estimated|projected',sentence,re.I):
   # Prefer explicit session averages. A range uses its lower bound, not its peak.
   for m in re.finditer(r'(?:averag(?:ing|ed)\s+(?:about\s+)?(\d+(?:\.\d+)?)\s+(?:over|during) (?:the |its )?session|(\d+(?:\.\d+)?)\s*(?:frames? (?:a|per) second|fps)?\s+on average)',sentence,re.I):
    v=float(m.group(1) or m.group(2));
    if 0<v<=240:averages.append(v)
   if not re.search(r'cutscene|standing still|window caption|menu|static view|lightest view|peak|up to|target|expected|aims? for|could reach|not yet',sentence,re.I):
    for m in re.finditer(r'(?:at|about)\s+(?:about\s+)?(\d+(?:\.\d+)?)(?:\s*(?:to|[–—-])\s*(\d+(?:\.\d+)?))?\s*(?:rendered )?(?:frames? (?:a|per) second|fps)\b',sentence,re.I):
     v=float(m.group(1));
     if 0<v<=240:ranges.append(v)
  if re.search(r'player (?:can walk|moving around|can move)|under player control|character under control|whole opening mission playable|mission[s]? (?:played|completed)|free roam.*(?:driving|walking)|player in control',sentence,re.I) and not re.search(r'cannot|not playable|unverified',sentence,re.I):out['control']=True
  if re.search(r'without a crash|without crashing|crash.free|closed by hand|ended by choice|closed on request',sentence,re.I) and not re.search(r'cutscene|menu only|earlier build|not crash.free|not without|never reached|target|expected|aims? for|could run',sentence,re.I):
   for m in re.finditer(r'(\d+)\s*hour[s]?\s*(?:(\d+)\s*minute[s]?)?|\b(\d+)\s*[-– ]?minute[s]?\b',sentence,re.I):
    v=int(m.group(1))*60+int(m.group(2) or 0) if m.group(1) else int(m.group(3));
    if 0<v<=100000:out['minutes']=max(out['minutes'] or 0,v)
 if averages:out['fps']=min(averages);out['fps_basis']='session_average'
 elif ranges:out['fps']=min(ranges);out['fps_basis']='reported_lower_bound'
 return out

NUMBER_WORDS={'a':1,'an':1,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,'half':0.5}
def race_forecast(page):
 soup=BeautifulSoup(page,'html.parser'); h=next((x for x in soup.find_all(['h2','h3']) if 'time to playable' in x.get_text(' ',strip=True).lower()),None)
 if not h:return None
 parts=[]
 for el in h.next_elements:
  if getattr(el,'name',None) in ('h2','h3'):break
  if isinstance(el,str):parts.append(str(el).strip())
 text=' '.join(parts); num=r'(?:\d+(?:\.\d+)?|'+ '|'.join(NUMBER_WORDS)+r')'
 m=re.search(r'\b(?:(about|around|roughly|approximately|under|over|less than|more than|within|at least|up to)\s+)?('+num+r')(?:\s*(?:–|—|-|to)\s*('+num+r'))?\s+(hours?|days?|weeks?|months?)\b',text,re.I)
 if not m:return None
 def n(x):return str(NUMBER_WORDS.get(x.lower(),x))
 qualifier=(m.group(1) or '').lower(); unit=m.group(4).lower(); normalized=(qualifier+' ' if qualifier else '')+n(m.group(2))+('–'+n(m.group(3)) if m.group(3) else '')+' '+unit
 d=re.search(r'Around[^.]{1,90}\.',text,re.I)
 checked=re.search(r'Checked\s+(.{1,40}?)\s+on\s+(\d+\s+\w+)',soup.get_text(' ',strip=True),re.I)
 return {'text':normalized,'raw_text':m.group(0),'date_text':d.group(0) if d else '', 'as_of':NOW,'upstream_checked':checked.group(0) if checked else '', 'url':RACE+'#forecast','status':'ok','note':'External estimate; as_of is retrieval time, not publication time.'}

def race_parse(page):
 soup=BeautifulSoup(page,'html.parser'); p={};ev=[]; headings=soup.find_all(['h2','h3']); mode=''; checked=''
 text=soup.get_text(' ',strip=True); m=re.search(r'Checked\s+(.{1,40}?)\s+on\s+(\d+\s+\w+)',text,re.I); checked=m.group(0) if m else ''
 if checked:
  # The upstream check omits a year; preserve its literal text.
  checked=checked.strip()
 for h in headings:
  title=h.get_text(' ',strip=True)
  if h.name=='h2':
   mode='standings' if 'standings' in title.lower() else 'updates' if title.lower()=='updates' else '';continue
  if mode=='standings':
   chunks=[]
   for el in h.next_elements:
    if getattr(el,'name',None) in ('h2','h3'):break
    if isinstance(el,str):chunks.append(str(el).strip())
   t=' '.join(x for x in chunks if x); m=re.search(r'Stage\s*(\d)\s*(?:of|/)\s*7',t,re.I)
   if not m:continue
   link=h.find('a',href=True); repo=ghrepo(link['href']) if link else ''
   # Extract only from the project's own report, never from fork/PR/cutscene clauses.
   st=int(m.group(1)); metrics=race_metrics(t,st)
   p[project_key(p,key(title),{'repo':repo})]=dict(name=title,repo=repo,race=dict(stage=st,reference_rank=len(p)+1,url=RACE,assessment=checked,verification='第三方汇总',note=t[:460],metrics=metrics,halted=bool(re.search(r'\bhalted since\b|\bproject (?:is|was) halted\b|\bdevelopment (?:has )?(?:stopped|ceased)\b|\bbuild has been taken down\b',t,re.I)),unavailable=bool(re.search(r'\b(?:repo(?:sitory)?|GitHub (?:repo(?:sitory)?|page)) (?:is |now |has |no longer )*(?:unavailable|not responding|stopped responding|stopped answering|no longer answers|returns? (?:a )?404|deleted|gone|inaccessible)\b',t,re.I))))
  elif mode=='updates':
   if title:
    parts=[]
    for el in h.next_elements:
     if getattr(el,'name',None) in ('h2','h3'):break
     if isinstance(el,str):parts.append(str(el).strip())
    detail=' '.join(parts);ev.append(event('PC Race',title,'',RACE+'#updates',category=category(title+' '+detail),note=detail[:1500],eid=ident('race-update',title,detail)))
 if not p:raise ValueError('PC Race standings not recognized')
 return p,ev,checked

def github_repo(repo):
 try:r=api('repos/'+repo)
 except Exception as e:raise RuntimeError('Repository metadata: '+str(e)) from e
 commits=api('repos/'+repo+'/commits?per_page=30'); prs=api('repos/'+repo+'/pulls?state=all&sort=updated&direction=desc&per_page=20'); ev=[]
 for c in commits:
  msg=c['commit']['message'].splitlines()[0];ev.append(event('GitHub commit',msg,c['commit']['committer']['date'],c.get('html_url'),repo,category(msg),eid=ident(repo,c['sha'])))
 for pr in prs:
  title=pr['title']; status='merged' if pr.get('merged_at') else pr['state']; ev.append(event('GitHub PR',title,pr.get('updated_at'),pr.get('html_url'),repo,category(title),note='PR '+status+' · 提案或合并记录，不等于实测突破',eid=ident(repo,'pr',pr['number'],pr.get('updated_at'))))
 return dict(pushed=r.get('pushed_at'),stars=r.get('stargazers_count'),archived=r.get('archived'),fork=r.get('fork'),repo=r.get('full_name'),checked=NOW),ev

def discover():
 queries=['"GTA VI" recompilation in:name,description,readme','"GTA 6" PC port in:name,description,readme','"GTA6" compatibility in:name,description,readme']; out={}; success=0
 for q in queries:
  try:
   results=api('search/repositories?'+urllib.parse.urlencode({'q':q,'sort':'updated','per_page':30}));success+=1
   for r in results.get('items',[]):
    out[r['full_name'].lower()]=dict(name=r['name'],repo=r['full_name'],url=r['html_url'],updated=r['pushed_at'],description=str(r.get('description') or '')[:300])
  except Exception:
   if not success and q==queries[-1]:raise
 if not success:raise RuntimeError('All discovery queries failed')
 return list(out.values())
def rule_analysis(e):
 return {'性能':'涉及速度变化；需要核对游戏内 FPS、硬件及统计口径。','稳定性':'涉及运行稳定性；需要核对持续时长及是否发生崩溃。','图形':'涉及画面输出；不代表完整图形管线或可玩性已解决。','玩法':'涉及交互或任务；需要可重复的实机证据。','版权动态':'涉及权利人或平台措施；以公开原始通知为准。','启动':'涉及启动或界面；不能证明进入可操控世界。'}.get(e['category'],'发现公开更新；尚未据此提高技术阶段。')
def main():
 state=json.loads(DATA.read_text(encoding='utf8')); projects=state['projects']; events={e['id']:e for e in state['events']}; health=state.get('health',{}); candidates=state.get('candidates',[])
 audit.init(state,state.get('forecast',{}).get('as_of') or NOW)
 if not audit.verify(state['ledger']):raise ValueError('Audit ledger failed integrity check; refusing to overwrite')
 old={k:audit.view(v,stored=True) for k,v in projects.items()};old_event_ids=set(events);old_candidates={c['repo'].lower() for c in candidates if c.get('repo')}; old_forecast=state.get('forecast',{});old_health={k:v.get('status') for k,v in health.items()}
 def merge(source,parser,url):
  try:
   try:raw=fetch(url)
   except Exception:
    if source!='PortWatch':raise
    raw=fetch(PORT_FALLBACK)
   incoming,ev,ts=parser(json.loads(raw) if source=='PortWatch' else raw)
   if not incoming:raise ValueError('No projects returned; preserving prior observations')
   src_key='race' if source=='PC Race' else 'port'
   prior_count=sum(1 for v in projects.values() if v.get(src_key,{}).get('listing')=='listed')
   if prior_count>=8 and len(incoming)<prior_count/2:raise ValueError('Unexpectedly incomplete standings; preserving prior observations')
   seen=set();src_key='race' if source=='PC Race' else 'port'
   for k,item in incoming.items():
    # reconcile repos across sources, prefer canonical slug when identical
    match=project_key(projects,k,item)
    existing=projects.setdefault(match,{}); existing.update({a:b for a,b in item.items() if b not in ('',None)}); existing['last_seen']=NOW;seen.add(match);existing[src_key]['listing']='listed'
   for k,p in projects.items():
    if k not in seen and p.get(src_key):p[src_key]['listing']='not_listed_in_latest_successful_scan'
   for e in ev:events.setdefault(e['id'],e)
   if source=='PC Race':
    forecast=race_forecast(raw)
    if forecast:
     previous=state.get('forecast',{})
     forecast['first_observed']=previous.get('first_observed',previous.get('as_of',NOW)) if all(previous.get(k)==forecast.get(k) for k in ('text','date_text')) else NOW
     state['forecast']=forecast
    else:state['forecast']={**state.get('forecast',{}),'status':'unparsed','checked':NOW}
   health[source]={'status':'ok','checked':NOW,'upstream':ts,'count':len(incoming)}
  except Exception as e:
   health[source]={**health.get(source,{}),'status':'error','checked':NOW,'error':str(e)[:180]}
   if source=='PC Race':state['forecast']={**state.get('forecast',{}),'status':'source_error','checked':NOW}
 merge('PortWatch',port_parse,PORT);merge('PC Race',race_parse,RACE)
 if os.getenv('GITHUB_TOKEN') or os.getenv('RADAR_SCAN_UNAUTH')=='1':
  repos=list(dict.fromkeys(v['repo'] for v in projects.values() if v.get('repo'))); limit=15 if os.getenv('GITHUB_TOKEN') else 1; start=int(state.get('repo_cursor',0))%max(1,len(repos));repos=(repos[start:]+repos[:start])[:limit];state['repo_cursor']=start+len(repos); ok=0;errors=0
  with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
   jobs={pool.submit(github_repo,r):r for r in repos}
   for f in concurrent.futures.as_completed(jobs):
    r=jobs[f]; p=next(v for v in projects.values() if v.get('repo')==r)
    try:
     p['github'],ev=f.result();p.pop('github_error',None);p.pop('github_error_at',None);ok+=1
     for e in ev:events.setdefault(e['id'],e)
    except Exception as e:
     p['github_error']=str(e)[:180];p['github_error_at']=NOW;errors+=1
  health['GitHub']={'status':'ok' if ok and not errors else 'partial' if ok else 'error','checked':NOW,'count':ok,'errors':errors,'scheduled':len(repos)}
  try:
   discovered=discover();candidates=audit.candidates_merge(candidates,discovered,NOW,projects);health['Discovery']={'status':'ok','checked':NOW,'count':len(discovered)}
  except Exception as e:health['Discovery']={'status':'error','checked':NOW,'error':str(e)[:180]}
 else:health['GitHub']={'status':'disabled','checked':NOW};health['Discovery']={'status':'disabled','checked':NOW}
 candidates=audit.candidates_merge(candidates,[],NOW,projects)
 # A failed scan is not fresh evidence. Preserve historical observations, flag their source.
 for p in projects.values():
  for src,label in [('race','PC Race'),('port','PortWatch')]:
   if p.get(src):p[src]['source_health']=health.get(label,{}).get('status','unknown')
 audit.changes(state,old,NOW)
 state['audit_policy']=audit.POLICY
 for c in candidates:
  if c['repo'].lower() not in old_candidates:audit.append(state,'candidate',c['repo'],None,c,NOW)
 for e in events.values():
  e.setdefault('analysis',rule_analysis(e));e.setdefault('first_seen',NOW if e['id'] not in old_event_ids else None)
  if e['id'] not in old_event_ids:audit.append(state,'event',e.get('project') or e['source'],None,e,NOW)
 if {k:v for k,v in old_forecast.items() if k not in ('as_of','checked','upstream_checked')}!={k:v for k,v in state.get('forecast',{}).items() if k not in ('as_of','checked','upstream_checked')}:audit.append(state,'forecast','PC Race',old_forecast,state.get('forecast'),NOW)
 for src,h in health.items():
  if old_health.get(src)!=h.get('status'):audit.append(state,'source_status',src,old_health.get(src),h.get('status'),NOW)
 # append only; preserve all previously seen events. Snapshot stages without invented FPS extrapolation.
 history=state.get('history',[]); counts=[sum(1 for p in projects.values() if p.get('race',{}).get('stage')==i) for i in range(1,8)]
 history.append({'at':NOW,'projects':len(projects),'stages':counts,'source_ok':sum(h['status']=='ok' for h in health.values()),'leader_strict':max((p['audit_score']['strict'] for p in projects.values() if p['audit_score'].get('eligible',True)),default=0),'ledger_count':len(state['ledger'])});
 state.update(projects=projects,events=sorted(events.values(),key=lambda e:e.get('when',''),reverse=True),health=health,candidates=candidates,history=history,checked=NOW,mode='自动扫描结果（可能部分失败）')
 tmp=DATA.with_suffix('.tmp');tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8');tmp.replace(DATA)
 print('projects',len(projects),'events',len(events),'sources',health)
if __name__=='__main__':main()
