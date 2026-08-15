#!/usr/bin/env bash
set -euo pipefail

NODE_VERSION="22.16.0"
NODE_DIR="${HOME}/.pipatzo-node"

if ! command -v node >/dev/null 2>&1; then
  mkdir -p "${NODE_DIR}"
  curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" -o /tmp/node.tar.xz
  tar -xJf /tmp/node.tar.xz -C "${NODE_DIR}" --strip-components=1
  export PATH="${NODE_DIR}/bin:${PATH}"
fi

cd frontend
npm install --registry https://registry.npmjs.org
npm run build
cd ..

pip install -r requirements.txt
