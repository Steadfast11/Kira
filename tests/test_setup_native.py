# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Setup voice lifecycle with fake speakers; no microphone or provider calls."""
from pathlib import Path
import unittest
from tests import run_swift

ROOT=Path(__file__).resolve().parents[1]


class SetupNativeTests(unittest.TestCase):
    def test_preview_ignores_answer_read_preference_and_does_not_copy(self):
        source=(ROOT/'Kira.swift').read_text()
        method=source[source.index('    func deliver('):source.index('    func linger(')]
        run_swift(self,'''import Cocoa
enum Prefs { static func bool(_ key:String)->Bool { key=="autoCopy" };static func str(_ key:String)->String { "" } }
func shortSpoken(_ s:String)->String { s }
func siriVoice() {}
final class Speaker { static let shared=Speaker();var said="";func say(_ s:String)->Bool {said=s;return true} }
final class VoiceWorker { static let cloud:Set<String>=[];static let shared=VoiceWorker();func speak(_ s:String,_ fallback:@escaping()->Void) {preconditionFailure("No network allowed")} }
enum SpeechLanguage { static var systemVoice:String?="fake";static let sayArguments:[String]=[] }
final class Clipboard { var copies=0;func clearContents(){copies+=1};func setString(_ text:String,forType:NSPasteboard.PasteboardType){} }
let clipboard=Clipboard()
final class Harness {
 var ackItem:DispatchWorkItem?,voice:Process?,voiceFallback=false
 func hide(after:Double){}
 @discardableResult func shush()->Bool {false}
'''+method.replace('NSPasteboard.general','clipboard')+'''
}
let app=Harness()
app.deliver("ordinary answer")
precondition(Speaker.shared.said.isEmpty,"Answer preference was ignored")
clipboard.copies=0
app.deliver("preview sample",preview:true)
precondition(Speaker.shared.said=="preview sample","Preview was suppressed by the answer preference")
precondition(clipboard.copies==0,"Preview changed the clipboard")
print("preview policy ok")
''')

    def test_shortcut_recognizes_remote_voice_before_stopping_it(self):
        source=(ROOT/'Kira.swift').read_text()
        method=source[source.index('    @discardableResult func shush()'):source.index('    /// A task that takes')]
        run_swift(self,'''import Foundation
final class Speaker {static let shared=Speaker();func stop()->Bool {false}}
final class VoiceWorker {static let shared=VoiceWorker();var isSpeaking=true;func stop(){isSpeaking=false}}
final class Harness {
 var ackItem:DispatchWorkItem?,voice:Process?,folds=0
 func hide(after:Double){folds+=1}
'''+method+'''
}
let app=Harness()
precondition(app.shush(),"Remote speech was treated as silence")
precondition(!VoiceWorker.shared.isSpeaking && app.folds==1)
precondition(!app.shush(),"Stopped speech remained active")
print("remote voice cutoff ok")
''')
