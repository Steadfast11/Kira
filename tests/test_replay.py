# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Replay actions use scratch storage and fake app workers, never paid calls or personal apps."""
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import kira
from tests import scratch_dir


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.root=scratch_dir(self)
        for p in [patch.object(kira,'SKILLS',str(self.root/'skills.json')),
                  patch.object(kira,'RECENT',str(self.root/'recent.jsonl')),
                  patch.object(kira,'WORKED',str(self.root/'worked.json')),patch.object(kira,'ME_FILE',str(self.root/'me.json')),
                  patch.dict(os.environ,{'KIRA_ASK':str(self.root),'KIRA_FRONT':'Other Fixture','KIRA_FOCUS_GUARD':'1'},clear=True)]:
            p.start();self.addCleanup(p.stop)
        self.commands=['open -a Fixture','peekaboo menu click --app "com.kira.fixture" --path "Fixture > Start meeting" --no-remote',
                       'osascript -e \'tell application "System Events" to get name of every window of process "Fixture"\'']

    def test_legacy_three_steps_upgrade_and_replay_native_actions_without_ai_or_reads(self):
        (self.root/'skills.json').write_text(json.dumps({'make a fixture meeting':{'cmds':self.commands,'reply':'Started.','mine':True}}))
        with patch.object(kira,'show',return_value='opened Fixture in the background') as show,patch.object(kira,'hands',return_value=('Clicked',True)) as hands,patch.object(kira.subprocess,'run') as shell,patch.object(kira,'start_claude') as ai:
            self.assertEqual(kira.fast('Please start a new fixture meeting'),'Started.')
        show.assert_called_once_with('Fixture',True);hands.assert_called_once_with('menu','com.kira.fixture','Fixture > Start meeting')
        shell.assert_not_called();ai.assert_not_called();self.assertEqual(len(kira.skills()['make a fixture meeting']['cmds']),2)

    def test_internal_partial_request_keys_are_pruned_when_skills_load(self):
        command = kira.SHOW + ' Fixture'
        junk = 'open fixture\nAlready completed: first step\nRemaining words: second step'
        (self.root / 'skills.json').write_text(json.dumps({
            'open fixture': {'cmds': [command], 'reply': 'Opened.', 'mine': True},
            junk: {'cmds': [command], 'reply': 'Opened.', 'mine': True},
        }))
        self.assertEqual(set(kira.skills()), {'open fixture'})
        self.assertEqual(set(json.loads((self.root / 'skills.json').read_text())), {'open fixture'})

    def test_new_shortcuts_drop_reads_and_keep_the_target_when_front_app_changes(self):
        with patch.object(kira,'cached_hands',return_value=None): self.assertTrue(kira.learn('make a fixture meeting',self.commands,'Started.'))
        commands=kira.skills()['make a fixture meeting']['cmds']
        self.assertEqual(commands,[kira.SHOW+' --bg Fixture',kira.HANDS+" menu com.kira.fixture 'Fixture > Start meeting'"])
        self.assertNotIn('Other Fixture',' '.join(commands))
        self.assertIsNone(kira.shortcut_commands('export',['%s click "File > Export"'%kira.HANDS]))

    def test_a_generalized_replay_learns_the_app_it_actually_used(self):
        kira.save_skills({'put fixture alpha left':{'cmds':['open -a "Fixture Alpha"'],'reply':'Done.','mine':True}})
        resolve=lambda name:{'fixture alpha':'Fixture Alpha','fixture beta':'Fixture Beta'}.get(name.lower())
        with patch.object(kira,'app_named',side_effect=resolve),patch.object(kira,'show',return_value='opened'),patch.object(kira,'tip'):
            self.assertEqual(kira.fast('when I say layout mode, put fixture beta left'),'Done.')
        command=kira.skills()['layout mode']['cmds'][0]
        self.assertIn('Fixture Beta',command);self.assertNotIn('Fixture Alpha',command)

    def test_explicit_open_remains_foreground_and_mutating_scripts_are_kept(self):
        script='osascript -e \'tell application "Fixture" to set name of window 1 to "Done"\''
        self.assertEqual(kira.shortcut_commands('open Fixture',['open -a Fixture',script]),['open -a Fixture',script])
        self.assertEqual(kira.shortcut_commands('check',['osascript -e \'get "click"\'']),[])
        found=f'{kira.SHOW} --bg "/tmp/Guide.pdf" && ls /tmp'   # a file found by searching: only the open is replayed
        self.assertEqual(kira.shortcut_commands('study guide',['mdfind -name guide 2>/dev/null | head -20; mdfind x | grep -i y',found]),[f'{kira.SHOW} --bg /tmp/Guide.pdf'])
        with patch.object(kira,'cached_hands',return_value=None): self.assertIsNone(kira.learn('study guide',['ls /tmp > /tmp/out',found],'Opened.'))   # a write is not a lookup

    def test_act_then_sleep_then_state_read_learns_the_act_alone(self):
        play,state='osascript -e \'tell application "Fixture" to play\'','osascript -e \'tell application "Fixture" to player state as string\''
        track='osascript -e \'tell application "Fixture" to name of current track\''
        with patch.object(kira,'cached_hands',return_value=None):
            self.assertTrue(kira.learn('unpause fixture',[f'{play} && sleep 1 && {state}'],'Playing again.'))
            self.assertEqual(kira.skills()['unpause fixture']['cmds'],[play])
            self.assertEqual(kira.shortcut_commands('pause fixture',[f'{play.replace("play","pause")} && {track}']),[play.replace('play','pause')])
            self.assertIsNone(kira.shortcut_commands('play fixture',[f'{state} && {play}']))   # a read before the act: replay would act blind
            self.assertIsNone(kira.learn('play fixture',[f'{state} && sleep 1 && {play}'],'Playing.'))
            delete='osascript -e \'tell application "System Events" to tell process "Fixture" to click button "Delete" of window 1\''
            self.assertIsNone(kira.learn('clear fixture',[f'{delete} && sleep 1 && {state}'],'Cleared.'))   # risky acts stay unlearned
        self.assertEqual(set(kira.skills()),{'unpause fixture'})
        both='osascript -e \'tell application "Fixture" to pause\' -e \'tell application "Fixture" to get player state\''
        self.assertEqual(kira.shortcut_commands('pause fixture',[both,state]),[both])   # an act with its own check in one script stays
        framed='osascript -e \'tell application "System Events"\' -e \'tell process "Fixture" to get name of every window\' -e \'end tell\''
        self.assertEqual(kira.shortcut_commands('windows',[framed]),[])

    def test_replay_says_the_outcome_not_how_the_first_run_went(self):
        play='osascript -e \'tell application "Fixture" to play\''
        (self.root/'skills.json').write_text(json.dumps({'unpause fixture':{'cmds':[play],'reply':'Fixture is playing. The first check still showed it paused, but a second check confirmed it.'}}))
        with patch.object(kira.subprocess,'run',return_value=kira.subprocess.CompletedProcess([],0,'','')):
            self.assertEqual(kira.fast('unpause fixture'),'Fixture is playing.')
        for whole in ['Done: focus mode.','Typed "Hi! See you." into Mail.','Opened 10 Hail Pl. Tell me the city.','Playing 1M. It runs in the background.','I typed your reply into the mail box. It isn’t sent yet.','Notes is open. Do not close it.']:
            self.assertEqual(kira.outcome(whole),whole)

    def test_unsupported_peekaboo_falls_back_without_running(self):
        kira.save_skills({'do fixture':{'cmds':['peekaboo click --id 12'],'reply':'Done.','mine':True}})
        with patch.object(kira.subprocess,'run') as run:self.assertIsNone(kira.replay('do fixture'));run.assert_not_called()
        self.assertIsNone(kira.shortcut_commands('do fixture',[self.commands[-1]+' && open -a Fixture']))
        self.assertIsNone(kira.shortcut_commands('do fixture',[kira.ME+' ask again']))
        reply,saved=kira.remember_workflow('nested fixture',f'Done. [workflow nested fixture | Use the native app.] [replay python3 {kira.ME} ask again]',True,['open Fixture'])
        self.assertTrue(saved);self.assertNotIn('nested fixture',kira.skills())

    def test_native_menu_bypasses_map_capture_but_waits_for_confirmation(self):
        args=('menu','com.kira.fixture','Fixture > Start meeting')
        worker=unittest.mock.Mock(returncode=0,stdout='Clicked Start meeting\n',stderr='')
        with patch.object(kira,'wait_commit',return_value=True),patch.object(kira,'hands_call',return_value=worker) as call,patch.object(kira,'hands_map') as mapping:
            self.assertTrue(kira.hands(*args)[1]);call.assert_called_once_with(list(args),timeout=2);mapping.assert_not_called()
        with patch.object(kira,'wait_commit',return_value=False),patch.object(kira,'hands_call') as call:
            self.assertFalse(kira.hands(*args)[1]);call.assert_not_called()

    def test_guarded_background_open_does_not_poll_or_sleep(self):
        with patch.object(kira,'osa') as osa,patch.object(kira.time,'sleep') as sleep,patch.object(kira,'preview_app'),patch.object(kira.subprocess,'run',return_value=unittest.mock.Mock(returncode=0)):
            kira.show('Fixture',bg=True);osa.assert_not_called();sleep.assert_not_called()

    def test_failed_direct_open_falls_back_instead_of_claiming_success(self):
        kira.save_skills({'open fixture':{'cmds':[kira.SHOW+' Fixture'],'reply':'Opened.','mine':True}})
        with patch.object(kira,'show',return_value='no app or file called "Fixture"'):
            self.assertIsNone(kira.replay('open fixture'))

    def test_recent_memory_creates_missing_scratch_directory(self):
        missing=self.root/'new';recent=missing/'recent.jsonl'
        with patch.object(kira,'DIR',str(missing)),patch.object(kira,'RECENT',str(recent)):
            kira.remember_turn('Find fixture notes','Found them.');self.assertEqual(kira.recent()[0]['q'],'Find fixture notes')
            self.assertEqual(recent.stat().st_mode&0o777,0o600)
            with patch.object(kira.os,'replace',side_effect=OSError('disk full')):
                with self.assertRaises(OSError): kira.remember_turn('Other ask','Other answer')
            self.assertEqual(kira.recent()[0]['q'],'Find fixture notes')

    def test_first_ai_answer_saves_memory_and_log_in_a_fresh_directory(self):
        class NoThread:
            def __init__(self,*a,**kw): pass
            def start(self): pass
            def join(self,*a): pass
        missing=self.root/'fresh';brain=unittest.mock.Mock(return_value=('Found them. [unlearn]',0,[]));brain.ok=True;brain.cmds=[];brain.ran=[];brain.observed=[]
        with patch.object(kira,'DIR',str(missing)),patch.object(kira,'RECENT',str(missing/'recent.jsonl')),patch.object(kira,'MEMORY',str(missing/'memory.md')),patch.object(kira.threading,'Thread',NoThread),patch('sys.argv',['kira.py','Find fixture notes']),patch.multiple(kira,licensed=lambda:True,ping=lambda:None,fast=lambda _:None,front=lambda:('Fixture','Scratch'),osa=lambda *a:'',screens=lambda:[],describe=lambda *a:'Scratch display',selection_context=lambda:'',screen_for=lambda *a:None,run=brain,wait_commit=lambda:True,restore_focus=lambda *a:None,say=lambda *a:None,tip=lambda *a:None,look=lambda:[],hands_map=lambda *a:None):
            kira.main();self.assertEqual(kira.recent()[0]['a'],'Found them.');self.assertTrue((missing/'log.jsonl').exists())
        brain.assert_called_once()

    def test_bare_running_check_is_dropped_and_a_new_shortcut_or_workflow_shows_the_learned_pill(self):
        class NoThread:
            def __init__(self,*a,**kw): pass
            def start(self): pass
            def join(self,*a): pass
        quit,check='osascript -e \'tell application "Fixture" to quit\'','osascript -e \'application "Fixture" is running\''
        self.assertEqual(kira.shortcut_commands('close fixture',[quit,check]),[quit])
        self.assertEqual(kira.shortcut_commands('close fixture',[f'{quit} && sleep 1 && {check.replace("is","is not")}']),[quit])
        self.assertIsNone(kira.shortcut_commands('close fixture',[f'{check} && {quit}']))   # a check before the act still refuses
        guarded='osascript -e \'tell application "Fixture"\' -e \'if player state is playing then pause\' -e \'end tell\''
        self.assertEqual(kira.shortcut_commands('pause fixture',[guarded]),[guarded])
        def ask(task,reply,cmds):
            brain=unittest.mock.Mock(return_value=(reply,0,[]));brain.ok=True;brain.cmds=cmds;brain.ran=cmds;brain.observed=[]
            tip=unittest.mock.Mock()
            with patch.object(kira,'DIR',str(self.root)),patch.object(kira,'RECENT',str(self.root/'recent.jsonl')),patch.object(kira,'MEMORY',str(self.root/'memory.md')),patch.object(kira.threading,'Thread',NoThread),patch('sys.argv',['kira.py',task]),patch.multiple(kira,licensed=lambda:True,ping=lambda:None,fast=lambda _:None,front=lambda:('Fixture','Scratch'),osa=lambda *a:'',screens=lambda:[],describe=lambda *a:'Scratch display',selection_context=lambda:'',screen_for=lambda *a:None,run=brain,wait_commit=lambda:True,restore_focus=lambda *a:None,say=lambda *a:None,tip=tip,look=lambda:[],hands_map=lambda *a:None,cached_hands=lambda:None):
                with patch.object(kira,'app_id',return_value='com.example.fixture'),patch.object(kira,'app_running',return_value=False): kira.main()
            return tip.call_args.args[1]
        self.assertEqual(ask('Close fixture','Fixture is closed.',[quit,check]),'Learned: Say “Close fixture” any time.')
        self.assertEqual(kira.skills()['close fixture']['cmds'],[quit])
        self.assertEqual(kira.recent()[-1]['shortcut']['key'],'close fixture')
        self.assertEqual(ask('Close fixture','Fixture is closed.',[quit,check]),'')   # already known: no pill
        self.assertEqual(ask('Tidy fixture','Tidied. [workflow tidy fixture | Use the View menu.]',[f'{kira.HANDS} see Fixture']),'Learned: Procedure saved for next time.')

    def test_instant_quit_uses_bundle_id_verifies_and_beats_old_skill(self):
        old='osascript -e \'tell application "Fixture Display" to quit\''
        kira.save_skills({'close fixture display':{'cmds':[old],'reply':'Old false success.','mine':True},
                             'end fixture':{'cmds':[old],'reply':'Ended.','mine':True}})
        resolve=lambda name: 'Fixture' if name == 'fixture display' else None
        with patch.object(kira,'app_named',side_effect=resolve),patch.object(kira,'app_id',return_value='com.example.fixture') as app_id, \
             patch.object(kira,'quit_app',return_value=True) as quit_app,patch.object(kira,'replay') as replay:
            self.assertEqual(kira.fast('close fixture display'),'Closed Fixture.')
            app_id.assert_called_once_with('Fixture');quit_app.assert_called_once_with('com.example.fixture');replay.assert_not_called()
            self.assertIn('application id "com.example.fixture"',kira.fast.cmds[0])
            self.assertIsNone(kira.fast('close this tab'))
            self.assertIsNone(kira.fast('close the window'))
        with patch.object(kira,'app_named',side_effect=resolve),patch.object(kira,'app_id',return_value='com.example.fixture'), \
             patch.object(kira,'quit_app',return_value=False):
            self.assertEqual(kira.fast('quit fixture display'),'Fixture is still open.')
            self.assertEqual(kira.fast.cmds,[])
        with patch.object(kira,'app_named',return_value='Fixture'),patch.object(kira,'app_id',return_value='com.example.fixture') as app_id, \
             patch.object(kira,'quit_app',return_value=True) as quit_app,patch.object(kira.subprocess,'run') as shell:
            self.assertEqual(kira.replay('end fixture'),'Ended.')
            app_id.assert_called_once_with('Fixture');quit_app.assert_called_once_with('com.example.fixture');shell.assert_not_called()
        with patch.object(kira,'app_running',side_effect=[True,True,False]),patch.object(kira,'osa') as osa,patch.object(kira.time,'sleep'):
            self.assertTrue(kira.quit_app('com.example.fixture'))
        osa.assert_called_once_with('tell application id "com.example.fixture" to quit',timeout=2)

    def test_user_reported_failure_unlearns_without_saving_the_correction(self):
        command='osascript -e \'tell application "Fixture" to set visible to false\''
        kira.save_skills({'hide fixture':{'cmds':[command],'reply':'Fixture is hidden.','mine':True}})
        worker=unittest.mock.Mock(returncode=0,stdout='fixture became hidden\n',stderr='')
        with patch.object(kira.subprocess,'run',return_value=worker),patch.object(kira,'preview_commands'):
            answer=kira.fast('hide fixture')
        self.assertEqual(answer,'Fixture is hidden.')
        kira.remember_turn('hide fixture',answer,kira.fast.shortcut)

        class NoThread:
            def __init__(self,*a,**kw): pass
            def start(self): pass
            def join(self,*a): pass
        brain=unittest.mock.Mock(return_value=('Fixture is hidden now. [unlearn] [workflow hide fixture | Hide it, then check.]',0,[]))
        brain.ok=True;brain.cmds=brain.ran=[command];brain.observed=[{'action':command,'error':False,'result':'verified hidden'}]
        say=unittest.mock.Mock()
        with patch.object(kira.threading,'Thread',NoThread),patch('sys.argv',['kira.py','It is still visible']), \
             patch.multiple(kira,licensed=lambda:True,ping=lambda:None,fast=lambda _:None,front=lambda:('Fixture','Scratch'),
                            osa=lambda *a:'',screens=lambda:[],describe=lambda *a:'Scratch display',selection_context=lambda:'',
                            screen_for=lambda *a:None,tool_help=lambda *a,**k:'',run=brain,wait_commit=lambda:True,
                            restore_focus=lambda *a:None,say=say,tip=lambda *a:None,look=lambda:[],hands_map=lambda *a:None):
            kira.main()
        self.assertEqual(say.call_args.args[1],'Fixture is hidden now.')   # no control tag shows, and the redo saves nothing
        self.assertEqual(kira.workflows(),{})
        prompt=brain.call_args.args[0]
        self.assertIn('Previous learned shortcut',prompt)
        self.assertIn('hide fixture',prompt)
        self.assertIn('fixture became hidden',prompt)
        self.assertEqual(brain.call_args.kwargs['request'],'It is still visible')
        self.assertNotIn('hide fixture',kira.skills())

    def test_unrelated_ask_after_replay_keeps_the_shortcut(self):
        command='osascript -e \'tell application "Fixture" to set visible to false\''
        kira.save_skills({'hide fixture':{'cmds':[command],'reply':'Fixture is hidden.','mine':True}})
        worker=unittest.mock.Mock(returncode=0,stdout='fixture became hidden\n',stderr='')
        with patch.object(kira.subprocess,'run',return_value=worker),patch.object(kira,'preview_commands'):
            answer=kira.fast('hide fixture')
        kira.remember_turn('hide fixture',answer,kira.fast.shortcut)

        class NoThread:
            def __init__(self,*a,**kw): pass
            def start(self): pass
            def join(self,*a): pass
        brain=unittest.mock.Mock(return_value=('The unrelated answer.',0,[]))
        brain.ok=True;brain.cmds=brain.ran=[];brain.observed=[]
        with patch.object(kira.threading,'Thread',NoThread),patch('sys.argv',['kira.py','Explain an unrelated topic']), \
             patch.multiple(kira,licensed=lambda:True,ping=lambda:None,fast=lambda _:None,front=lambda:('Fixture','Scratch'),
                            osa=lambda *a:'',screens=lambda:[],describe=lambda *a:'Scratch display',selection_context=lambda:'',
                            screen_for=lambda *a:None,tool_help=lambda *a,**k:'',run=brain,wait_commit=lambda:True,
                            restore_focus=lambda *a:None,say=lambda *a:None,tip=lambda *a:None,look=lambda:[],hands_map=lambda *a:None):
            kira.main()
        self.assertIn('Previous learned shortcut',brain.call_args.args[0])
        self.assertIn('hide fixture',kira.skills())

    def test_stray_unlearn_control_is_never_shown(self):
        class NoThread:
            def __init__(self,*a,**kw): pass
            def start(self): pass
            def join(self,*a): pass
        brain=unittest.mock.Mock(return_value=('Done. [unlearn]',0,[]))
        brain.ok=True;brain.cmds=brain.ran=[];brain.observed=[]
        say=unittest.mock.Mock()
        with patch.object(kira.threading,'Thread',NoThread),patch('sys.argv',['kira.py','Do the fixture task']), \
             patch.multiple(kira,licensed=lambda:True,ping=lambda:None,fast=lambda _:None,front=lambda:('Fixture','Scratch'),
                            osa=lambda *a:'',screens=lambda:[],describe=lambda *a:'Scratch display',selection_context=lambda:'',
                            screen_for=lambda *a:None,tool_help=lambda *a,**k:'',run=brain,wait_commit=lambda:True,
                            restore_focus=lambda *a:None,say=say,tip=lambda *a:None,look=lambda:[],hands_map=lambda *a:None):
            kira.main()
        self.assertEqual(say.call_args.args[1],'Done.')
        self.assertEqual(kira.recent()[-1]['a'],'Done.')

    def test_failed_replay_is_redone_and_successful_recovery_replaces_it(self):
        quit='osascript -e \'tell application "Fixture" to quit\''
        kira.save_skills({'bye fixture':{'cmds':[quit],'reply':'Fixture is closed.','mine':True}})
        stubs=dict(app_id=lambda *a:'com.example.fixture',osa=lambda *a,**k:'',app_named=lambda *a:None)
        with patch.multiple(kira,**stubs),patch.object(kira,'app_running',side_effect=[True,False]),patch.object(kira.time,'sleep'),patch.object(kira.subprocess,'run') as shell:
            self.assertEqual(kira.fast('bye fixture'),'Fixture is closed.')   # verified: the same instant reply
            self.assertIsNone(kira.fast.failed);shell.assert_not_called()
        with patch.object(kira,'wants_focus',return_value=True),patch.multiple(kira,**stubs),patch.object(kira.time,'sleep'),patch.object(kira,'preview_commands'), \
             patch.object(kira.subprocess,'run',return_value=kira.subprocess.CompletedProcess([],0,'','')):
            kira.save_skills({**kira.skills(),'show fixture':{'cmds':['open -a Fixture'],'reply':'Opened.','mine':True}})
            with patch.object(kira,'app_running',return_value=False): self.assertIsNone(kira.replay('show fixture'))
            self.assertEqual(kira.replay.ran[-1],'Fixture => not running')
            with patch.object(kira,'app_running',return_value=True): self.assertEqual(kira.replay('show fixture'),'Opened.')

        class NoThread:
            def __init__(self,*a,**kw): pass
            def start(self): pass
            def join(self,*a): pass
        replacement=kira.HANDS+" menu com.example.fixture 'Fixture > Quit'"
        brain=unittest.mock.Mock(return_value=('Fixture is closed now; the shortcut had not quit it. [unlearn]',0,[]))
        brain.ok=True;brain.cmds=brain.ran=[replacement]
        brain.observed=[{'action':replacement,'error':False,'result':'Fixture closed'}]
        say,tip=unittest.mock.Mock(),unittest.mock.Mock()
        with patch.object(kira.threading,'Thread',NoThread),patch('sys.argv',['kira.py','bye fixture']),patch.object(kira,'app_running',return_value=True),patch.object(kira.time,'sleep'), \
             patch.multiple(kira,**stubs,licensed=lambda:True,ping=lambda:None,front=lambda:('Fixture','Scratch'),screens=lambda:[],describe=lambda *a:'Scratch display',
                            selection_context=lambda:'',screen_for=lambda *a:None,tool_help=lambda *a,**k:'',run=brain,wait_commit=lambda:True,
                            restore_focus=lambda *a:None,say=say,tip=tip,look=lambda:[],hands_map=lambda *a:None,report=lambda *a:None,cached_hands=lambda:None):
            kira.main()
        said=[c.args for c in say.call_args_list]
        self.assertIn(('▸','The shortcut did not work. Redoing it'),said)
        self.assertNotIn('Fixture is closed.',[s for _,s in said])   # never the learned success line
        self.assertEqual(said[-1][1],'Fixture is closed now; the shortcut had not quit it.')
        prompt=brain.call_args.args[0]
        self.assertIn('still open',prompt);self.assertIn('failed (see its output): redo the request',prompt)
        self.assertEqual(kira.skills()['bye fixture']['cmds'],[replacement])
        self.assertEqual(tip.call_args.args[1],'Learned: Say “bye fixture” any time.')

    def test_a_quit_that_is_still_running_is_not_learned(self):
        command='osascript -e \'tell application id "com.example.fixture" to quit\''
        with patch.object(kira,'cached_hands',return_value=None),patch.object(kira,'app_running',return_value=True):
            self.assertIsNone(kira.learn('close fixture',[command],'Fixture is closed.'))
        with patch.object(kira,'shortcut_commands',return_value=['osascript -e "']):
            self.assertIsNone(kira.learn('malformed fixture',[command],'Done.'))
        self.assertNotIn('close fixture',kira.skills())

    def test_reference_ask_receives_recent_target_and_agent_history(self):
        class NoThread:
            def __init__(self,*a,**kw): pass
            def start(self): pass
            def join(self,*a): pass
        url='https://fixture.example/posts/42'
        agent=self.root/'agents'/('a'*32);agent.mkdir(parents=True)
        kira.private_json(str(agent/'context.json'),{'id':'a'*32,'status':'done','created':time.time(),
                                                       'brief':'Find a useful post','links':[url]})
        (self.root/'worked.json').write_text(json.dumps({'app':'Reader Fixture','window':'Earlier post'}))
        brain=unittest.mock.Mock(return_value=('Opened the earlier post.',0,[]));brain.ok=True;brain.cmds=[];brain.ran=[];brain.observed=[]
        with patch.object(kira,'RECENT',str(self.root/'recent.jsonl')),patch.object(kira,'MEMORY',str(self.root/'memory.md')):
            kira.remember_turn('Find a useful post','Opened '+url)
            with patch.object(kira.threading,'Thread',NoThread),patch('sys.argv',['kira.py','Open that post you opened']),patch.multiple(kira,licensed=lambda:True,ping=lambda:None,fast=lambda _:None,front=lambda:('Fixture','Scratch'),osa=lambda *a:'',screens=lambda:[],describe=lambda *a:'Scratch display',selection_context=lambda:'',screen_for=lambda *a:None,run=brain,wait_commit=lambda:True,restore_focus=lambda *a:None,say=lambda *a:None,tip=lambda *a:None,look=lambda:[],hands_map=lambda *a:None):
                kira.main()
        prompt=brain.call_args.args[0]
        self.assertIn('Earlier:\nQ: Find a useful post\nA: Opened '+url,prompt)
        self.assertIn('Last task worked in: Reader Fixture "Earlier post"',prompt)
        self.assertIn('Background tasks',prompt);self.assertIn('a'*32,prompt)
        self.assertEqual(brain.call_args.kwargs['request'],'Open that post you opened')
