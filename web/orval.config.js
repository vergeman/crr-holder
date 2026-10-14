// Imports
import { defineConfig } from 'orval';

// Output: keep all replaceable code inside the generated directory.
export default defineConfig({
  explorer: {
    input: 'http://api:8000/openapi.json',
    output: {
      target: './src/generated/client.ts',
      client: 'fetch',
    },
  },
});
