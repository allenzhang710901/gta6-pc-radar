"""Evidence-only scoring and append-only observation ledger. No game files accessed."""
import hashlib,json,copy,math
POLICY='6.0'
WEIGHTS={'stage':20,'fps':20,'render':20,'story':15,'stability':15,'control':10}
STAGES=[0,3,6,9,12,15,20,20]
STABILITY={'constant':0,'often':.25,'sometimes':.55,'rarely':.8,'stable':1}
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def number(x,hi):return x if type(x) in (int,float) and math.isfinite(x) and 0<x<=hi else 0
def fraction(x):
 return float(x) if type(x) in (int,float) and math.isfinite(x) and 0<=x<=1 else None
def stability_fraction(x):
 return STABILITY.get(x) if isinstance(x,str) else fraction(x)
def score(p):
 options=[]
 for src in ('race','port'):
  d=p.get(src) or {}; st=d.get('stage',0) if d.get('listing')!='not_listed_in_latest_successful_scan' else 0; st=min(6,st) if type(st)==int and 0<=st<=7 else 0
  if not st:continue
  m=d.get('metrics') or {} if src=='race' else {}
  fps=number(m.get('fps') if src=='race' else d.get('fps'),240) if st==6 else 0
  minutes=number(m.get('minutes'),100000) if st==6 else 0
  control=(m.get('control') is True if src=='race' else d.get('playable') in (1,True)) if st==6 else False
  render=fraction(d.get('render')) if src=='port' and st==6 else None
  story=fraction(d.get('story')) if src=='port' and st==6 else None
  stability=stability_fraction(d.get('stability')) if src=='port' and st==6 else min(minutes/30,1) if minutes else None
  observed=src=='port' and d.get('verification')=='portwatch'
  # PortWatch says it observed a build; not our own test or independent reproduction.
  factor=.75 if observed else .60
  basis=m.get('fps_basis') if src=='race' else 'upstream_rating'
  dimensions={'stage':STAGES[st],'fps':20*min(fps/20,1) if fps else None,'render':20*render if render is not None else None,'story':15*story if story is not None else None,'stability':15*stability if stability is not None else None,'control':10 if control else None}
  components={k:round(v*(min(factor,.55) if k=='fps' and basis!='session_average' else factor),3) for k,v in dimensions.items() if v is not None}
  raw=min(99,round(sum(v for v in dimensions.values() if v is not None)))
  strict=math.floor(sum(components.values()))
  options.append(dict(source=src,stage=st,reported=raw,strict=strict,source_health=d.get('source_health','unknown'),fps=fps or None,fps_basis=basis,minutes=minutes or None,control=control,confidence='B · 外部观察声明' if observed else 'C · 第三方转述',evidence_grade='B' if observed else 'C',dimensions=dimensions,components=components,coverage=sum(WEIGHTS[k] for k,v in dimensions.items() if v is not None),url=d.get('url',''),note=d.get('note',''),missing=['同一构建、同一测试的独立可复核证据']+(['持续游戏内20 FPS'] if fps<20 else [])+(['连续30分钟无崩溃'] if minutes<30 else [])+(['可控角色'] if not control else [])))
 result=copy.deepcopy(max(options,key=lambda x:(x['strict'],x['reported'],x['stage'],x['source_health']=='ok'),default=dict(source='',stage=0,reported=0,strict=0,fps=None,minutes=None,control=False,confidence='U · 未知',evidence_grade='U',dimensions={k:None for k in WEIGHTS},components={},coverage=0,url='',note='',missing=['无可评分证据'])))
 # Never combine two sources into a synthetic same-build test.
 current=lambda src:p.get(src,{}) if p.get(src,{}).get('listing')!='not_listed_in_latest_successful_scan' else {}
 halted=bool(current('race').get('halted') or current('port').get('archived') or p.get('github',{}).get('archived'))
 unavailable=bool(current('race').get('unavailable') or current('port').get('unavailable') or (p.get('github_error') and 'Repository metadata: HTTP Error 404' in p['github_error']))
 listed=any(current(src) for src in ('race','port'))
 status='paused' if halted else 'unavailable' if unavailable else 'unlisted' if not listed else 'unverified' if not result['stage'] else 'tracked'
 result.update(halted=halted,status=status,eligible=status=='tracked',policy=POLICY,playable=False,alternatives=options)
 return result

def view(p,stored=False):
 scored=copy.deepcopy(p.get('audit_score')) if stored and p.get('audit_score') else score(p)
 out={'name':p.get('name'),'repo':p.get('repo',''),'status':scored.get('status','paused' if scored['halted'] else 'tracked'),'score':scored}
 for src in ('race','port'):
  if p.get(src):out[src]={k:v for k,v in p[src].items() if k not in ('assessment',)}
 if p.get('github'):out['repository']={k:v for k,v in p['github'].items() if k not in ('checked','stars')}
 return out

def append(state,kind,project,before,after,at):
 ledger=state.setdefault('ledger',[])
 row=dict(seq=len(ledger)+1,at=at,kind=kind,project=project,before=copy.deepcopy(before),after=copy.deepcopy(after),prev=ledger[-1]['hash'] if ledger else 'GENESIS')
 row['hash']=digest(row);ledger.append(row);return row

def verify(ledger):
 prev='GENESIS'
 for i,r in enumerate(ledger,1):
  payload={k:v for k,v in r.items() if k!='hash'}
  if r.get('seq')!=i or r.get('prev')!=prev or r.get('hash')!=digest(payload):return False
  prev=r['hash']
 return True

def init(state,at):
 if 'ledger' in state:return
 state['ledger']=[]
 for k,p in sorted(state['projects'].items()):append(state,'baseline',k,None,view(p),at)
 state['audit_policy']=POLICY

def changes(state,old,at):
 for k,p in sorted(state['projects'].items()):
  before=old.get(k);after=view(p)
  if before!=after:append(state,'project_added' if before is None else 'project_changed',k,before,after,at)
  p['audit_score']=score(p)

def candidates_merge(old,new,at,projects):
 known={p.get('repo','').lower() for p in projects.values() if p.get('repo')}
 result={c['repo'].lower():dict(c) for c in old if c.get('repo')}
 for c in new:
  k=c['repo'].lower(); prev=result.get(k,{})
  result[k]={**prev,**c,'first_seen':prev.get('first_seen',at),'last_seen':at}
 for k,c in result.items():c['status']='tracked' if k in known else 'candidate'
 return sorted(result.values(),key=lambda c:(c['status']=='candidate',c.get('last_seen','')),reverse=True)
