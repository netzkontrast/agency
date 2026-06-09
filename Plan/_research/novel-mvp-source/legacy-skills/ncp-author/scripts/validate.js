#!/usr/bin/env node
/**
 * ncp-author — schema validator
 *
 * Wraps Ajv against the pinned upstream NCP schema
 * (`../upstream/schema/ncp-schema.json`, currently v1.3.0 at SHA 0b9ab12)
 * and validates one or more JSON files. Prints PASS/FAIL per file with
 * the first error message on failure.
 *
 * Usage:
 *   node scripts/validate.js <file1.json> [file2.json ...]
 *
 * Exit codes:
 *   0 — all files PASS
 *   1 — usage error or at least one file FAILed
 *
 * Dependency:
 *   ajv (>=8). Install once with `npm install` from this skill's root,
 *   or `npm install ajv` globally / in your project.
 *
 * Behavior matches `upstream/tests/validate-file.js` (same strict:false,
 * allErrors:true settings) so PASS/FAIL parity with upstream CI is
 * preserved. The wrapper is thinner-on-purpose: it adds nothing the
 * canonical NCP validator doesn't already do, only relocates the entry
 * point to a stable path inside this skill.
 */

'use strict';

const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);

if (args.length === 0) {
  console.error('Usage: node scripts/validate.js <file1.json> [file2.json ...]');
  process.exit(1);
}

let Ajv;
try {
  Ajv = require('ajv');
} catch (err) {
  console.error('FATAL: ajv is not installed.');
  console.error('Run `npm install` from this skill\'s root, or `npm install ajv`.');
  process.exit(1);
}

const skillRoot = path.join(__dirname, '..');
const schemaPath = path.join(skillRoot, 'upstream', 'schema', 'ncp-schema.json');

if (!fs.existsSync(schemaPath)) {
  console.error(`FATAL: schema not found at ${schemaPath}`);
  console.error('The upstream/ snapshot may be missing or moved.');
  process.exit(1);
}

const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

function formatErrors(errors) {
  return (errors || [])
    .map((error) => `${error.instancePath || '/'} ${error.message}`)
    .join('; ');
}

let failures = 0;

for (const inputPath of args) {
  const targetPath = path.isAbsolute(inputPath)
    ? inputPath
    : path.resolve(process.cwd(), inputPath);

  let data;

  try {
    data = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
  } catch (error) {
    failures += 1;
    console.error(`FAIL ${inputPath}: unable to parse JSON (${error.message})`);
    continue;
  }

  const ok = validate(data);

  if (ok) {
    console.log(`PASS ${inputPath}`);
  } else {
    failures += 1;
    console.error(`FAIL ${inputPath}: ${formatErrors(validate.errors)}`);
  }
}

if (failures > 0) {
  process.exitCode = 1;
}
