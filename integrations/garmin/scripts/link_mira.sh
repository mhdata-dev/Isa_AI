#!/bin/sh
set -eu
# Attach only the named Isa container, without restarting it or changing its image.
container=${1:-warp-drive-pilot-mira-1}
network=isa-integrations-mira
project=$(docker inspect "$container" --format '{{ index .Config.Labels "com.docker.compose.project" }}')
service=$(docker inspect "$container" --format '{{ index .Config.Labels "com.docker.compose.service" }}')
if [ "$project" != warp-drive-pilot ] || [ "$service" != mira ]; then
  echo 'Refusing to attach a container outside the existing Isa service.' >&2
  exit 1
fi
if docker network inspect "$network" --format '{{range .Containers}}{{println .Name}}{{end}}' | grep -Fxq "$container"; then
  echo 'Isa already attached.'
else
  docker network connect "$network" "$container"
  echo 'Isa attached to its dedicated MCP network; no restart.'
fi
