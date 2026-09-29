"""Read-only installation checks; output only operational metadata."""
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]


def command(args,input=None):
    return subprocess.run(args,cwd=ROOT,input=input,text=True,capture_output=True,check=True).stdout


def sql(database,query):
    result=command(['docker','compose','exec','-T','postgres','psql','-X','-U','postgres','-d',database,'-At','-v','ON_ERROR_STOP=1'],query)
    return json.loads(result.strip())


result={}
with urlopen('http://127.0.0.1:5678/healthz/readiness',timeout=10) as response:
    result['n8n_http']=response.status
with urlopen('http://127.0.0.1:5678/rest/settings',timeout=10) as response:
    settings=json.load(response).get('data',{})
    result['n8n_owner_setup_required']=settings.get('userManagement',{}).get('showSetupOnFirstLoad')
result['database']=sql('garmin',"SELECT json_build_object('version',current_setting('server_version'),'record_count',(SELECT count(*) FROM health.records),'activity_count',(SELECT count(*) FROM health.activities));")
result['workflow']=sql('n8n',"SELECT json_build_object('id',id,'active',active,'published',\"activeVersionId\" IS NOT NULL) FROM workflow_entity WHERE id='isaGarminDailySync';")
request={'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'isa-connectivity-test','version':'1'}}}
response=command(['docker','exec','warp-drive-pilot-mira-1','curl','-fsS','-X','POST','-H','Content-Type: application/json','-H','Accept: application/json, text/event-stream','--data-binary',json.dumps(request),'http://isa-garmin-mcp:8000/mcp'])
assert 'isa-garmin' in response,'Mira could not initialize the Garmin MCP.'
result['mira_to_mcp']='initialized'
baseline=ROOT/'runtime/existing-containers.before.txt'
if baseline.exists():
    previous=baseline.read_text().splitlines()
    unchanged=[]
    for row in previous:
        name=row.split(' | ')[0]
        current=command(['docker','inspect',name,'--format','{{.Name}} | {{.Id}} | {{.State.StartedAt}}']).strip()
        assert current==row,'Existing container changed: '+name
        unchanged.append(name)
    result['original_container_ids_and_start_times_unchanged']=unchanged
print(json.dumps(result,indent=2))
