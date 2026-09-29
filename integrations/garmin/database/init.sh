#!/bin/sh
set -eu
# Passwords are generated locally by provision.py and never printed.
n8n_password=$(cat /run/secrets/n8n_database)
writer_password=$(cat /run/secrets/garmin_writer)
reader_password=$(cat /run/secrets/garmin_reader)
psql -X -v ON_ERROR_STOP=1 --username postgres --dbname postgres <<SQL
CREATE ROLE n8n LOGIN PASSWORD '$n8n_password';
CREATE DATABASE n8n OWNER n8n;
CREATE ROLE garmin_writer LOGIN PASSWORD '$writer_password';
CREATE ROLE garmin_reader LOGIN PASSWORD '$reader_password';
CREATE DATABASE garmin;
REVOKE CONNECT ON DATABASE garmin FROM PUBLIC;
GRANT CONNECT ON DATABASE garmin TO garmin_writer, garmin_reader;
REVOKE CONNECT ON DATABASE n8n FROM PUBLIC;
GRANT CONNECT ON DATABASE n8n TO n8n;
SQL
unset n8n_password writer_password reader_password
psql -X -v ON_ERROR_STOP=1 --username postgres --dbname garmin -f /opt/isa/0001_garmin.sql
psql -X -v ON_ERROR_STOP=1 --username postgres --dbname garmin -f /opt/isa/0002_habits.sql
