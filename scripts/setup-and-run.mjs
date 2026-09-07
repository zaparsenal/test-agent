import { existsSync } from 'node:fs';
import { spawn, spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const MIN_NODE = [22, 13];
const MIN_PYTHON = [3, 11];
const MAX_PYTHON = [3, 15];
const isWindows = process.platform === 'win32';
const npm = isWindows ? (process.env.ComSpec ?? 'cmd.exe') : 'npm';
const npmPrefix = isWindows ? ['/d', '/s', '/c', 'npm'] : [];
const venvPython = isWindows
  ? resolve('.venv', 'Scripts', 'python.exe')
  : resolve('.venv', 'bin', 'python');

function versionAtLeast(current, minimum) {
  return current[0] > minimum[0]
    || (current[0] === minimum[0] && current[1] >= minimum[1]);
}

function versionBefore(current, maximum) {
  return current[0] < maximum[0]
    || (current[0] === maximum[0] && current[1] < maximum[1]);
}

function run(command, args) {
  const result = spawnSync(command, args, { stdio: 'inherit' });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if (result.status !== 0) process.exit(result.status ?? 1);
}

function inspectPython(command, prefix = []) {
  const result = spawnSync(
    command,
    [...prefix, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'],
    { encoding: 'utf8' },
  );
  if (result.status !== 0) return null;
  const version = result.stdout.trim().split('.').map(Number);
  if (!versionAtLeast(version, MIN_PYTHON) || !versionBefore(version, MAX_PYTHON)) return null;
  return { command, prefix, version: version.join('.') };
}

function findPython() {
  const candidates = isWindows
    ? [
        ['py', ['-3.14']],
        ['py', ['-3.13']],
        ['py', ['-3.12']],
        ['py', ['-3.11']],
        ['python', []],
      ]
    : [
        ['python3.14', []],
        ['python3.13', []],
        ['python3.12', []],
        ['python3.11', []],
        ['python3', []],
        ['python', []],
      ];

  for (const [command, prefix] of candidates) {
    const python = inspectPython(command, prefix);
    if (python) return python;
  }
  return null;
}

function openDemo() {
  const url = 'http://localhost:3000';
  try {
    if (process.platform === 'darwin') {
      spawn('open', [url], { detached: true, stdio: 'ignore' }).unref();
    } else if (isWindows) {
      spawn('cmd.exe', ['/c', 'start', '', url], { detached: true, stdio: 'ignore' }).unref();
    } else {
      spawn('xdg-open', [url], { detached: true, stdio: 'ignore' }).unref();
    }
  } catch {
    console.log(`Open ${url} in your browser.`);
  }
}

const nodeVersion = process.versions.node.split('.').slice(0, 2).map(Number);
if (!versionAtLeast(nodeVersion, MIN_NODE)) {
  console.error('FieldGuide needs Node.js 22.13 or newer. Download it from https://nodejs.org/.');
  process.exit(1);
}

console.log('\nFieldGuide setup and startup\n');

if (!existsSync(venvPython)) {
  const python = findPython();
  if (!python) {
    console.error('Python 3.11, 3.12, 3.13, or 3.14 is required. Download it from https://www.python.org/downloads/.');
    process.exit(1);
  }
  console.log(`[1/4] Creating .venv with Python ${python.version}...`);
  run(python.command, [...python.prefix, '-m', 'venv', '.venv']);
} else if (!inspectPython(venvPython)) {
  console.error('The existing .venv uses an unsupported Python version. Rename or remove .venv, then run this command again.');
  process.exit(1);
} else {
  console.log('[1/4] Reusing the existing Python environment...');
}

console.log('[2/4] Installing Python packages...');
run(venvPython, ['-m', 'pip', 'install', '-r', 'requirements.txt']);

console.log('[3/4] Installing web packages...');
run(npm, [...npmPrefix, 'install']);

if (process.env.FIELDGUIDE_SETUP_ONLY === '1') {
  console.log('\nFieldGuide environment is ready.');
  process.exit(0);
}

console.log('[4/4] Starting FieldGuide...');
console.log('The demo will open at http://localhost:3000. Press Ctrl+C to stop it.\n');

const demo = spawn(npm, [...npmPrefix, 'run', 'demo'], { stdio: 'inherit' });
const browserTimer = setTimeout(openDemo, 5000);

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => demo.kill(signal));
}

demo.on('error', (error) => {
  clearTimeout(browserTimer);
  console.error(error.message);
  process.exit(1);
});

demo.on('exit', (code) => {
  clearTimeout(browserTimer);
  process.exit(code ?? 0);
});
