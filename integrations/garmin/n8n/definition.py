"""Build the workflow for import. Versioned JSON is subsequently exported by n8n."""
import json
import uuid

WORKFLOW_ID='isaGarminDailySync'
HTTP_CREDENTIAL={'httpHeaderAuth':{'id':'isaGarminCollector','name':'Isa Garmin collector'}}
SQL_CREDENTIAL={'postgres':{'id':'isaGarminWriter','name':'Isa Garmin ingestion'}}


def build():
    def node(name,type,version,parameters,x,credentials=None):
        item={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'isa/garmin/'+name)),'name':name,'type':type,'typeVersion':version,'position':[x,0],'parameters':parameters}
        if credentials: item['credentials']=credentials
        return item
    nodes=[
        node('Manual','n8n-nodes-base.manualTrigger',1,{},0),
        node('Daily schedule','n8n-nodes-base.scheduleTrigger',1.2,{'rule':{'interval':[{'field':'cronExpression','expression':'15 8,20 * * *'}]}},0),
        node('Garmin session','n8n-nodes-base.httpRequest',4.2,{'url':'http://garmin-collector:8000/status','authentication':'genericCredentialType','genericAuthType':'httpHeaderAuth','options':{'timeout':15000}},240,HTTP_CREDENTIAL),
        node('Session available','n8n-nodes-base.if',2.2,{'conditions':{'options':{'caseSensitive':True,'leftValue':'','typeValidation':'strict','version':2},'conditions':[{'id':'session','leftValue':'={{ $json.session_available }}','rightValue':'','operator':{'type':'boolean','operation':'true','singleValue':True}},{'id':'cooldown','leftValue':'={{ $json.rate_limit_cooldown }}','rightValue':'','operator':{'type':'boolean','operation':'false','singleValue':True}}],'combinator':'and'},'options':{}},480),
        node('Last seven days','n8n-nodes-base.code',2,{'jsCode':"return Array.from({length:7}, (_,i)=>({json:{date:$now.setZone('Europe/Madrid').minus({days:6-i}).toISODate()}}));"},720),
        node('Fetch daily snapshot','n8n-nodes-base.httpRequest',4.2,{'url':"={{ 'http://garmin-collector:8000/snapshot/' + $json.date }}",'authentication':'genericCredentialType','genericAuthType':'httpHeaderAuth','options':{'timeout':300000,'batching':{'batch':{'batchSize':1,'batchInterval':2000}}}},960,HTTP_CREDENTIAL),
        node('Store snapshot','n8n-nodes-base.postgres',2.6,{'operation':'executeQuery','query':'SELECT health.ingest_snapshot($1::jsonb) AS result;','options':{'queryReplacement':'={{ [JSON.stringify($json)] }}','queryBatching':'independently'}},1200,SQL_CREDENTIAL),
    ]
    edges={'Manual':{'main':[[{'node':'Garmin session','type':'main','index':0}]]},'Daily schedule':{'main':[[{'node':'Garmin session','type':'main','index':0}]]},'Garmin session':{'main':[[{'node':'Session available','type':'main','index':0}]]},'Session available':{'main':[[{'node':'Last seven days','type':'main','index':0}],[]]},'Last seven days':{'main':[[{'node':'Fetch daily snapshot','type':'main','index':0}]]},'Fetch daily snapshot':{'main':[[{'node':'Store snapshot','type':'main','index':0}]]}}
    return {'id':WORKFLOW_ID,'name':'Isa - Garmin daily synchronization','active':False,'nodes':nodes,'connections':edges,'settings':{'executionOrder':'v1','timezone':'Europe/Madrid','executionTimeout':1800,'saveDataSuccessExecution':'none','saveDataErrorExecution':'none','saveManualExecutions':False},'pinData':{}}


if __name__=='__main__': print(json.dumps([build()],indent=2))
