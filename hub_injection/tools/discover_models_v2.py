"""Read actual OpenCode model inventory and public model metadata, no inference."""
import datetime
import json
import os
from pathlib import Path
import runpy
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[1]


def main():
    destination=ROOT/'reports/multi_model_review';destination.mkdir(parents=True,exist_ok=True)
    helper=Path('E:/DevSpaceProjects/opencode_model.txt')
    base=runpy.run_path(str(helper))['BASE']
    key=os.environ.get('OPENCODE_API_KEY','').strip() or (helper.parent/'.opencode-local/api_key.txt').read_text(encoding='utf-8-sig').strip()
    request=urllib.request.Request(base+'models',headers={'Authorization':'Bearer '+key,
        'User-Agent':'codex-opencode-coding-subagent/2.0','x-opencode-session':'kbs-task1-v2-model-discovery'})
    with urllib.request.urlopen(request,timeout=60) as response:
        data=json.load(response);status=response.status
    models=data['data']
    result={'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'base_url':base,'model_endpoint_http_status':status,'catalog_models':models,
        'catalog_is_not_inference_entitlement':True,'authentication':'external key; not recorded',
        'documentation_sources':['https://opencode.ai/v2/docs/console/go/','https://opencode.ai/v2/docs/console/models/'],
        'cost_note':'Published Go token usage prices are accounting units; actual account charge/remaining quota unavailable. No automatic provider fallback.'}
    try:
        with urllib.request.urlopen('https://models.dev/api.json',timeout=60) as response:
            metadata=json.load(response)
        available={m['id'] for m in models};filtered={}
        for provider,record in metadata.items():
            entries={k:v for k,v in record.get('models',{}).items() if k in available}
            if entries and ('opencode' in provider):filtered[provider]=entries
        result['public_capability_metadata']=filtered
        result['public_capability_source']='https://models.dev/api.json'
    except Exception as error:
        result['metadata_error']=str(error).replace(key,'[REDACTED]')
    (destination/'model_inventory.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'http_status':status,'catalog_count':len(models),
        'catalog_keys':list(models[0]),'public_providers':list(result.get('public_capability_metadata',{}))}))


if __name__=='__main__':main()
