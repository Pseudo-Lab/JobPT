import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';

const require = createRequire(import.meta.url);
const workerPath = require.resolve('pdfjs-dist/build/pdf.worker.min.mjs');
const workerUrl = pathToFileURL(workerPath).toString();

const targetPath = new URL('../src/lib/pdfjsWorkerSrc.ts', import.meta.url);
writeFileSync(
  targetPath,
  `export const pdfjsWorkerSrc = "${workerUrl}" as const;\n`
);
