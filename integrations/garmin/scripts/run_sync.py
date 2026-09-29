"""Run the stored workflow without printing Garmin payloads in terminal logs."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def run(extra_args, probe=False):
    result=subprocess.run(['docker','compose','exec','-T','-e','N8N_RUNNERS_BROKER_PORT=5680','n8n','n8n','execute',*extra_args,'--rawOutput'],cwd=ROOT,capture_output=True,text=True,timeout=1900)
    # Some startup messages precede raw JSON. Parse, but never echo those messages
    # or the execution payload, which can contain personal Garmin records.
    execution=None
    decoder=json.JSONDecoder()
    for index,char in enumerate(result.stdout):
        if char=='{':
            try:
                item,_=decoder.raw_decode(result.stdout[index:])
                if isinstance(item,dict) and ('data' in item or 'resultData' in item):
                    execution=item
                    break
            except json.JSONDecodeError:
                pass
    if result.returncode or execution is None:
        raise RuntimeError('Workflow execution failed. No private execution data was printed.')
    data=execution.get('data',execution).get('resultData',{})
    if data.get('error'):
        raise RuntimeError('Workflow reported an error. Review the node configuration in n8n.')
    runs=data.get('runData',{})
    if probe:
        items=[item for run in runs.get('Store snapshot',[]) for group in run.get('data',{}).get('main',[]) for item in group]
        if len(items)!=7 or any(item.get('json',{}).get('collector_health')!='ok' for item in items):
            raise RuntimeError('Workflow probe returned an unexpected SQL parameter value.')
    return {'status':'ok','completed_nodes':list(runs),'stored_snapshots':sum(len(group) for run in runs.get('Store snapshot',[]) for group in run.get('data',{}).get('main',[]))}


if __name__=='__main__':
    try:
        print(json.dumps(run(['--id=isaGarminDailySync']),ensure_ascii=False))
    except (RuntimeError,subprocess.TimeoutExpired) as error:
        raise SystemExit(str(error)) from None
