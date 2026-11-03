// Proves one generation attempt in the lab: checks 3 and 4 for every candidate that passed 1 and 2.
//
//   node qe/lab/prove.mjs <attempt>        (npm run qe:prove -- <attempt>)
//
// 20 runs of the whole suite with the candidates added, each on a fresh database, then the new
// candidates alone on every seeded fault of their rules, where a catch must repeat on five fresh
// databases. Results go to qe/lab/results/proof/attempt-<n>-runs.jsonl and -faults.jsonl.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync } from 'node:fs';

const attempt = process.argv[2];
if (!attempt) throw new Error('Say which attempt to prove, for example: npm run qe:prove -- 1');

const manifest = JSON.parse(readFileSync(`qe/generated/attempt-${attempt}/manifest.json`, 'utf8'));
const faults = readFileSync('qe/faults/faults.yaml', 'utf8');
const faultRules = [...faults.matchAll(/- id: (\S+)\n\s+rule: (\S+)/g)].map(([, id, rule]) => ({ id, rule }));
const fresh = manifest.candidates.filter((c) => c.ready_for_lab && c.attempt === Number(attempt));
if (!fresh.length) {
  console.log(`Attempt ${attempt} has no new candidates for the lab.`);
  process.exit(0);
}
const rules = new Set(fresh.map((c) => c.rule));
const builds = faultRules.filter((f) => rules.has(f.rule)).map((f) => f.id);
const escape = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// Playwright matches --grep against the file path and title together, so the titles are not anchored.
const grep = fresh.map((c) => escape(c.title)).join('|');

mkdirSync('qe/lab/results/proof', { recursive: true });
const out = (name) => `qe/lab/results/proof/attempt-${attempt}-${name}.jsonl`;
for (const name of ['runs', 'faults']) if (existsSync(out(name))) rmSync(out(name));

function lab(args) {
  const command = ['compose', '-f', 'docker-compose.qe.yml', 'run', '--rm', 'lab', '--overlay', `/estate/generated/attempt-${attempt}`, ...args];
  console.log(`docker ${command.join(' ')}`);
  const result = spawnSync('docker', command, { stdio: 'inherit' });
  if (result.status !== 0) throw new Error(`the lab stopped with ${result.status}`);
}

console.log(`Proving ${fresh.length} candidates: 20 runs of the suite, then ${builds.length} fault builds.`);
lab(['--builds', 'baseline', '--runs', '20', '--parallel', '3', '--out', `/results/proof/attempt-${attempt}-runs.jsonl`]);
lab(['--builds', builds.join(','), '--grep', grep, '--workers', '1', '--confirm', '5', '--parallel', '3',
  '--out', `/results/proof/attempt-${attempt}-faults.jsonl`]);
console.log(`Attempt ${attempt} proved. Next: npm run qe:generate -- ${Number(attempt) + 1}, which redoes only the failures.`);
