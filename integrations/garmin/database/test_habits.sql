BEGIN;
SET LOCAL ROLE garmin_reader;
INSERT INTO habits.daily(day,answers) VALUES ('1900-01-01','{"energy":0,"water_over_3l":false}')
ON CONFLICT(day) DO UPDATE SET answers=EXCLUDED.answers;
INSERT INTO habits.daily(day,answers) VALUES ('1900-01-01','{"focus":7}')
ON CONFLICT(day) DO UPDATE SET answers=habits.daily.answers || EXCLUDED.answers;
DO $$ BEGIN
 IF (SELECT answers FROM habits.daily WHERE day='1900-01-01') <> '{"energy":0,"water_over_3l":false,"focus":7}'::jsonb THEN
  RAISE EXCEPTION 'Partial update erased morning answers';
 END IF;
 IF has_table_privilege(current_user,'health.records','INSERT') OR has_table_privilege(current_user,'health.records','UPDATE') THEN
  RAISE EXCEPTION 'Garmin write access must remain denied';
 END IF;
 IF has_table_privilege(current_user,'habits.daily','DELETE') THEN
  RAISE EXCEPTION 'Habit deletion must remain denied';
 END IF;
END $$;
ROLLBACK;
