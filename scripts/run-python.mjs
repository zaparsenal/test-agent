import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const python = process.platform === 'win32'
  ? resolve('.venv', 'Scripts', 'python.exe')
  : resolve('.venv', 'bin', 'python');

if (!existsSync(python)) {
  console.error('Python environment not found. Create .venv before running this command.');
  process.exit(1);
}

const result = spawnSync(python, process.argv.slice(2), { stdio: 'inherit' });

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
