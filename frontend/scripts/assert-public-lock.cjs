"use strict";

const fs = require("fs");
const path = require("path");

const lockfile = path.join(__dirname, "..", "package-lock.json");
const banned = /artifactoryrepo1\.appslatam|appslatam\.com\/artifactory|jfrog\.io/i;

if (!fs.existsSync(lockfile)) {
  process.exit(0);
}

const text = fs.readFileSync(lockfile, "utf8");
if (banned.test(text)) {
  console.error(
    "El package-lock.json apunta al Artifactory de LATAM. Este repo solo usa https://registry.npmjs.org/\n" +
      "Borra node_modules y package-lock.json, luego: npm install --registry https://registry.npmjs.org/"
  );
  process.exit(1);
}
