BEGIN;
CREATE SCHEMA IF NOT EXISTS habits;
CREATE TABLE IF NOT EXISTS habits.daily (
    day date PRIMARY KEY,
    answers jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(answers)='object' AND octet_length(answers::text)<=65536),
    updated_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON SCHEMA habits FROM PUBLIC;
REVOKE ALL ON habits.daily FROM PUBLIC;
GRANT USAGE ON SCHEMA habits TO garmin_reader;
GRANT SELECT, INSERT, UPDATE ON habits.daily TO garmin_reader;
COMMIT;
