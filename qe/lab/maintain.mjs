// Proves maintenance changes in the lab.
//
//   node qe/lab/maintain.mjs flaky      20 runs of the suite with the flaky-test fixes
//   node qe/lab/maintain.mjs release    the suite on the next release, before any repair
//   node qe/lab/maintain.mjs repair     the suite on the next release with the repaired page objects
//
// Results go to qe/lab/results/maintenance.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, rmSync } from 'node:fs';

const RELEASE = 'release-4.9';
const steps = {
  flaky: { overlay: 'maintenance/flaky-fix', builds: 'baseline', runs: 20, out: 'flaky-fix-runs' },
  release: { overlay: 'maintenance/flaky-fix', builds: RELEASE, runs: 1, out: `${RELEASE}-before` },
  repair: { overlay: `maintenance/${RELEASE}-repair`, builds: RELEASE, runs: 1, out: `${RELEASE}-after` },
};
const step = steps[process.argv[2]];
if (!step) throw new Error(`Say which step: ${Object.keys(steps).join(', ')}`);

mkdirSync('qe/lab/results/maintenance', { recursive: true });
const out = `qe/lab/results/maintenance/${step.out}.jsonl`;
if (existsSync(out)) rmSync(out);
const command = ['compose', '-f', 'docker-compose.qe.yml', 'run', '--rm', 'lab',
  '--overlay', `/estate/generated/${step.overlay}`, '--builds', step.builds, '--runs', String(step.runs),
  '--parallel', '3', '--out', `/results/maintenance/${step.out}.jsonl`];
console.log(`docker ${command.join(' ')}`);
const result = spawnSync('docker', command, { stdio: 'inherit' });
process.exit(result.status ?? 1);
