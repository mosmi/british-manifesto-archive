#!/usr/bin/env node
/**
 * @deprecated Use scripts/build-party-colours.mjs
 * Kept as a thin wrapper for older docs/commands.
 */
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const script = join(dirname(fileURLToPath(import.meta.url)), 'build-party-colours.mjs');
const result = spawnSync(process.execPath, [script, ...process.argv.slice(2)], { stdio: 'inherit' });
process.exit(result.status ?? 1);
