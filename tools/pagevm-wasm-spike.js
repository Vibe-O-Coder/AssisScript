// Trusted, generated comparison fixtures only; not a general page loader.
// Node/V8 is used for the Wasm alternative. See ADR-0001: no format chosen.
'use strict';
const fs = require('node:fs');
const request = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let counter = 0n;
let calls = 0;
try {
  const module = new WebAssembly.Module(Buffer.from(request.module, 'base64'));
  for (const item of WebAssembly.Module.imports(module)) {
    if (item.module !== 'counter' || item.name !== 'add_v1' || item.kind !== 'function') {
      throw new Error('denied_import');
    }
  }
  const instance = new WebAssembly.Instance(module, {counter: {add_v1(delta) {
    if (!request.grant) throw new Error('denied_capability');
    if (calls >= request.maxCalls) throw new Error('host_quota');
    if (delta < -1000000n || delta > 1000000n) throw new Error('host_argument');
    calls++;
    counter = BigInt.asIntN(64, counter + delta);
    return counter;
  }}});
  const result = instance.exports.run();
  let growth = null;
  if (instance.exports.memory) growth = instance.exports.memory.grow(0);
  process.stdout.write(JSON.stringify({status:'halted',result:String(result),counter:String(counter),calls,growth,node:process.version,v8:process.versions.v8}));
} catch (error) {
  process.stdout.write(JSON.stringify({status:'rejected',error:error.message,counter:String(counter),calls,node:process.version,v8:process.versions.v8}));
}
