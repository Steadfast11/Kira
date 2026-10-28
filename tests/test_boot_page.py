# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""ui/boot.html in a real WKWebView that is never put in a window: the scenes in time, words in step with the recorded voice,
Reduce Motion, Skip / Esc / the button, sound off, the live name, and the orb's light staying inside its outline. Plus the voice
assets (tools/make_boot_voice.py) and how Kira.swift and build.sh load them."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / 'ui' / 'boot'
HARNESS = r'''import Cocoa
import WebKit
// Loads argv[1] as Boot does, gives the page argv[3] (JSON) as boot.env, runs argv[2] as an async function body once it has loaded,
// then prints {"result", "posts"}: what the body returned and every message the page posted to Swift's `boot` handler.
// argv[4] == "reduced": the page is told Reduce Motion is on.
final class Harness: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
    var posts: [Any] = [], web: WKWebView!
    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) { posts.append(m.name == "errors" ? ["error": m.body] : m.body) }
    func webView(_ w: WKWebView, didFinish n: WKNavigation!) {
        w.callAsyncJavaScript(CommandLine.arguments[2], arguments: [:], in: nil, in: .page) { r in
            switch r {
            case .success(let x):
                let out = try! JSONSerialization.data(withJSONObject: ["result": x ?? NSNull(), "posts": self.posts])
                print(String(data: out, encoding: .utf8)!); exit(0)
            case .failure(let e): print(e); exit(1)
            }
        }
    }
}
NSApplication.shared.setActivationPolicy(.prohibited)   // no Dock icon, no menu, no window
let h = Harness(), cfg = WKWebViewConfiguration(), u = cfg.userContentController
cfg.preferences.setValue(false, forKey: "hiddenPageDOMTimerThrottlingEnabled")   // a page never put in a window counts as hidden; in Kira's window it is shown
u.add(h, name: "boot"); u.add(h, name: "errors")
u.addUserScript(WKUserScript(source: "window.__BOOT_SELF=true;window.__ORB_KEEP=true;addEventListener('error',e=>webkit.messageHandlers.errors.postMessage(String(e.message)));addEventListener('unhandledrejection',e=>webkit.messageHandlers.errors.postMessage(String(e.reason)))", injectionTime: .atDocumentStart, forMainFrameOnly: true))
u.addUserScript(WKUserScript(source: "boot.env(" + CommandLine.arguments[3] + ")", injectionTime: .atDocumentEnd, forMainFrameOnly: true))   // as Swift does, before the scene starts
if CommandLine.arguments.count > 4, CommandLine.arguments[4] == "reduced" {
    u.addUserScript(WKUserScript(source: "const mq=window.matchMedia.bind(window);window.matchMedia=q=>q.includes('prefers-reduced-motion')?{matches:true,addEventListener(){},addListener(){}}:mq(q)", injectionTime: .atDocumentStart, forMainFrameOnly: true))
}
h.web = WKWebView(frame: NSRect(x: 0, y: 0, width: 1280, height: 800), configuration: cfg)
h.web.navigationDelegate = h
h.web.loadHTMLString(try! String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8), baseURL: nil)
DispatchQueue.main.asyncAfter(deadline: .now() + 55) { print("timeout"); exit(1) }
NSApplication.shared.run()
'''
# Each body starts by watching data-phase: `seen` is [[phase, ms since load], ...]. The page's own timers run in this windowless view, so timing is real.
WATCH = r'''
const tick = ms => new Promise(r => setTimeout(r, ms)), phase = () => document.body.dataset.phase, seen = [[phase(), Math.round(performance.now())]];
new MutationObserver(() => seen.push([phase(), Math.round(performance.now())])).observe(document.body, {attributes: true, attributeFilter: ['data-phase']});
const key = k => window.dispatchEvent(new KeyboardEvent('keydown', {key: k}));
const until = async (p, ms = 30000) => { for (let i = 0; i < ms / 50 && phase() !== p; i++) await tick(50); return phase() === p; };
const out = {};
'''
# The whole first-launch scene. When the welcome line starts, Swift's "start" is played back 250 ms late, as a slow audio start would be.
TIMELINE = WATCH + r'''
const words = [];
new MutationObserver(ms => { for (const m of ms) if (m.target.classList?.contains('on') && m.target.classList.contains('w')) words.push([m.target.textContent, Math.round(performance.now())]); })
  .observe(document.getElementById('line'), {subtree: true, attributes: true, attributeFilter: ['class']});
await until('words'); await tick(250); boot.voice({id: 'welcome', state: 'start'}); out.started = Math.round(performance.now());
out.reachedCta = await until('cta');
out.seen = seen; out.words = words;
out.copy = [document.getElementById('greet').textContent, document.getElementById('cta').textContent, document.getElementById('skip').textContent, document.getElementById('word').textContent];
out.focus = document.activeElement.id;
out.network = performance.getEntriesByType('resource').filter(e => !e.name.startsWith('data:')).map(e => e.name);
out.look = [getComputedStyle(document.body).backgroundImage.includes('gradient'), getComputedStyle(document.body).backgroundColor];
out.gl = __boot.orb.gl;
return out;
'''
REDUCED = WATCH + r'''
await tick(80); out.first = __boot.orbAt(performance.now()).main; out.top = {y: innerHeight * .31, r: __boot.R() * .62};
out.calm = document.body.classList.contains('calm');
await until('words', 12000); out.seen = seen;
return out;
'''
SKIP = WATCH + r'''
await tick(500); key('Escape'); out.afterEsc = phase();
await until('cta', 8000); out.cta = phase();
key('Escape'); await tick(50); out.seen = seen;
return out;
'''
SETUP = WATCH + r'''
await tick(300); document.getElementById('skip').click();
await until('cta', 8000); document.getElementById('cta').click();
out.left = await until('leaving', 12000);
await tick(1100); out.under = __boot.orbAt(performance.now());   // gliding up under the notch
await tick(500); out.sinking = __boot.orbAt(performance.now());   // melted onto its edge, being drawn in
await tick(700); out.seen = seen; out.end = __boot.orbAt(performance.now());
return out;
'''
REPLAY = WATCH + r'''
await tick(300); key('Escape');
out.left = await until('leaving', 20000); await tick(1800); out.seen = seen;
return out;
'''
MUTE = WATCH + r'''
await tick(200); document.getElementById('sound').click(); out.muted = [document.body.classList.contains('muted'), document.getElementById('sound').getAttribute('aria-label')];
return out;
'''
# The orb at rest, read back pixel by pixel: bright and blue inside, nothing at all just outside the outline.
ORB = WATCH + r'''
const s = __boot.show('rise', 6000), c = document.getElementById('orb'), k = c.width / innerWidth;
const copy = document.createElement('canvas'); copy.width = c.width; copy.height = c.height;
const g = copy.getContext('2d'); g.drawImage(c, 0, 0);
const px = (x, y) => Array.from(g.getImageData(Math.round(x * k), Math.round(y * k), 1, 1).data);
const m = s.main, ring = [];
for (let i = 0; i < 16; i++) { const a = i * Math.PI / 8; ring.push(px(m.x + Math.cos(a) * m.r * 1.04, m.y + Math.sin(a) * m.r * 1.04)); }
const inside = [];
for (const [dx, dy] of [[0, 0], [-.4, -.3], [.4, .3], [.3, -.4], [-.3, .45]]) inside.push(px(m.x + dx * m.r, m.y + dy * m.r));
out.ring = ring; out.inside = inside; out.far = px(m.x + m.r * 1.6, m.y); out.gl = __boot.orb.gl; out.r = m.r;
return out;
'''


