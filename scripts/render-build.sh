#!/usr/bin/env bash
set -euo pipefail

NODE_VERSION="22.16.0"
NODE_DIR="${HOME}/.pipatzo-node"

# Credenciales corporativas (Artifactory LATAM, NPM_TOKEN, etc.) rompen el build en Render.
unset NPM_TOKEN NODE_AUTH_TOKEN NPM_CONFIG__AUTH || true
export npm_config_registry="https://registry.npmjs.org/"

if ! command -v node >/dev/null 2>&1; then
  mkdir -p "${NODE_DIR}"
  curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" -o /tmp/node.tar.xz
  tar -xJf /tmp/node.tar.xz -C "${NODE_DIR}" --strip-components=1
  export PATH="${NODE_DIR}/bin:${PATH}"
fi

cd frontend
node ./scripts/assert-public-lock.cjs
npm install --registry https://registry.npmjs.org/
npm run build
cd ..

pip install -r requirements.txt
