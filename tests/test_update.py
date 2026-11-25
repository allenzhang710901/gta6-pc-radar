import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import update as u
class Tests(unittest.TestCase):
 def test_port(self):
  p,e,t=u.port_parse({'updated':'2026-11-25','efforts':[{'name':'ZETTROX','repo':'Zettrox/ztrx','gta':{'playable':1,'fps':3}}], 'news':[{'id':'x','title':'FPS update'}]})
  self.assertEqual(p['ztrx']['port']['stage'],6);self.assertEqual(e[0]['category'],'性能')
 def test_race(self):
  p,e,t=u.race_parse('<h2>Standings</h2><h3><a href="https://github.com/a/b">VIctory</a></h3><p>Stage 6 of 7: In-game</p><h2>Updates</h2><h3>New lighting</h3>')
  self.assertEqual(p['victory']['race']['stage'],6);self.assertEqual(p['victory']['repo'],'a/b');self.assertEqual(len(e),1)
 def test_metrics(self):
  m=u.race_metrics('Its README reports the whole opening mission playable on an RTX 3050, in one session of more than 1 hour 30 minutes without a crash, at 1 to 3 frames a second.',6)
  self.assertEqual((m['fps'],m['minutes'],m['control']),(3,90,True))
  self.assertIsNone(u.race_metrics('A pull request runs the opening mission at 20 FPS.',6)['fps'])
  self.assertIsNone(u.race_metrics('Opening cutscene at 30 FPS.',5)['fps'])
 def test_forecast(self):
  f=u.race_forecast('<h2>Time to playable</h2><p>about 2 days</p><p>Around early on Fri 27 Nov.</p><h3>Reasons</h3>')
  self.assertEqual(f['text'],'about 2 days')
 def test_fail(self):
  with self.assertRaises(ValueError):u.race_parse('<h2>error</h2>')
 def test_id(self):self.assertEqual(u.ident('a','b'),u.ident('a','b'))
 def test_url(self):self.assertEqual(u.safeurl('javascript:alert(1)'),'')
if __name__=='__main__':unittest.main()
