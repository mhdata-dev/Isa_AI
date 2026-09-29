"""Probe Code → HTTP → parameterized PostgreSQL without importing health data."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'n8n'))
from definition import build
from run_sync import run
from bootstrap_n8n import import_json

workflow=build()
workflow['id']='isaGarminProbe'
workflow['name']='Isa Garmin integration probe (temporary)'
workflow['nodes']=[n for n in workflow['nodes'] if n['name'] in ('Manual','Last seven days','Fetch daily snapshot','Store snapshot')]
workflow['connections']={
    'Manual':{'main':[[{'node':'Last seven days','type':'main','index':0}]]},
    'Last seven days':{'main':[[{'node':'Fetch daily snapshot','type':'main','index':0}]]},
    'Fetch daily snapshot':{'main':[[{'node':'Store snapshot','type':'main','index':0}]]},
}
for node in workflow['nodes']:
    if node['name']=='Fetch daily snapshot': node['parameters']['url']='http://garmin-collector:8000/healthz'
    if node['name']=='Store snapshot': node['parameters']['query']="SELECT $1::jsonb->>'status' AS collector_health;"
psql=['docker','compose','exec','-T','postgres','psql','-X','-U','postgres','-d','n8n','-v','ON_ERROR_STOP=1','-At']
existing=subprocess.run(psql,cwd=ROOT,input="SELECT count(*) FROM workflow_entity WHERE id='isaGarminProbe';",text=True,capture_output=True,check=True)
assert existing.stdout.strip()=='0','Existing probe ID must be reviewed before retrying.'
import_json('workflow',[workflow])
try:
    outcome=run(['--id=isaGarminProbe'],probe=True)
    assert outcome['stored_snapshots']==7,outcome
    print('Workflow probe passed: 7 Code → HTTP → parameterized SQL items, no stored health records.')
finally:
    cleanup="DELETE FROM workflow_entity WHERE id='isaGarminProbe' AND name='Isa Garmin integration probe (temporary)' AND active=false;"
    subprocess.run(psql,cwd=ROOT,input=cleanup,text=True,capture_output=True,check=True)
