#!/usr/bin/env node
/**
 * generate-og.mjs — batch-render OG images for manifestos.org.uk
 *
 * Usage:
 *   npm install
 *   node tools/og-generator/generate-og.mjs tools/og-generator/pages.json
 *   node tools/og-generator/generate-og.mjs tools/og-generator/pages.json . --force
 *
 * pages.json is an array of { path, spec } entries. Output paths are relative
 * to the output directory (repo root by default), mirroring site URLs.
 */
import puppeteer from 'puppeteer';
import { createHash } from 'crypto';
import {
  readFileSync, writeFileSync, mkdirSync, existsSync,
} from 'fs';
import { dirname, resolve, join } from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { platform } from 'os';

function systemChromePath() {
  if (process.env.PUPPETEER_EXECUTABLE_PATH) {
    return process.env.PUPPETEER_EXECUTABLE_PATH;
  }
  if (platform() === 'darwin') {
    for (const p of [
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
    ]) {
      if (existsSync(p)) return p;
    }
  }
  return null;
}

async function launchBrowser() {
  try {
    return await puppeteer.launch({ headless: true });
  } catch (err) {
    const chrome = systemChromePath();
    if (!chrome) throw err;
    console.warn(`Bundled Chrome unavailable (${err.message}); using ${chrome}`);
    return puppeteer.launch({ headless: true, executablePath: chrome });
  }
}

const [, , manifestPath, outDirArg, ...rest] = process.argv;
const force = rest.includes('--force');

if (!manifestPath) {
  console.error('Usage: node tools/og-generator/generate-og.mjs pages.json [outDir] [--force]');
  process.exit(1);
}

const here = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(outDirArg || join(here, '..', '..'));
const ogUrl = pathToFileURL(join(here, 'og.html')).href;
const pages = JSON.parse(readFileSync(manifestPath, 'utf8'));
const hashPath = join(outDir, 'og', '.og-hashes.json');

let hashes = {};
if (existsSync(hashPath)) {
  try {
    hashes = JSON.parse(readFileSync(hashPath, 'utf8'));
  } catch {
    hashes = {};
  }
}

function specHash(spec) {
  return createHash('sha1').update(JSON.stringify(spec)).digest('hex');
}

const browser = await launchBrowser();
const page = await browser.newPage();
await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });

let rendered = 0;
let skipped = 0;

for (const { path: relPath, spec } of pages) {
  const hash = specHash(spec);
  const file = resolve(outDir, relPath);
  if (!force && hashes[relPath] === hash && existsSync(file)) {
    skipped++;
    continue;
  }

  const url = `${ogUrl}?spec=${encodeURIComponent(JSON.stringify(spec))}`;
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForFunction('window.__ready === true', { timeout: 15000 });
  mkdirSync(dirname(file), { recursive: true });
  await page.screenshot({ path: file, type: 'jpeg', quality: 88 });
  hashes[relPath] = hash;
  rendered++;
  console.log(`✓ ${relPath}  (${rendered + skipped}/${pages.length})`);
}

await browser.close();

mkdirSync(join(outDir, 'og'), { recursive: true });
writeFileSync(hashPath, JSON.stringify(hashes, null, 2) + '\n', 'utf8');
console.log(`Done — ${rendered} rendered, ${skipped} skipped → ${outDir}`);
