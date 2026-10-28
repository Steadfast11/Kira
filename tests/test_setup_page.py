# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""First-run page acceptance in an offscreen WebKit view; no app or providers."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from tests.test_settings_page import HARNESS, ROOT


class SetupPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.root=Path(cls.temp.name); cls.binary=cls.root/'setup'
        source=cls.root/'page.swift'; source.write_text(HARNESS.replace('name: "st"','name: "setup"'))
        result=subprocess.run(['swiftc',str(source),'-o',str(cls.binary)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)
        html=(ROOT/'ui/setup.html').read_text().replace('/*CATALOG*/',(ROOT/'ui/catalog.js').read_text()).replace('/*SETUP*/',(ROOT/'ui/setup.js').read_text())
        cls.pagefile=cls.root/'setup.html'; cls.pagefile.write_text(html)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def page(self,script):
        initial="setup.load({prefs:{setupStep:'name',uiLanguage:'en',languages:['en-US'],primaryLanguage:'en-US'},account:{available:false},permissions:{},language:{}});"
        result=subprocess.run([str(self.binary),str(self.pagefile),initial+script],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_name_save_and_blank_validation(self):
        result=self.page("document.querySelector('#next').click();const warning=document.querySelector('#notice').textContent;document.querySelector('#first').value='Xasan';document.querySelector('#last').value='A';document.querySelector('#next').click();return warning;")
        self.assertIn('first name',result['result'])
        self.assertIn({'action':'save','values':{'firstName':'Xasan','lastName':'A'},'next':'language'},result['posts'])

    def test_account_free_resume_and_language_ui(self):
        result=self.page("setup.load({prefs:{setupStep:'language',uiLanguage:'uz',languages:['uz-UZ'],primaryLanguage:'uz-UZ'},account:{available:false},language:{}});document.querySelector('#next').click();return [document.documentElement.lang,document.querySelector('h1').textContent];")
        self.assertEqual(result['result'][0],'uz')
        self.assertIn('tilda',result['result'][1])
        saved=next(p for p in result['posts'] if p.get('action')=='save')
        self.assertEqual(saved['next'],'voice');self.assertEqual(saved['values']['primaryLanguage'],'uz-UZ')

    def test_failed_save_does_not_advance(self):
        result=self.page("document.querySelector('#first').value='X';document.querySelector('#next').click();setup.saved({error:'Disk full'});return [document.querySelector('h1').textContent,document.querySelector('#notice').textContent,document.querySelector('#next').disabled];")
        self.assertEqual(result['result'],['What should I call you?','Disk full',False])

    def test_capability_refresh_preserves_unsaved_name(self):
        result=self.page("document.querySelector('#first').value='Draft';document.querySelector('#first').dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('#first').blur();setup.update({permissions:{mic:true}});return document.querySelector('#first').value;")
        self.assertEqual(result['result'],'Draft')
