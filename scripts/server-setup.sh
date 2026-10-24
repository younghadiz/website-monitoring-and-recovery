#!/usr/bin/env bash
set -euo pipefail

test "$(id -u)" -eq 0

. /etc/os-release
test "$ID" = "ubuntu"
test "$VERSION_ID" = "24.04"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl

install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

chmod a+r /etc/apt/keyrings/docker.asc

architecture="$(dpkg --print-architecture)"

cat > /etc/apt/sources.list.d/docker.sources <<DOCKER_SOURCE
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $architecture
Signed-By: /etc/apt/keyrings/docker.asc
DOCKER_SOURCE

apt-get update

apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

systemctl enable --now docker
systemctl enable ssh.socket

if docker container inspect capstone-nginx >/dev/null 2>&1; then
    echo "capstone-nginx already exists; inspect it instead of replacing it"
    exit 1
fi

docker pull nginx:stable-alpine

docker run -d \
  --name capstone-nginx \
  --restart=no \
  -p 8080:80 \
  nginx:stable-alpine

docker inspect \
  --format '{{.State.Status}} {{.Config.Image}}' \
  capstone-nginx

curl --fail --silent --show-error http://127.0.0.1:8080/

docker image inspect nginx:stable-alpine \
  --format '{{json .RepoDigests}}'

docker version
