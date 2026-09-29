"""Protocol smoke test; never prints personal records."""
import asyncio
import json
from mcp import Client


async def main():
    async with Client('http://isa-garmin-mcp:8000/mcp') as client:
        result=await client.list_tools()
        tools=result.tools if hasattr(result,'tools') else result
        names=sorted(tool.name for tool in tools)
        assert names==['garmin_activities','garmin_daily_summary','garmin_sync_status'],names
        status=await client.call_tool('garmin_sync_status',{})
        data=status.structured_content
        if data is None and status.content:
            data=json.loads(status.content[0].text)
        if isinstance(data,dict) and 'result' in data:
            data=data['result']
        assert isinstance(data,dict) and 'days_with_data' in data
        print(json.dumps({'mcp':'ok','tools':names,'days_with_data':data['days_with_data']}))


if __name__=='__main__': asyncio.run(main())
