# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Portable bounded speech adapters; the host supplies one selected credential over stdin, never argv."""
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Protocol


class SpeechError(RuntimeError):
    pass


class STTProvider(Protocol):
    def transcribe(self, audio: bytes, options: dict) -> str: ...


class TTSProvider(Protocol):
    def synthesize(self, text: str, options: dict) -> bytes: ...


class AccountProvider(Protocol):
    def status(self) -> dict: ...
    def sign_in(self, method: str) -> dict: ...


class UnavailableAccountProvider:
    def status(self): return {'available': False, 'signedIn': False, 'text': 'Kira accounts are not configured. Continue without an account.'}
    def sign_in(self, method): return {'ok': False, 'error': 'No account backend is configured.'}


def endpoint(base):
    try:
        url=urllib.parse.urlsplit(str(base).strip())
        if url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.query or url.fragment: raise ValueError()
        if url.scheme=='http' and url.hostname not in ('localhost','127.0.0.1','::1'): raise ValueError()
        _=url.port
    except ValueError: raise SpeechError('Use an HTTPS server address, or HTTP on localhost, without credentials or a query.') from None
    return urllib.parse.urlunsplit((url.scheme,url.netloc,url.path.rstrip('/'),'',''))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl): return None


def request(url,headers,body,timeout=10):
    started=time.monotonic(); limit=32*1024*1024
    try:
        opener=urllib.request.build_opener(NoRedirect())
        with opener.open(urllib.request.Request(url,data=body,headers=headers,method='POST'),timeout=timeout) as response:
            chunks=[]; size=0
            while True:
                remaining=timeout-(time.monotonic()-started)
                if remaining<=0: raise SpeechError('The speech provider timed out.')
                sock=getattr(getattr(getattr(response,'fp',None),'raw',None),'_sock',None)
                if sock is not None: sock.settimeout(remaining)
                chunk=response.read1(min(65536,limit-size+1))
                if not chunk: return b''.join(chunks)
                size+=len(chunk)
                if size>limit: raise SpeechError('The speech response was too large.')
                chunks.append(chunk)
    except urllib.error.HTTPError as error:
        reason='The speech provider rejected its key.' if error.code in (401,403) else 'The speech provider reached a usage limit.' if error.code==429 else 'The speech provider could not complete the request.'
        raise SpeechError(reason) from None
    except (OSError,urllib.error.URLError,socket.timeout): raise SpeechError('Could not reach the speech provider. Check the connection and try again.') from None


def multipart(audio,model,language):
    boundary='kira-'+uuid.uuid4().hex
    fields={'model':model,'response_format':'json'}
    if language: fields['language']=language.split('-')[0]
    chunks=[]
    for key,value in fields.items():chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    chunks.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="speech.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode(),audio,f'\r\n--{boundary}--\r\n'.encode()])
    return 'multipart/form-data; boundary='+boundary,b''.join(chunks)


