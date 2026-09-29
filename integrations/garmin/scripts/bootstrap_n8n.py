"""Import credentials directly into n8n. Never export decrypted credentials."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'n8n'))
from definition import build,WORKFLOW_ID


def docker(*args,input=None):
    result=subprocess.run(['docker','compose',*args],cwd=ROOT,input=input,text=True,capture_output=True)
    if result.returncode:
        # Do not echo arbitrary CLI output when processing credential data.
        raise SystemExit('n8n setup command failed: '+ ' '.join(args[:4]))
    return result.stdout


def import_json(kind,data):
    path='/tmp/isa-'+kind+'.json'
    docker('exec','-T','n8n','sh','-c',f'umask 077; cat > {path}',input=json.dumps(data))
    try:
        docker('exec','-T','n8n','n8n','import:'+kind,'--input='+path)
    finally:
        docker('exec','-T','n8n','rm','-f',path)


def main():
    marker=ROOT/'runtime/n8n-bootstrap-complete'
    if marker.exists():
        raise SystemExit('Already imported. Use an explicit workflow update; credentials were preserved.')
    credentials=[
        {'id':'isaGarminCollector','name':'Isa Garmin collector','type':'httpHeaderAuth','data':{'name':'Authorization','value':'Bearer '+(ROOT/'secrets/collector_api').read_text().strip()}},
        {'id':'isaGarminWriter','name':'Isa Garmin ingestion','type':'postgres','data':{'host':'postgres','database':'garmin','user':'garmin_writer','password':(ROOT/'secrets/garmin_writer').read_text().strip(),'port':5432,'ssl':'disable'}},
    ]
    import_json('credentials',credentials)
    del credentials
    import_json('workflow',[build()])
    marker.write_text(WORKFLOW_ID+'\n')
    print('Workflow and encrypted credentials imported. No Garmin login was attempted.')


if __name__=='__main__': main()
