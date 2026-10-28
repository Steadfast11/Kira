# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Static bridge inventory and headless native lifecycle checks."""
from pathlib import Path
import unittest
from unittest.mock import patch
from tools.check_page_bridges import check, ROOT, PAGES
from tests import run_swift


class ReviewBridgeTests(unittest.TestCase):
    def test_page_bridges_resolve(self):
        problems, inventory = check()
        self.assertEqual(problems, [])
        self.assertEqual(len(inventory), len(PAGES))

    def test_bridge_checker_catches_a_missing_action_and_native_call(self):
        read = Path.read_text
        def changed(path, *a, **k):
            text = read(path, *a, **k)
            if path == ROOT / 'ui/settings.html': text += '<button data-do="missingAction">Missing</button>'
            if path == ROOT / 'Kira.swift': text += '\n// fixture: "st.missingFunction()"\n'
            return text
        with patch.object(Path, 'read_text', changed): problems, _ = check()
        self.assertIn('settings: action missingAction has no native handler', problems)
        self.assertIn('settings: native call st.missingFunction has no page function', problems)

    def test_unconfigured_support_does_not_reach_the_overlay(self):
        source = (ROOT / 'Kira.swift').read_text()
        method = source[source.index('    func js(_ call: String, _ arg: Any? = nil)'):source.index('    var pointerNext:')]
        run_swift(self, '''import Foundation
let kofi: URL? = nil
var calls = [String]()
func callJS(_ web:Int,_ call:String,_ args:[Any]) { calls.append(args.first as? String ?? call) }
enum NotchHost { static let docked = false }
final class Fixture {
 let web=0, pillOn=false, chatPinned=false
 func setVoice(_ on:Bool) {}
''' + method + '''
}
let f=Fixture();f.js("line","i Support: Tip");f.js("line","i Useful tip");f.js("line","✓ Done")
precondition(calls == ["i Useful tip","✓ Done"])
''')

    def test_boot_releases_replaced_players_and_reports_playback_failure(self):
        source = (ROOT / 'Kira.swift').read_text()
        method = source[source.index('    func play(_ id: String, sound: Bool)'):source.index('    func audioPlayerDidFinishPlaying')]
        run_swift(self, '''import Foundation
let dir="/fixture"
enum Prefs { static func bool(_ key:String)->Bool { false } }
final class AVAudioPlayer {
 static var succeeds=true
 var delegate:AnyObject?, volume:Float=0, isMeteringEnabled=false, stopped=false
 init(contentsOf:URL) throws {}
 func stop(){stopped=true};func prepareToPlay(){};func play()->Bool { Self.succeeds }
 func updateMeters(){};func averagePower(forChannel:Int)->Float { -42 }
}
final class Fixture {
 var players=[AVAudioPlayer](), line:(id:String,player:AVAudioPlayer)?, meter:Timer?, events=[[String:String]]()
 func call(_ name:String,_ value:Any) { if let e=value as? [String:String] { events.append(e) } }
''' + method + '''
}
let f=Fixture(); f.play("first",sound:false);let first=f.line!.player
f.play("second",sound:false);precondition(first.stopped);precondition(f.players.count==1,"stopped player retained")
AVAudioPlayer.succeeds=false;f.play("third",sound:false)
precondition(f.players.isEmpty && f.line==nil,"failed player retained")
precondition(f.events.last?["state"]=="error","failed playback reported start")
f.meter?.invalidate()
''')

    def test_closing_settings_cancels_its_permission_walk_only(self):
        source = (ROOT / 'Kira.swift').read_text()
        start = source.index('    func windowWillClose(_ n: Notification)', source.index('final class SettingsWindow:'))
        method = source[start:source.index('\n}\n', start)]
        run_swift(self, '''import Foundation
final class Setup { var win:Bool?, cancelled=false;func cancelWalk(){cancelled=true} }
let onboarding=Setup()
final class Controller {func removeScriptMessageHandler(forName:String){} }
final class Configuration {let userContentController=Controller()}
final class Web {let configuration=Configuration();func evaluateJavaScript(_ s:String,completionHandler:((Any?,Error?)->Void)?=nil){} }
final class Window {func setFrameAutosaveName(_ s:String){} }
final class Fixture {
 var feedbackJob=0,feedbackURL:URL?,web:Web?,monitor:Int?,timer:Timer?,win:Window?
 func done(_ value:Int?){};func handle(_ b:[String:Any]){}
''' + method + '''
}
let f=Fixture();f.windowWillClose(Notification(name:Notification.Name("close")))
precondition(onboarding.cancelled,"Settings closed but its walk kept running")
onboarding.cancelled=false;onboarding.win=true
f.windowWillClose(Notification(name:Notification.Name("close")))
precondition(!onboarding.cancelled,"Settings close cancelled an open setup window")
''')

    def test_cancelled_permission_walk_does_not_open_a_late_settings_pane(self):
        source = (ROOT / 'Kira.swift').read_text()
        method = source[source.index('    func step() {', source.index('final class Onboarding:')):source.index('    func call(_ f:', source.index('final class Onboarding:'))]
        run_swift(self, '''import Foundation
let noErr=0, gate=DispatchSemaphore(value:0), began=DispatchSemaphore(value:0)
enum Apps {static func check(_ id:String,ask:Bool)->Int {began.signal();gate.wait();return 1}}
final class Settings {func send(_ call:String,_ value:Any){} }
enum Kira {static let settings=Settings()}
final class Fixture {
 var walk=["auto"],walkSince=Date(),panes=0,walkJob=0
 func call(_ f:String,_ v:Any){};func grant(_ id:String){}
 func settings(_ p:String,point:String){panes+=1}
''' + method + '''
}
let f=Fixture();f.step();precondition(began.wait(timeout:.now()+1)==.success)
f.walk=[];gate.signal();RunLoop.main.run(until:Date().addingTimeInterval(0.3))
precondition(f.panes==0,"a cancelled walk opened Settings later")
'''.replace(')==.success', ') == .success'))

    def test_bridge_checker_catches_overlay_and_agent_actions(self):
        read = Path.read_text
        def changed(path, *a, **k):
            text = read(path, *a, **k)
            if path == ROOT / 'ui/ui.html': text += '<script>post({missingOverlayAction:true})</script>'
            if path == ROOT / 'ui/agents.html': text += '<script>post({action:"missingAgentAction"})</script>'
            return text
        with patch.object(Path, 'read_text', changed): problems, _ = check()
        self.assertIn('ui: action missingOverlayAction has no native handler', problems)
        self.assertIn('agents: action missingAgentAction has no native handler', problems)

    def test_disabled_telemetry_does_not_launch_a_helper(self):
        source = (ROOT / 'Kira.swift').read_text()
        method = source[source.index('func telemetry(_ args:'):source.index('func detectLocalServers')]
        run_swift(self, '''import Foundation
var diagnosticsAvailable=false,stats=true,launches=0
enum Prefs {static func bool(_ key:String)->Bool {stats}}
final class Worker {var standardOutput:Any?,standardError:Any?;func run() throws {launches+=1}}
func py(_ args:[String])->Worker {Worker()}
''' + method + '''
for _ in 0..<100 {telemetry(["dictation"])}
precondition(launches==0,"unconfigured diagnostics launched useless workers")
diagnosticsAvailable=true;telemetry(["dictation"]);precondition(launches==1)
stats=false;telemetry(["dictation"]);precondition(launches==1)
''')