class SpeechService:
    def __init__(self, transport=request): self.transport=transport

    def _call(self,url,headers,body):
        try:return self.transport(url,headers,body,10)
        except SpeechError:raise
        except Exception:raise SpeechError('The speech provider could not complete the request.') from None

    def _key(self,options):
        key=options.get('key','')
        if not isinstance(key,str) or not key or '\r' in key or '\n' in key:raise SpeechError('Save a valid key for the selected speech provider first.')
        return key

    def transcribe(self,provider,audio,options):
        if not isinstance(audio,bytes) or not 0<len(audio)<=25*1024*1024:raise SpeechError('Record between one byte and 25 MB of WAV audio.')
        if provider=='whisper':return whisper_transcribe(audio,options)
        key=self._key(options); language=str(options.get('language','en-US'))
        if not re.fullmatch(r'[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8}){0,2}',language):raise SpeechError('Choose a valid speech language.')
        if provider=='deepgram':
            url='https://api.deepgram.com/v1/listen?'+urllib.parse.urlencode({'model':options.get('model') or 'nova-3','language':language.split('-')[0],'smart_format':'true'})
            headers={'Authorization':'Token '+key,'Content-Type':'audio/wav'};body=audio
        elif provider in ('openai','custom'):
            base='https://api.openai.com/v1' if provider=='openai' else endpoint(options.get('base',''))
            content,body=multipart(audio,str(options.get('model') or 'gpt-4o-mini-transcribe'),language)
            url=base+'/audio/transcriptions';headers={'Authorization':'Bearer '+key,'Content-Type':content}
        else:raise SpeechError('This provider does not implement speech recognition.')
        raw=self._call(url,headers,body)
        try:
            data=json.loads(raw)
            text=data['results']['channels'][0]['alternatives'][0]['transcript'] if provider=='deepgram' else data['text']
            if not isinstance(text,str):raise ValueError()
            return text.strip()
        except (ValueError,KeyError,TypeError,IndexError):raise SpeechError('The speech provider returned an invalid transcript.') from None

    def synthesize(self,provider,text,options):
        if not isinstance(text,str) or not text.strip() or len(text)>4000:raise SpeechError('Use between 1 and 4,000 characters for speech.')
        key=self._key(options)
        headers={'Content-Type':'application/json'}
        if provider=='deepgram':
            url='https://api.deepgram.com/v1/speak?'+urllib.parse.urlencode({'model':options.get('model') or 'aura-2-thalia-en','encoding':'linear16','container':'wav'})
            headers['Authorization']='Token '+key;body={'text':text}
        elif provider in ('openai','custom'):
            base='https://api.openai.com/v1' if provider=='openai' else endpoint(options.get('base',''))
            url=base+'/audio/speech';headers['Authorization']='Bearer '+key
            body={'model':options.get('model') or 'gpt-4o-mini-tts','voice':options.get('voice') or 'coral','input':text,'response_format':'wav'}
        elif provider=='elevenlabs':
            voice=options.get('voice','')
            if not isinstance(voice,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',voice):raise SpeechError('Choose an ElevenLabs voice ID first.')
            url='https://api.elevenlabs.io/v1/text-to-speech/'+voice+'?output_format=mp3_44100_128';headers['xi-api-key']=key
            body={'text':text,'model_id':options.get('model') or 'eleven_multilingual_v2'}
        else:raise SpeechError('This provider does not implement speech synthesis.')
        raw=self._call(url,headers,json.dumps(body,ensure_ascii=False).encode())
        if not isinstance(raw,bytes) or not raw or raw.lstrip().startswith((b'{',b'[',b'<')):raise SpeechError('The speech provider returned no playable audio.')
        return raw


def worker(data):
    """The native host supplies private paths and one selected key; responses never include configuration."""
    import os
    import tempfile
    from pathlib import Path
    if not isinstance(data,dict):raise SpeechError('Invalid speech request.')
    service=SpeechService(); mode=data.get('mode');provider=data.get('provider');options=data.get('options')
    if not isinstance(options,dict):raise SpeechError('Invalid speech options.')
    root=Path(tempfile.gettempdir()).resolve()
    def private_path(value):
        path=Path(str(value))
        if path.is_symlink() or path.parent.resolve()!=root or not path.name.startswith('kira-speech-'):raise SpeechError('Invalid temporary speech file.')
        return path
    if mode=='stt':
        path=private_path(data.get('path',''))
        if path.stat().st_size>25*1024*1024:raise SpeechError('The speech recording is too large.')
        return {'text':service.transcribe(provider,path.read_bytes(),options)}
    if mode=='tts':
        path=private_path(data.get('path',''));audio=service.synthesize(provider,data.get('text'),options)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,'wb') as output:output.write(audio)
        except BaseException:
            path.unlink(missing_ok=True);raise
        return {'path':str(path)}
    raise SpeechError('Unknown speech operation.')


def model_registry():
    from pathlib import Path
    source=(Path(__file__).parent/'ui/catalog.js').read_text().split('const WHISPER = [',1)[1].split('];',1)[0]
    return {key:{'file':file,'bytes':int(size),'sha256':digest} for key,file,size,digest in re.findall(r"id: '([^']+)', file: '([^']+)', bytes: (\d+), sha256: '([0-9a-f]{64})'",source)}


def download_model(identifier,folder,emit=lambda value:None,registry=None,opener=urllib.request.urlopen):
    import fcntl
    import os
    from pathlib import Path
    registry=model_registry() if registry is None else registry
    if identifier not in registry:raise SpeechError('Choose a supported local model.')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=folder/(registry[identifier]['file']+'.lock')
    with os.fdopen(os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600),'wb') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SpeechError('This model is already being downloaded. Wait or pause the active download.') from None
        return _download_model(identifier,folder,emit,registry,opener)


