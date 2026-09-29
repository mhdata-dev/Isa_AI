import os
from collections import defaultdict
import psycopg
from psycopg.rows import dict_row
from mcp.server import MCPServer
from common import read_secret, date_range, daily_summary

mcp=MCPServer('isa-garmin')


def query(sql,parameters=()):
    with psycopg.connect(host=os.environ['PGHOST'],dbname=os.environ['PGDATABASE'],user=os.environ['PGUSER'],password=read_secret('PG_PASSWORD_FILE'),connect_timeout=5,row_factory=dict_row) as connection:
        return connection.execute(sql,parameters).fetchall()


@mcp.tool()
def garmin_sync_status() -> dict:
    """Read Garmin synchronization status. Empty storage means no imported data, not zero activity."""
    counts=query('SELECT count(DISTINCT day) AS days, max(fetched_at) AS last_fetch FROM health.records')[0]
    return {'source':'Garmin Connect','days_with_data':counts['days'],'last_fetch':str(counts['last_fetch']) if counts['last_fetch'] else None,'recent_attempts':query('SELECT day::text, attempted_at::text, errors, successful_kinds FROM health.sync_status ORDER BY attempted_at DESC LIMIT 7')}


@mcp.tool()
def garmin_daily_summary(start: str, end: str) -> dict:
    """Read up to 31 days of Garmin activity, sleep, HRV, heart rate, stress and Body Battery summaries. Dates use Europe/Madrid; sleep is labeled by Garmin's date, normally the wake date. Null means unavailable. Always check freshness and errors; this is stored data, not a live watch reading."""
    first,last=date_range(start,end)
    rows=query('SELECT day, kind, payload, fetched_at FROM health.records WHERE day BETWEEN %s AND %s ORDER BY day,kind',(first,last))
    grouped=defaultdict(list)
    for row in rows:
        grouped[row['day']].append(row)
    return {'source':'Garmin Connect','timezone':'Europe/Madrid','days':[daily_summary(day,records) for day,records in grouped.items()],'sync_attempts':query('SELECT day::text,attempted_at::text,errors FROM health.sync_status WHERE day BETWEEN %s AND %s ORDER BY day',(first,last))}


@mcp.tool()
def garmin_activities(start: str, end: str, limit: int=50, offset: int=0) -> dict:
    """List stored Garmin activities for up to 31 days. Duration is seconds, distance meters, heart rate bpm. Pagination is stable by date and ID. No GPS tracks are returned."""
    first,last=date_range(start,end)
    if not 1<=limit<=100 or not 0<=offset<=10000:
        raise ValueError('Limit must be 1..100 and offset 0..10000.')
    rows=query('SELECT activity_id,day::text,payload,fetched_at::text FROM health.activities WHERE day BETWEEN %s AND %s ORDER BY day DESC,activity_id LIMIT %s OFFSET %s',(first,last,limit+1,offset))
    items=[]
    for row in rows[:limit]:
        p=row['payload']
        items.append({'id':row['activity_id'],'date':row['day'],'name':p.get('activityName'),'type':(p.get('activityType') or {}).get('typeKey'),'start_local':p.get('startTimeLocal'),'start_utc':p.get('startTimeGMT'),'duration_seconds':p.get('duration'),'distance_m':p.get('distance'),'average_heart_rate_bpm':p.get('averageHR'),'max_heart_rate_bpm':p.get('maxHR'),'calories_kcal':p.get('calories'),'fetched_at':row['fetched_at']})
    return {'activities':items,'next_offset':offset+limit if len(rows)>limit else None,'source':'Garmin Connect'}


if __name__=='__main__':
    mcp.run(transport='streamable-http',host='0.0.0.0',port=8000)
