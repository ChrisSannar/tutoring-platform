#!/usr/bin/env bash
set -euo pipefail

image="ghcr.io/chrissannar/tutoring-platform"
docker_config="${DOCKER_CONFIG:-$HOME/.docker}/config.json"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Refusing to publish a dirty Git worktree" >&2
  exit 1
fi
if [[ ! -f "$docker_config" ]] || ! grep -q '"ghcr.io"' "$docker_config"; then
  echo "Authenticate first: docker login ghcr.io" >&2
  exit 1
fi

sha="$(git rev-parse HEAD)"
docker buildx build \
  --platform linux/amd64 \
  --label "org.opencontainers.image.source=https://github.com/chrissannar/tutoring-platform" \
  --tag "$image:latest" \
  --tag "$image:$sha" \
  --push \
  .