def _download_model(identifier,folder,emit=lambda value:None,registry=None,opener=urllib.request.urlopen):
    import hashlib
    import os
    import shutil
    from pathlib import Path
    registry=model_registry() if registry is None else registry
    if identifier not in registry:raise SpeechError('Choose a supported local model.')
    item=registry[identifier];folder=Path(folder);folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    target=folder/item['file'];partial=target.with_suffix(target.suffix+'.part')
    if target.is_symlink() or partial.is_symlink():raise SpeechError('A model file cannot be a symbolic link.')
    size=partial.stat().st_size if partial.exists() else 0
    if size>item['bytes']:partial.unlink();size=0
    if shutil.disk_usage(folder).free<item['bytes']-size+16*1024*1024:raise SpeechError('There is not enough free disk space for this model.')
    if size<item['bytes']:
        url='https://huggingface.co/ggerganov/whisper.cpp/resolve/main/'+urllib.parse.quote(item['file'])
        req=urllib.request.Request(url,headers={'Range':f'bytes={size}-'} if size else {})
        try:
            with opener(req,timeout=15) as response:
                resumed=size and getattr(response,'status',200)==206
                if resumed and not response.headers.get('Content-Range','').startswith(f'bytes {size}-'):raise SpeechError('The model server returned an invalid resume range.')
                if not resumed:size=0
                flags=os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW|(os.O_APPEND if resumed else os.O_TRUNC)
                with os.fdopen(os.open(partial,flags,0o600),'wb') as output:
                    while True:
                        chunk=response.read(1024*1024)
                        if not chunk:break
                        size+=len(chunk)
                        if size>item['bytes']:raise SpeechError('The model response exceeded its expected size.')
                        output.write(chunk);emit({'event':'progress','bytes':size,'total':item['bytes']})
        except SpeechError:raise
        except (OSError,urllib.error.URLError):raise SpeechError('The model download stopped. Resume it to keep the downloaded portion.') from None
    digest=hashlib.sha256()
    with partial.open('rb') as file:
        for chunk in iter(lambda:file.read(1024*1024),b''):digest.update(chunk)
    if size!=item['bytes'] or digest.hexdigest()!=item['sha256']:
        partial.unlink(missing_ok=True);raise SpeechError('The model checksum did not match. The incomplete file was removed.')
    os.replace(partial,target)
    receipt=target.with_suffix(target.suffix+'.verified.json');temporary=receipt.with_suffix('.tmp')
    temporary.write_text(json.dumps({'sha256':item['sha256'],'mtime_ns':target.stat().st_mtime_ns}));os.chmod(temporary,0o600);os.replace(temporary,receipt)
    emit({'event':'ready','id':identifier});return target


def whisper_transcribe(audio,options):
    import os
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path
    model=options.get('whisperModel') or 'base';registry=model_registry()
    if model not in registry:raise SpeechError('Choose a supported Whisper model.')
    root=Path(os.environ.get('KIRA_DIR') or Path.home()/'.config/kira')/'models'
    path=root/registry[model]['file'];binary=shutil.which('whisper-cli')
    if not binary or model not in model_status(root)['models']:raise SpeechError('Install whisper.cpp and download a verified model first.')
    fd,name=tempfile.mkstemp(prefix='kira-speech-',suffix='.wav');os.close(fd)
    output=name+'.out'
    try:
        Path(name).write_bytes(audio)
        result=subprocess.run([binary,'-m',str(path),'-f',name,'-l',str(options.get('language','en')).split('-')[0],'-otxt','-of',output,'-np'],capture_output=True,timeout=10)
        if result.returncode:raise SpeechError('The local speech model could not transcribe the recording.')
        return Path(output+'.txt').read_text().strip()
    except (OSError,subprocess.TimeoutExpired):raise SpeechError('The local speech model was unavailable or timed out.') from None
    finally:
        for file in (name,output+'.txt'):Path(file).unlink(missing_ok=True)


def model_status(folder):
    import shutil
    from pathlib import Path
    folder=Path(folder);registry=model_registry();available=[]
    for identifier,item in registry.items():
        path=folder/item['file'];receipt=path.with_suffix(path.suffix+'.verified.json')
        try:
            meta=json.loads(receipt.read_text());info=path.stat()
            if not path.is_symlink() and info.st_size==item['bytes'] and meta.get('sha256')==item['sha256'] and meta.get('mtime_ns')==info.st_mtime_ns:available.append(identifier)
        except (OSError,ValueError,TypeError):pass
    return {'installed':bool(shutil.which('whisper-cli')),'models':available,'files':list(registry),'free':shutil.disk_usage(folder if folder.exists() else folder.parent).free}


def model_worker(data,emit):
    import os
    from pathlib import Path
    folder=Path(os.environ.get('KIRA_DIR') or Path.home()/'.config/kira')/'models'
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    if data.get('action')=='status':return model_status(folder)
    identifier=data.get('id');registry=model_registry()
    if identifier not in registry:raise SpeechError('Unknown local model.')
    if data.get('action')=='download':
        path=download_model(identifier,folder,emit)
        return {'ready':identifier,**model_status(folder)}
    if data.get('action')=='delete':
        path=folder/registry[identifier]['file']
        for file in (path,path.with_suffix(path.suffix+'.part'),path.with_suffix(path.suffix+'.verified.json')):file.unlink(missing_ok=True)
        return model_status(folder)
    raise SpeechError('Unknown model operation.')
