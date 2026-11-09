#!/usr/bin/env bash
set -euo pipefail

tag="cst4562-db-$$"
primary="$tag-primary"
restore="$tag-restore"
service_net="$tag-service"
backup_net="$tag-backup"
evidence="${1:-$(dirname "$0")/evidence/database-verification.txt}"
image="${CST4562_POSTGRES_IMAGE:-postgres:16-alpine}"
mkdir -p "$(dirname "$evidence")"

cleanup() {
  docker rm -fv "$primary" "$restore" >/dev/null 2>&1 || true
  docker network rm "$service_net" "$backup_net" >/dev/null 2>&1 || true
}
trap cleanup EXIT

start() {
  docker run -d --pull=never --name "$1" --network "$2" \
    -e POSTGRES_PASSWORD='MSS-LAB-OPERATOR-ONLY' "$image" >/dev/null
  for _ in {1..40}; do
    if docker exec "$1" pg_isready -h 127.0.0.1 -U postgres >/dev/null 2>&1; then return; fi
    sleep 1
  done
  return 1
}

query() {
  docker exec "$1" psql -X -At -v ON_ERROR_STOP=1 -U postgres -d mss -c "$2"
}

employee() {
  docker run --rm --pull=never --network "$service_net" -e PGPASSWORD='MSS-LAB-APP-ONLY' "$image" \
    psql -X -At -v ON_ERROR_STOP=1 -h "$primary" -U mss_app -d mss -c "$1"
}

report() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
  docker network create --internal "$service_net" >/dev/null
  docker network create --internal "$backup_net" >/dev/null
  start "$primary" "$service_net"
  start "$restore" "$backup_net"
  docker inspect "$primary" "$restore" --format '{{.Name}} {{range $key, $v := .NetworkSettings.Networks}}{{$key}} {{end}} ports={{json .HostConfig.PortBindings}}'
  docker exec "$primary" postgres --version

  docker exec "$primary" createdb -U postgres mss
  docker exec "$restore" createdb -U postgres mss
  docker exec -i "$primary" psql -X -v ON_ERROR_STOP=1 -U postgres -d mss <<'SQL'
CREATE ROLE mss_app LOGIN PASSWORD 'MSS-LAB-APP-ONLY';
CREATE SCHEMA marketing;
CREATE SCHEMA sales;
CREATE SCHEMA support;
CREATE TABLE marketing.campaign (id integer PRIMARY KEY, label text NOT NULL);
CREATE TABLE sales.quote (id integer PRIMARY KEY, label text NOT NULL);
CREATE TABLE support.ticket (id integer PRIMARY KEY, label text NOT NULL);
INSERT INTO marketing.campaign VALUES (1, 'Example campaign');
INSERT INTO sales.quote VALUES (1, 'Example quote');
INSERT INTO support.ticket VALUES (1, 'Example ticket');
GRANT USAGE ON SCHEMA marketing, sales, support TO mss_app;
GRANT SELECT ON ALL TABLES IN SCHEMA marketing, sales, support TO mss_app;
SQL
  read_sql="SELECT label FROM marketing.campaign UNION ALL SELECT label FROM sales.quote UNION ALL SELECT label FROM support.ticket ORDER BY 1"
  expected="$(printf 'Example campaign\nExample quote\nExample ticket')"
  rows="$(employee "$read_sql")"
  [[ "$rows" == "$expected" ]]
  printf '\nApplication identity read all three departments\n%s\n' "$rows"
  if denied="$(employee "DELETE FROM sales.quote WHERE id=1" 2>&1)"; then
    echo 'Application identity unexpectedly deleted a row' >&2
    return 1
  fi
  [[ "$denied" == *'permission denied'* ]]
  printf '\nApplication identity write denied\n%s\n' "$denied"

  docker exec "$primary" pg_dump -U postgres -Fc mss |
    docker exec -i "$restore" pg_restore -U postgres -d mss --no-owner --no-acl --exit-on-error
  restored="$(query "$restore" "$read_sql")"
  [[ "$restored" == "$expected" ]]
  printf '\nRestored in isolated backup network\n%s\n' "$restored"
  echo 'PASS: three department records restored and matched'
}

report | tee "$evidence"
