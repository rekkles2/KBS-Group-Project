#!/usr/bin/env python3
"""Task-local OpenCode text worker with documented Kimi thinking switch.

Loads only the base URL from the user's inspected helper. Never modifies it.
No automatic retry or provider fallback; no filesystem tools given to model.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import sys
import time
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper', type=Path, required=True)
    parser.add_argument('--key-file', type=Path)
    parser.add_argument('--prompt-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--session-id', required=True)
    parser.add_argument('--model', default='kimi-k2.6')
    parser.add_argument('--protocol',choices=['chat','google'],default='chat')
    parser.add_argument('--thinking', choices=['auto','enabled','disabled'], default='auto')
    parser.add_argument('--image',type=Path,action='append',default=[])
    parser.add_argument('--reasoning-effort',choices=['low','high','max'])
    parser.add_argument('--enable-thinking',choices=['true','false'])
    parser.add_argument('--max-tokens', type=int, default=8000)
    parser.add_argument('--timeout', type=float, default=240)
    args = parser.parse_args()
    key = ''
    started = time.monotonic()
    result = {'ok': False, 'model': args.model, 'session_id': args.session_id,
              'thinking_requested': args.thinking,
              'request_parameters':{'protocol':args.protocol,'reasoning_effort':args.reasoning_effort,
                  'enable_thinking':args.enable_thinking,'max_tokens':args.max_tokens,'timeout':args.timeout},
              'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        if args.timeout <= 0 or args.max_tokens <= 0 or any(c.isspace() for c in args.session_id):
            raise ValueError('Invalid timeout, output budget or session identifier')
        base = runpy.run_path(str(args.helper))['BASE']
        key = os.environ.get('OPENCODE_API_KEY','').strip()
        if not key:
            key_path = args.key_file or args.helper.parent / '.opencode-local/api_key.txt'
            key = key_path.read_text(encoding='utf-8-sig').strip()
        if not key or any(c.isspace() for c in key):
            raise ValueError('Missing or malformed API key')
        prompt = args.prompt_file.read_text(encoding='utf-8-sig')
        result['prompt_sha256'] = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        result['endpoint'] = base + 'chat/completions'
        content=prompt
        if args.image:
            content=[{'type':'text','text':prompt}]
            result['image_sha256']={}
            for path in args.image:
                raw=path.read_bytes()
                mime='image/png' if path.suffix.lower()=='.png' else 'image/jpeg'
                content.append({'type':'image_url','image_url':{'url':'data:'+mime+';base64,'+base64.b64encode(raw).decode('ascii')}})
                result['image_sha256'][path.name]=hashlib.sha256(raw).hexdigest()
        payload = {'model': args.model, 'messages':[{'role':'user','content':content}],
                   'max_tokens':args.max_tokens, 'stream':False}
        if args.thinking!='auto':payload['thinking']={'type':args.thinking}
        if args.reasoning_effort:payload['reasoning_effort']=args.reasoning_effort
        if args.enable_thinking:payload['enable_thinking']=args.enable_thinking=='true'
        if args.protocol=='google':
            # Same OpenCode Go subscription, documented Google API-family route.
            result['endpoint']='https://opencode.ai/inference/go/google/v1beta/models/'+args.model+':generateContent'
            parts=[{'text':prompt}]
            for path in args.image:
                parts.append({'inlineData':{'mimeType':'image/png' if path.suffix.lower()=='.png' else 'image/jpeg',
                                            'data':base64.b64encode(path.read_bytes()).decode('ascii')}})
            payload={'contents':[{'role':'user','parts':parts}],
                     'generationConfig':{'maxOutputTokens':args.max_tokens}}
        request = urllib.request.Request(result['endpoint'],
            headers={'Authorization':'Bearer '+key, 'Content-Type':'application/json',
                     'User-Agent':'codex-opencode-coding-subagent/1.0', 'x-opencode-session':args.session_id},
            data=json.dumps(payload,ensure_ascii=False).encode('utf-8'))
        with urllib.request.urlopen(request,timeout=args.timeout) as response:
            result['http_status'] = response.status
            data = json.load(response)
        if data.get('error'):
            raise ValueError(str(data['error']))
        if args.protocol=='google':
            choice=data['candidates'][0]
            result.update(model=data.get('modelVersion',args.model),response_id=data.get('responseId'),
                          finish_reason='stop' if choice.get('finishReason')=='STOP' else choice.get('finishReason'),
                          usage=data.get('usageMetadata'),cost=data.get('cost'),protocol='google')
            content='\n'.join(p['text'] for p in choice['content']['parts'] if 'text' in p and not p.get('thought'))
        else:
            choice = data['choices'][0]
            result.update(model=data.get('model',args.model),response_id=data.get('id'),
                          finish_reason=choice.get('finish_reason'),usage=data.get('usage'),cost=data.get('cost'))
            content = choice['message'].get('content')
        if not isinstance(content,str) or not content.strip():
            raise ValueError('No usable final text returned')
        result.update(ok=True,text=content)
    except Exception as error:
        if isinstance(error,urllib.error.HTTPError):
            result['http_status'] = error.code
            message = f'HTTP {error.code}: {error.read().decode("utf-8",errors="replace")[:1000]}'
        else:
            message = f'{type(error).__name__}: {error}'
        if key:
            message = message.replace(key,'[REDACTED]')
        result['error'] = re.sub(r'oc_sk_[A-Za-z0-9_-]+','[REDACTED]',message)
    result['elapsed_seconds'] = round(time.monotonic()-started,3)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='text'},ensure_ascii=True))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
