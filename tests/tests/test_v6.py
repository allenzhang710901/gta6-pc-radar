import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit,update
class V6(unittest.TestCase):
 def dexnom(self):
  return {'id':'dexnom','name':'DexNom','repo':'DexNom/VIctory','tier':'tracked','gpu':['AMD'],'verification':'portwatch','gta':{'loads':1,'boots':1,'menu':1,'world':1,'playable':1,'render':.9,'story':.5,'fps':3,'stability':.7}}
 def test_dexnom(self):
  e=self.dexnom();p,_,_=update.port_parse({'efforts':[e]});d=p['dexnom'];s=audit.score(d)
  self.assertEqual(d['port']['gpu'],['AMD']);self.assertEqual(d['port']['reference_score'],78.0);self.assertEqual(d['port']['reference_rank'],1)
  self.assertEqual(s['dimensions'],{'stage':20,'fps':3.0,'render':18.,'story':7.5,'stability':10.5,'control':10});self.assertEqual(s['reported'],69);self.assertEqual(s['strict'],51);self.assertFalse(s['playable']);self.assertEqual(s['evidence_grade'],'B')
 def test_not_join_sources(self):
  p={'race':{'stage':6,'metrics':{'fps':20,'minutes':30}},'port':{'stage':6,'render':1,'story':1,'verification':'portwatch'}};s=audit.score(p)
  self.assertEqual(len(s['alternatives']),2);self.assertFalse(s['playable']);self.assertTrue(s['dimensions']['render'] is None or s['dimensions']['fps'] is None)
 def test_unknown_not_zero(self):
  s=audit.score({'port':{'stage':6,'render':None,'story':0,'stability':'unknown'}});self.assertIsNone(s['dimensions']['render']);self.assertEqual(s['dimensions']['story'],0);self.assertIsNone(s['dimensions']['stability'])
 def test_rank_private_and_nuked(self):
  e=self.dexnom();x={**e,'id':'private','repo':None};y={**e,'id':'removed','nuked':True,'manualScore':100};self.assertEqual(update.port_rankings([x,y,e]),{'dexnom':1})
 def test_port_missing(self):
  e=self.dexnom();e['stats']={'missing':True};p,_,_=update.port_parse({'efforts':[e]});self.assertFalse(audit.score(p['dexnom'])['eligible'])
 def test_untrusted_fields(self):
  s=audit.score({'port':{'stage':6,'fps':-2,'render':7,'story':True,'stability':float('nan')}});self.assertIsNone(s['dimensions']['fps']);self.assertIsNone(s['dimensions']['render']);self.assertIsNone(s['dimensions']['story']);self.assertIsNone(s['dimensions']['stability'])
 def test_race_display_order(self):
  p,_,_=update.race_parse('<h2>Standings</h2><h3>A</h3>Stage 6 of 7<h3>B</h3>Stage 5 of 7');self.assertEqual(p['b']['race']['reference_rank'],2)
