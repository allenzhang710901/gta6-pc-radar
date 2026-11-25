import sys,unittest,copy,json,tempfile,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import update as u, audit
class Regressions(unittest.TestCase):
 def test_name_collision(self):
  old={'a':{'repo':'one/a'}}
  self.assertNotEqual(u.project_key(old,'a',{'repo':'two/a'}),'a')
  self.assertEqual(u.project_key(old,'new',{'repo':'ONE/A'}),'a')
 def test_port_name_collision(self):
  p,_,_=u.port_parse({'efforts':[{'name':'A','repo':'one/a','gta':{'world':1}},{'name':'A','repo':'two/a','gta':{'boots':1}}]});self.assertEqual(len(p),2)
 def test_unverified_not_leader(self):
  self.assertFalse(audit.score({'race':{'stage':0}})['eligible'])
 def test_target_not_fps(self):
  self.assertIsNone(u.race_metrics('The target is gameplay at 20 FPS.',6)['fps'])
 def test_negated_duration(self):
  self.assertIsNone(u.race_metrics('The game ran 30 minutes but not without a crash.',6)['minutes'])
 def test_invalid_url(self):
  for url in ['https://','https://user:pw@host.com','javascript:alert(1)']:self.assertEqual(u.safeurl(url),'')
 def test_scan_failure_and_recovery(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'state.json';seed={'projects':{},'events':[],'candidates':[],'health':{},'history':[],'forecast':{}};path.write_text(json.dumps(seed))
   html='<h2>Standings</h2><h3><a href="https://github.com/a/b">Alpha</a></h3><p>Stage 6 of 7. The opening mission runs at 4 FPS.</p><h2>Updates</h2><h3>New render</h3><h2>Time to playable</h2><p>under two days</p>'
   port=json.dumps({'efforts':[{'name':'Alpha','repo':'a/b','gta':{'world':1}}],'news':[{'id':'x','title':'Render update'}]})
   def fake(url):return html if url==u.RACE else port
   def run(time,fn):
    with patch.object(u,'DATA',path),patch.object(u,'NOW',time),patch.object(u,'fetch',side_effect=fn),patch.dict(os.environ,{'GITHUB_TOKEN':'','RADAR_SCAN_UNAUTH':'0'}):u.main()
    return json.loads(path.read_text())
   d=run('2026-11-25T12:00:00+00:00',fake);self.assertEqual(len(d['projects']),1);self.assertEqual(d['forecast']['text'],'under 2 days');self.assertTrue(audit.verify(d['ledger']))
   e=run('2026-11-25T12:05:00+00:00',fake);self.assertEqual(len(e['events']),len(d['events']));self.assertEqual(e['forecast']['first_observed'],d['forecast']['first_observed']);self.assertEqual(len(e['ledger']),len(d['ledger']))
   def failed(url):raise TimeoutError('test timeout')
   f=run('2026-11-25T12:10:00+00:00',failed);self.assertEqual(f['forecast']['status'],'source_error');self.assertEqual(f['projects']['alpha']['audit_score']['source_health'],'error');self.assertEqual(len(f['events']),len(e['events']));self.assertTrue(audit.verify(f['ledger']))
   g=run('2026-11-25T12:15:00+00:00',fake);self.assertEqual(g['forecast']['status'],'ok');self.assertEqual(g['projects']['alpha']['audit_score']['source_health'],'ok');self.assertEqual(g['ledger'][:len(f['ledger'])],f['ledger']);self.assertTrue(audit.verify(g['ledger']))
   g['ledger'][0]['project']='corruption';path.write_text(json.dumps(g));before=path.read_bytes();
   with self.assertRaises(ValueError):run('2026-11-25T12:20:00+00:00',fake)
   self.assertEqual(path.read_bytes(),before)
if __name__=='__main__':unittest.main()