@unittest.skipUnless(sys.platform == 'darwin', 'macOS WebKit page check')
class BootPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.page, src, cls.binary = cls.tmp / 'boot.html', cls.tmp / 'page.swift', cls.tmp / 'page'
        html = (ROOT / 'ui/boot.html').read_text()
        for mark, part in [('/*GLOBE*/', 'globe.js'), ('/*ORB*/', 'orb.js'), ('/*CATALOG*/', 'catalog.js'), ('/*VOICE*/', 'boot/timings.json')]:   # as loadPage() does
            html = html.replace(mark, (ROOT / 'ui' / part).read_text())
        cls.page.write_text(html)
        src.write_text(HARNESS)
        built = subprocess.run(['swiftc', str(src), '-o', str(cls.binary)], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        cls.voice = json.loads((BOOT / 'timings.json').read_text())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def run_page(self, script, env=None, *flags):
        run = subprocess.run([str(self.binary), str(self.page), script, json.dumps(env or {}), *flags], capture_output=True, text=True, timeout=70)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        got = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual([p for p in got['posts'] if isinstance(p, dict) and 'error' in p], [])
        return got['result'], got['posts']

    def test_first_launch_scenes_in_time(self):
        out, posts = self.run_page(TIMELINE)
        self.assertTrue(out['reachedCta'])
        self.assertEqual([p for p, _ in out['seen']], ['rise', 'logo', 'words', 'greet', 'cta'])   # drop -> logo -> words -> greeting -> setup button
        at = dict(reversed(out['seen']))
        self.assertTrue(5800 <= at['logo'] <= 7600, at)   # a 4.4 s rise, then the drop lands on the logo
        self.assertTrue(at['words'] - at['logo'] >= 2200, at)   # the logo holds about two seconds before Kira speaks
        self.assertTrue(at['cta'] - at['greet'] >= 2800, at)   # the greeting stays almost three seconds
        self.assertEqual(out['copy'], ['Hi there, great to meet you!', 'Set up Kira', 'Skip intro', 'Kira'])
        self.assertEqual(out['focus'], 'cta')   # Return goes on
        self.assertEqual(out['network'], [])   # nothing is fetched
        self.assertTrue(out['look'][0])   # the page's own veil, see-through over Swift's frosted glass
        sounds = [p['id'] for p in posts if p.get('do') == 'play']
        self.assertEqual(sounds, ['rise', 'chime', 'welcome', 'hiThere'])   # nothing asks for the microphone or anything else
        self.assertTrue(all(p.get('sound') for p in posts if p.get('id') in ('rise', 'chime')))

    def test_words_appear_as_they_are_spoken(self):
        out, _ = self.run_page(TIMELINE)
        line = self.voice['lines']['welcome']
        self.assertEqual([w for w, _ in out['words']], [w for w, _ in line['words']])
        for (word, shown), (_, said) in zip(out['words'], line['words']):   # from the moment the sound started, as Swift reported it
            self.assertLess(abs(shown - out['started'] - said), 90, (word, shown - out['started'], said))

    def test_reduced_motion_cross_fades_in_place(self):
        out, posts = self.run_page(REDUCED, {}, 'reduced')
        self.assertTrue(out['calm'])
        self.assertAlmostEqual(out['first']['y'], out['top']['y'], delta=1)   # no drop rising: the orb fades in where it rests
        self.assertAlmostEqual(out['first']['r'], out['top']['r'], delta=1)
        self.assertEqual([p for p, _ in out['seen']][:3], ['rise', 'logo', 'words'])
        self.assertNotIn('rise', [p.get('id') for p in posts])

    def test_escape_skips_then_closes(self):
        out, posts = self.run_page(SKIP)
        self.assertEqual((out['afterEsc'], out['cta']), ('greet', 'cta'))
        self.assertNotIn('logo', [p for p, _ in out['seen']])   # the stopped intro does not come back
        self.assertIn({'do': 'stop'}, posts)   # its sound stops with it
        self.assertEqual(posts[-1], {'do': 'done', 'next': 'later'})   # Esc at the button: setup later (at launch Kira opens it anyway)

    def test_setup_button_says_the_setup_line_and_goes_home_into_the_notch(self):
        notch = {'x': 640, 'w': 200, 'h': 34, 'hardware': True}
        out, posts = self.run_page(SETUP, {'notch': notch, 'status': {'x': 1200, 'y': 12}})
        self.assertTrue(out['left'])
        self.assertIn({'do': 'play', 'id': 'setup'}, posts)
        self.assertEqual(posts[-1], {'do': 'done', 'next': 'setup'})   # Swift opens Kira's box from the notch, then setup
        for state in (out['under'], out['sinking'], out['end']):
            self.assertAlmostEqual(state['main']['x'], 640, delta=40)   # straight up to the notch, never to the menu bar icon
        self.assertGreater(out['under']['main']['y'], 34)
        self.assertEqual(out['sinking']['sink'], {'x': 640, 'w': 200, 'h': 34})   # it melts into the notch's own shape
        self.assertGreater(out['sinking']['k3'], 0)
        self.assertLess(out['end']['main']['y'] + out['end']['main']['r'] * out['end']['stretch'], 34)   # all of it is inside the notch now
        self.assertGreater(out['end']['alpha'], .9)   # it is not faded out: the hardware notch takes it

    def test_without_the_notch_it_glides_to_the_menu_bar_icon(self):
        out, posts = self.run_page(SETUP, {'status': {'x': 1200, 'y': 12}})
        self.assertIsNone(out['sinking'].get('sink'))   # nothing melts at the top
        self.assertAlmostEqual(out['end']['main']['x'], 1200, delta=1)
        self.assertLess(out['end']['alpha'], .05)

    def test_show_intro_ends_with_goodbye(self):
        out, posts = self.run_page(REPLAY, {'mode': 'replay'})
        self.assertTrue(out['left'])
        self.assertEqual([p for p, _ in out['seen']][-2:], ['farewell', 'leaving'])
        self.assertIn({'do': 'play', 'id': 'farewell'}, posts)
        self.assertEqual(posts[-1], {'do': 'done', 'next': 'close'})

    def test_name_is_said_live_and_sound_off_plays_nothing(self):
        out, posts = self.run_page(SKIP, {'name': 'Xasan'})
        self.assertIn({'do': 'say', 'text': 'Hi Xasan, great to meet you!', 'id': 'greet'}, posts)
        out, posts = self.run_page(SKIP, {'name': 'Xasan', 'muted': True})
        self.assertEqual([p for p in posts if p.get('do') in ('play', 'say')], [])
        out, posts = self.run_page(MUTE)
        self.assertEqual(out['muted'], [True, 'Turn sound on'])
        self.assertIn({'do': 'mute', 'on': True}, posts)

    def test_orb_is_bright_inside_and_casts_no_light(self):
        out, _ = self.run_page(ORB)
        for px in out['ring'] + [out['far']]:
            self.assertEqual(px[3], 0, out['ring'])   # no halo, bloom or ring: just outside the outline is empty
        for r, g, b, a in out['inside']:
            self.assertEqual(a, 255)
            self.assertGreater(b, 170)   # blue, and bright: even the shaded side stays a clear blue
            self.assertGreaterEqual(b, r)
            self.assertGreater(0.2126 * r + 0.7152 * g + 0.0722 * b, 60)

    def test_page_is_offline_and_easy_to_rename(self):
        page = (ROOT / 'ui/boot.html').read_text()
        self.assertRegex(page, r"\n  const WORDMARK = 'Kira';")
        for mark in ('/*GLOBE*/', '/*ORB*/', '/*CATALOG*/', '/*VOICE*/'): self.assertIn(mark, page)
        self.assertNotRegex(page, r'https?://(?!www\.w3\.org)')


class BootVoiceTests(unittest.TestCase):
    """The recorded lines match their text, and the timings script finds words where they are."""

    def test_every_line_is_recorded_and_timed(self):
        cfg, voice = json.loads((BOOT / 'lines.json').read_text()), json.loads((BOOT / 'timings.json').read_text())
        self.assertEqual(voice['wordmark'], cfg['wordmark'])
        self.assertEqual(set(voice['lines']), set(cfg['lines']))
        for key, text in cfg['lines'].items():
            line = voice['lines'][key]
            self.assertEqual(line['text'], text.replace('{WORDMARK}', cfg['wordmark']))
            self.assertEqual([w for w, _ in line['words']], line['text'].split())
            starts = [t for _, t in line['words']]
            self.assertEqual(starts, sorted(starts), key)
            self.assertLess(starts[-1], line['ms'] - 150, key)   # the last word starts well before the sound ends
            self.assertTrue((BOOT / f'{key}.m4a').stat().st_size > 5000, key)
        for key in ('rise', 'chime'):
            self.assertTrue((BOOT / f'{key}.m4a').stat().st_size > 5000)
            self.assertGreater(voice['sounds'][key], 2000)

    def test_alignment_follows_pauses_and_loudness(self):
        sys.path.insert(0, str(ROOT / 'tools'))
        try: import make_boot_voice as tool
        finally: sys.path.pop(0)
        rate = 24000
        def burst(ms): t = np.arange(int(rate * ms / 1000)) / rate; return 0.4 * np.sin(2 * np.pi * 220 * t) * np.hanning(len(t))
        quiet = lambda ms: np.zeros(int(rate * ms / 1000))
        # "Hi there. Good day": two words, a 300 ms pause, two words with a short dip between them
        audio = np.concatenate([quiet(100), burst(250), quiet(40), burst(300), quiet(300), burst(280), quiet(60), burst(320), quiet(200)])
        starts = tool.align(audio, rate, ['Hi', 'there.', 'Good', 'day'], [1, 1, 1, 1])
        expected = [100, 390, 990, 1330]
        for got, want in zip(starts, expected):
            self.assertLess(abs(got - want), 70, (starts, expected))

    def test_assets_are_loud_enough_and_soft_enough(self):
        ff = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
        if not Path(ff).exists(): self.skipTest('ffmpeg is not installed')
        for key, lo, hi in (('welcome', -21, -17), ('farewell', -21, -17), ('rise', -28, -24), ('chime', -26, -22)):
            log = subprocess.run([ff, '-hide_banner', '-nostats', '-i', str(BOOT / f'{key}.m4a'), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
            lufs, peak = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', log)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', log)[-1])
            self.assertTrue(lo <= lufs <= hi, (key, lufs))
            self.assertLess(peak, -1, key)


class BootWiringTests(unittest.TestCase):
    """Kira.swift and build.sh: the boot replaces the old splash and ships its sound."""

    def test_swift_and_build_load_the_boot(self):
        swift, build = (ROOT / 'Kira.swift').read_text(), (ROOT / 'build.sh').read_text()
        self.assertFalse((ROOT / 'ui/splash.html').exists())
        self.assertNotIn('splash.html', swift)
        self.assertIn('loadPage(v, "boot.html")', swift)
        self.assertIn('@objc func showIntro() { boot.open() }', swift)
        for mark, part in [('/*ORB*/', 'orb.js'), ('/*CATALOG*/', 'catalog.js'), ('/*VOICE*/', 'boot/timings.json'), ('/*GLOBE*/', 'globe.js')]:
            self.assertIn(f'("{mark}", "{part}")', swift)
        self.assertIn('cp ui/boot/*.m4a ui/boot/timings.json "$APP/Contents/Resources/ui/boot/"', build)
        boot = swift[swift.index('final class Boot:'):swift.index('// The menu bar icon')]
        self.assertNotIn('AVCaptureDevice', boot)   # the boot never touches the microphone
        self.assertNotIn('requestAccess', boot)
        self.assertIn('Int(CGWindowLevelForKey(.dockWindow)) - 1', boot)   # under the Dock, so the drop rises from behind it
        self.assertIn('e["notch"] = ["x": x - f.minX, "w": NotchUI.gap, "h": NotchUI.band, "hardware": NotchUI.notchWidth > 0]', boot)
        self.assertIn('app.js("reset"); app.show(); app.js("msg", line); app.hide(after: 4.5)', boot)   # Kira carries on from the notch


if __name__ == '__main__':
    unittest.main()
