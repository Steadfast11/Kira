# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Speech contracts use captured fake HTTP; no external provider requests."""
import unittest
import speech_runtime as voice


class SpeechProviderTests(unittest.TestCase):
    def test_keys_are_sent_only_to_the_selected_provider(self):
        seen=[]
        def transport(url,headers,body,timeout):
            seen.append((url,headers,body,timeout))
            return b'{"results":{"channels":[{"alternatives":[{"transcript":"hello"}]}]}}'
        service=voice.SpeechService(transport)
        self.assertEqual(service.transcribe('deepgram',b'RIFFfixture',{'key':'fixture-secret','language':'en-US'}),'hello')
        self.assertTrue(seen[0][0].startswith('https://api.deepgram.com/v1/listen?'))
        self.assertEqual(seen[0][1]['Authorization'],'Token fixture-secret')
        self.assertNotIn(b'fixture-secret',seen[0][2])

    def test_openai_audio_contracts_and_custom_url(self):
        seen=[]
        def transport(url,headers,body,timeout):
            seen.append((url,headers,body));return b'{"text":"spoken"}' if 'transcriptions' in url else b'RIFFaudio'
        service=voice.SpeechService(transport)
        self.assertEqual(service.transcribe('openai',b'RIFFfixture',{'key':'k','model':'whisper-1'}),'spoken')
        self.assertIn(b'name="file"; filename="speech.wav"',seen[0][2])
        self.assertEqual(service.synthesize('custom','hello',{'key':'local','base':'http://127.0.0.1:8000/v1','model':'local','voice':'one'}),b'RIFFaudio')
        self.assertEqual(seen[-1][0],'http://127.0.0.1:8000/v1/audio/speech')

    def test_elevenlabs_requires_a_voice_and_never_returns_fake_audio(self):
        seen=[]
        service=voice.SpeechService(lambda *args:seen.append(args) or b'audio')
        with self.assertRaises(voice.SpeechError):service.synthesize('elevenlabs','hello',{'key':'k'})
        self.assertFalse(seen)
        self.assertEqual(service.synthesize('elevenlabs','hello',{'key':'k','voice':'voice_1'}),b'audio')
        self.assertEqual(seen[-1][1]['xi-api-key'],'k')

    def test_errors_do_not_echo_provider_response_or_key(self):
        service=voice.SpeechService(lambda *args:(_ for _ in ()).throw(RuntimeError('fixture-secret')))
        with self.assertRaises(voice.SpeechError) as error:service.synthesize('openai','hello',{'key':'fixture-secret'})
        self.assertNotIn('fixture-secret',str(error.exception))

    def test_remote_http_and_credential_urls_are_rejected(self):
        for base in ('http://example.com','https://user:password@example.com','file:///tmp/a','https://example.com?key=secret'):
            with self.subTest(base=base), self.assertRaises(voice.SpeechError):voice.endpoint(base)

    def test_malformed_transcript_and_empty_audio_are_not_success(self):
        for output in (b'[]',b'{"text":3}',b'not json'):
            with self.subTest(output=output),self.assertRaises(voice.SpeechError):voice.SpeechService(lambda *a:output).transcribe('openai',b'RIFFx',{'key':'k'})
        with self.assertRaises(voice.SpeechError):voice.SpeechService(lambda *a:b'').synthesize('openai','hello',{'key':'k'})

    def test_account_contract_never_fakes_sign_in(self):
        account=voice.UnavailableAccountProvider()
        self.assertFalse(account.status()['available'])
        self.assertFalse(account.sign_in('google')['ok'])

    def test_download_verifies_before_promoting_and_removes_corruption(self):
        import hashlib
        import io
        import tempfile
        from pathlib import Path
        class Reply(io.BytesIO):
            status=200;headers={}
        registry={'tiny':{'file':'ggml-tiny.bin','bytes':7,'sha256':hashlib.sha256(b'fixture').hexdigest()}}
        with tempfile.TemporaryDirectory() as folder:
            path=voice.download_model('tiny',Path(folder),registry=registry,opener=lambda req,timeout:Reply(b'fixture'))
            self.assertEqual(path.read_bytes(),b'fixture')
            path.unlink()
            with self.assertRaises(voice.SpeechError):voice.download_model('tiny',Path(folder),registry=registry,opener=lambda req,timeout:Reply(b'corrupt'))
            self.assertFalse(path.exists());self.assertFalse(path.with_suffix('.bin.part').exists())

    def test_concurrent_model_download_is_rejected_before_writing(self):
        import hashlib
        import io
        import tempfile
        from pathlib import Path
        class Reply(io.BytesIO):
            status=200;headers={}
        registry={'tiny':{'file':'ggml-tiny.bin','bytes':7,'sha256':hashlib.sha256(b'fixture').hexdigest()}}
        with tempfile.TemporaryDirectory() as folder:
            def opener(req,timeout):
                with self.assertRaisesRegex(voice.SpeechError,'already'):
                    voice.download_model('tiny',Path(folder),registry=registry,opener=lambda *a,**kw:Reply(b'fixture'))
                return Reply(b'fixture')
            result=voice.download_model('tiny',Path(folder),registry=registry,opener=opener)
            self.assertEqual(result.read_bytes(),b'fixture')
