import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit
class TestAudit(unittest.TestCase):
 def test_single_source(self):
  p={'race':{'stage':5,'metrics':{'fps':20,'control':True,'minutes':30}},'port':{'stage':6}}
  s=audit.score(p);self.assertEqual((s['reported'],s['strict'],s['fps']),(65,39,None));self.assertFalse(s['playable'])
 def test_same_claim_not_independent(self):
  p={'race':{'stage':6,'metrics':{'fps':3,'control':True,'minutes':90}}};s=audit.score(p);p['port']={'stage':6};self.assertEqual(audit.score(p)['strict'],s['strict']);self.assertEqual(s['reported'],87)
 def test_no_full_score(self):
  s=audit.score({'race':{'stage':7,'metrics':{'fps':20,'control':True,'minutes':30}}});self.assertEqual(s['reported'],99);self.assertLess(s['strict'],60);self.assertFalse(s['playable'])
 def test_change_and_replay_integrity(self):
  p={'name':'p','race':{'stage':5,'assessment':'t1'}};state={'projects':{'p':p}};audit.init(state,'t1');old={'p':audit.view(p)};p['race']['assessment']='t2';audit.changes(state,old,'t2');self.assertEqual(len(state['ledger']),1)
  p['race']['stage']=4;audit.changes(state,old,'t3');self.assertEqual(len(state['ledger']),2);self.assertLess(state['ledger'][-1]['after']['score']['strict'],state['ledger'][-1]['before']['score']['strict']);self.assertTrue(audit.verify(state['ledger']));state['ledger'][0]['after']['name']='tamper';self.assertFalse(audit.verify(state['ledger']))
 def test_candidates_persist(self):
  x={'repo':'x/y','name':'y'};a=audit.candidates_merge([], [x], 't1',{});b=audit.candidates_merge(a,[],'t2',{});self.assertEqual(b[0]['first_seen'],'t1');self.assertEqual(b[0]['last_seen'],'t1');self.assertEqual(audit.candidates_merge(b,[],'t3',{'y':{'repo':'x/y'}})[0]['status'],'tracked')
 def test_repeated_event_no_change(self):
  s={'projects':{}};audit.init(s,'t');self.assertTrue(audit.verify(s['ledger']));audit.append(s,'event','x',None,{'title':'x'},'t');self.assertTrue(audit.verify(s['ledger']))
