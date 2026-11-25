"""Evidence-only scoring and append-only observation ledger. No game files accessed."""
import hashlib,json,copy,math
BASE=[0,5,12,22,35,50,65,65]
POLICY='5.2'
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def number(x,hi):return x if type(x) in (int,float) and math.isfinite(x) and 0<x<=hi else 0
def score(p):
 options=[]
 for src in ('race','port'):
  d=p.get(src) or {}; st=d.get('stage',0) if d.get('listing')!='not_listed_in_latest_successful_scan' else 0; st=min(6,st) if type(st)==int and 0<=st<=7 else 0
  if not st:continue
  m=d.get('metrics') or {} if src=='race' else {}
  fps=number(m.get('fps'),240) if st==6 else 0; minutes=number(m.get('minutes'),100000) if st==6 else 0; control=st==6 and m.get('control') is True
  # These are third-party summaries even if they cite primary material. No independence assumed.
  raw=round(BASE[st]+15*min(fps/20,1)+10*min(minutes/30,1)+10*control)
  raw=min(99,raw)
  # Separate milestone and measurement quality. All are secondary reports; no bonus for duplicate reports.
  # The weights are explicit editorial rules, not statistical probabilities.
  components={'stage':BASE[st]*.65,'fps':15*min(fps/20,1)*(.55 if m.get('fps_basis')=='session_average' else .45),'stability':10*min(minutes/30,1)*.55,'control':10*control*.55}
  strict=min(99,math.floor(sum(components.values())))
  options.append(dict(source=src,stage=st,reported=raw,strict=strict,source_health=d.get('source_health','unknown'),fps=fps or None,fps_basis=m.get('fps_basis'),minutes=minutes or None,control=control,confidence='C · 第三方转述',components=components,url=d.get('url',''),note=d.get('note',''),missing=['同一构建、同一测试的独立可复核证据']+(['持续游戏内20 FPS'] if fps<20 else [])+(['连续30分钟无崩溃'] if minutes<30 else [])+(['可控角色'] if not control else [])))
 result=copy.deepcopy(max(options,key=lambda x:(x['strict'],x['reported'],x['stage'],x['source']=='race'),default=dict(source='',stage=0,reported=0,strict=0,fps=None,minutes=None,control=False,confidence='U · 未知',url='',note='',missing=['无可评分证据'])))
 halted=bool((p.get('race',{}).get('listing')!='not_listed_in_latest_successful_scan' and p.get('race',{}).get('halted')) or p.get('github',{}).get('archived'))
 unavailable=bool((p.get('race',{}).get('listing')!='not_listed_in_latest_successful_scan' and p.get('race',{}).get('unavailable')) or (p.get('github_error') and 'Repository metadata: HTTP Error 404' in p['github_error']))
 listed=any(p.get(src) and p[src].get('listing')!='not_listed_in_latest_successful_scan' for src in ('race','port'))
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
