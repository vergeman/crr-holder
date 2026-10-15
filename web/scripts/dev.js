// Imports
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';
import { generate } from 'orval';
import config from '../orval.config.js';

// Generate the client at startup before launching Vite.
const shutdown = new AbortController();
let vite;

function stop() {
  shutdown.abort();
  vite?.kill('SIGTERM');
}

process.on('SIGINT', stop);
process.on('SIGTERM', stop);

// Retry until the API is ready and client generation succeeds.
while (!shutdown.signal.aborted) {
  try {
    const response = await fetch(config.explorer.input, {
      signal: AbortSignal.any([shutdown.signal, AbortSignal.timeout(5000)]),
    });
    if (!response.ok) throw new Error(`OpenAPI request failed: ${response.status}`);
    const schema = await response.text();

    await generate({ ...config.explorer, input: { target: JSON.parse(schema) } });
    console.log('HTTP client updated from the API schema.');

    // Output: serve the UI only after its generated imports exist.
    if (!vite && !shutdown.signal.aborted) {
      vite = spawn(process.execPath,
        ['node_modules/vite/bin/vite.js', '--host', '0.0.0.0', '--port', '5173'],
        { stdio: 'inherit' });
      vite.on('error', (error) => {
        console.error(error);
        process.exitCode = 1;
        stop();
      });
      vite.on('exit', (code) => {
        if (!shutdown.signal.aborted) {
          process.exitCode = code ?? 1;
          stop();
        }
      });
    }

    break;
  } catch (error) {
    if (!shutdown.signal.aborted) console.error(`Client generation: ${error.message}`);
  }

  try {
    await delay(2000, undefined, { signal: shutdown.signal });
  } catch {
    // Shutdown interrupts the retry delay.
  }
}
