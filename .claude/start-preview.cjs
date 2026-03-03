// Wrapper to start Vite with correct API port for preview
const { spawn } = require('child_process');
const path = require('path');

const uiDir = path.join(__dirname, '..', 'ui');
const vite = path.join(uiDir, 'node_modules', 'vite', 'bin', 'vite.js');
const args = process.argv.slice(2);

const child = spawn(process.execPath, [vite, ...args], {
  cwd: uiDir,
  stdio: 'inherit',
  env: { ...process.env, VITE_API_PORT: process.env.VITE_API_PORT || '8889' }
});

child.on('exit', (code) => process.exit(code || 0));
process.on('SIGTERM', () => child.kill('SIGTERM'));
process.on('SIGINT', () => child.kill('SIGINT'));
