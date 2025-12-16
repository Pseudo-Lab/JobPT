import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const workerPath = require.resolve('pdfjs-dist/build/pdf.worker.min.mjs');
const workerUrl = pathToFileURL(workerPath).toString();

process.stdout.write(workerUrl);
