BEGIN;
CREATE SCHEMA health;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA health TO garmin_writer, garmin_reader;

CREATE TABLE health.records (
    day date NOT NULL,
    kind text NOT NULL CHECK (kind IN ('stats','sleep','heart_rate','hrv','stress','body_battery','activities')),
    payload jsonb NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY(day, kind)
);
CREATE TABLE health.activities (
    activity_id text PRIMARY KEY,
    day date NOT NULL,
    payload jsonb NOT NULL,
    fetched_at timestamptz NOT NULL
);
CREATE INDEX activities_day ON health.activities(day);
CREATE TABLE health.sync_status (
    day date PRIMARY KEY,
    attempted_at timestamptz NOT NULL,
    errors jsonb NOT NULL DEFAULT '[]',
    successful_kinds jsonb NOT NULL DEFAULT '[]'
);

CREATE FUNCTION health.ingest_snapshot(snapshot jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, health AS $$
DECLARE
    d date;
    fetched timestamptz;
    record jsonb;
    activity jsonb;
    kinds jsonb := '[]'::jsonb;
BEGIN
    IF snapshot->>'schema_version' IS DISTINCT FROM '1'
       OR jsonb_typeof(snapshot->'records') IS DISTINCT FROM 'array'
       OR jsonb_typeof(snapshot->'errors') IS DISTINCT FROM 'array'
       OR octet_length(snapshot::text) > 10485760 THEN
        RAISE EXCEPTION 'Invalid Garmin snapshot';
    END IF;
    d := (snapshot->>'date')::date;
    fetched := (snapshot->>'fetched_at')::timestamptz;
    IF d IS NULL OR fetched IS NULL OR d > (now() AT TIME ZONE 'Europe/Madrid')::date THEN
        RAISE EXCEPTION 'Invalid snapshot date';
    END IF;
    FOR record IN SELECT value FROM jsonb_array_elements(snapshot->'records') LOOP
        IF NOT (record ? 'payload') OR record->'payload' = 'null'::jsonb THEN
            RAISE EXCEPTION 'Record without payload';
        END IF;
        INSERT INTO health.records(day, kind, payload, fetched_at)
        VALUES(d, record->>'kind', record->'payload', fetched)
        ON CONFLICT(day,kind) DO UPDATE SET payload=EXCLUDED.payload, fetched_at=EXCLUDED.fetched_at
        WHERE EXCLUDED.fetched_at >= records.fetched_at;
        kinds := kinds || jsonb_build_array(record->>'kind');
        IF record->>'kind' = 'activities' THEN
            IF jsonb_typeof(record->'payload') IS DISTINCT FROM 'array' THEN
                RAISE EXCEPTION 'Activities must be an array';
            END IF;
            FOR activity IN SELECT value FROM jsonb_array_elements(record->'payload') LOOP
                IF coalesce(activity->>'activityId','') !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION 'Activity without a valid ID';
                END IF;
                INSERT INTO health.activities(activity_id, day, payload, fetched_at)
                VALUES(activity->>'activityId', d, activity, fetched)
                ON CONFLICT(activity_id) DO UPDATE SET day=EXCLUDED.day, payload=EXCLUDED.payload, fetched_at=EXCLUDED.fetched_at
                WHERE EXCLUDED.fetched_at >= activities.fetched_at;
            END LOOP;
        END IF;
    END LOOP;
    INSERT INTO health.sync_status(day, attempted_at, errors, successful_kinds)
    VALUES(d, fetched, snapshot->'errors', kinds)
    ON CONFLICT(day) DO UPDATE SET attempted_at=EXCLUDED.attempted_at, errors=EXCLUDED.errors, successful_kinds=EXCLUDED.successful_kinds
    WHERE EXCLUDED.attempted_at >= sync_status.attempted_at;
    RETURN jsonb_build_object('date',d,'stored_kinds',kinds,'errors',snapshot->'errors');
END;
$$;
REVOKE ALL ON FUNCTION health.ingest_snapshot(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION health.ingest_snapshot(jsonb) TO garmin_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA health TO garmin_reader;
ALTER ROLE garmin_reader SET default_transaction_read_only = on;
ALTER ROLE garmin_reader SET statement_timeout = '5s';
ALTER ROLE garmin_writer SET statement_timeout = '15s';
COMMIT;
