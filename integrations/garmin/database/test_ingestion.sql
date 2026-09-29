\set ON_ERROR_STOP on
BEGIN;
SELECT health.ingest_snapshot('{"schema_version":1,"date":"2000-01-01","fetched_at":"2000-01-02T00:00:00Z","records":[{"kind":"stats","payload":{"totalSteps":42}},{"kind":"activities","payload":[{"activityId":9990000001,"distance":1200}]}],"errors":[]}');
SELECT health.ingest_snapshot('{"schema_version":1,"date":"2000-01-01","fetched_at":"2000-01-02T01:00:00Z","records":[{"kind":"stats","payload":{"totalSteps":43}},{"kind":"activities","payload":[{"activityId":9990000001,"distance":1250}]}],"errors":[]}');
SELECT health.ingest_snapshot('{"schema_version":1,"date":"2000-01-01","fetched_at":"2000-01-01T00:00:00Z","records":[{"kind":"stats","payload":{"totalSteps":1}}],"errors":[]}');
DO $$ BEGIN
  IF (SELECT count(*) FROM health.records WHERE day='2000-01-01')<>2 THEN RAISE EXCEPTION 'Duplicate daily records'; END IF;
  IF (SELECT count(*) FROM health.activities WHERE activity_id='9990000001')<>1 THEN RAISE EXCEPTION 'Duplicate activities'; END IF;
  IF (SELECT payload->>'totalSteps' FROM health.records WHERE day='2000-01-01' AND kind='stats')<>'43' THEN RAISE EXCEPTION 'Stale update overwrote newer data'; END IF;
END $$;
SELECT health.ingest_snapshot('{"schema_version":1,"date":"2000-01-01","fetched_at":"2000-01-02T02:00:00Z","records":[],"errors":[{"kind":"stats","code":"upstream_unavailable"}]}');
DO $$ BEGIN
  IF (SELECT payload->>'totalSteps' FROM health.records WHERE day='2000-01-01' AND kind='stats')<>'43' THEN RAISE EXCEPTION 'Failed metric erased stored data'; END IF;
  BEGIN
    PERFORM health.ingest_snapshot('{"schema_version":1,"date":"2000-01-01","fetched_at":"2000-01-02T03:00:00Z","records":[{"kind":"forbidden","payload":{}}],"errors":[]}');
    RAISE EXCEPTION 'Unknown kind was accepted';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;
SET LOCAL ROLE garmin_reader;
SELECT count(*) FROM health.records;
DO $$ BEGIN
  BEGIN
    DELETE FROM health.records;
    RAISE EXCEPTION 'Reader unexpectedly has write access';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    PERFORM health.ingest_snapshot('{}');
    RAISE EXCEPTION 'Reader unexpectedly has ingestion access';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;
RESET ROLE;
SET LOCAL ROLE garmin_writer;
DO $$ BEGIN
  BEGIN
    PERFORM count(*) FROM health.records;
    RAISE EXCEPTION 'Writer unexpectedly can read health records';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;
RESET ROLE;
ROLLBACK;
