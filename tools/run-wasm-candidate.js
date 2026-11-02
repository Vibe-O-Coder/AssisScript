// Local comparison harness only. No product logic or native page authority.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {performance} = require('node:perf_hooks');
const file = process.argv[2];
function reject(error) { process.stdout.write(JSON.stringify({status:'rejected',error})); }
try {
  if (fs.statSync(file).size > 12 * 1024 * 1024) throw Error('envelope_size');
  const request = JSON.parse(fs.readFileSync(file, 'utf8'));
  const start = performance.now();
  const verified = spawnSync(process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),
    [path.join(__dirname, 'asv2-wasm-candidate.py'), file, '--verify'],
    {encoding:'utf8',timeout:10000,maxBuffer:12*1024*1024,windowsHide:true});
  if (verified.status !== 0) throw Error('noncanonical_or_invalid');
  const bytes = Buffer.from(verified.stdout.trim(), 'base64');
  const validated = performance.now();
  const module = new WebAssembly.Module(bytes);
  if (WebAssembly.Module.imports(module).length) throw Error('imports_denied');
  const loaded = performance.now();
  const id = request.identity || [1,7,1];
  if (id.length !== 3 || !id.every(n => Number.isSafeInteger(n) && n > 0)) throw Error('identity');
  const repeats = request.repeat ?? 1;
  if (!Number.isInteger(repeats) || repeats < 1 || repeats > 2000) throw Error('repeat');
  let snapshots = [];
  let linearBytes = 0;
  for (let repeat=0;repeat<repeats;repeat++) {
  const instance = new WebAssembly.Instance(module, {});
  const e = instance.exports;
  linearBytes = e.memory.buffer.byteLength;
  let event = 0;
  let closed = false;
  const same = a => Array.isArray(a) && a.length === 3 && a.every((v,i) => v === id[i]);
  snapshots = [];
  for (const action of request.actions || [{op:'tick',quantum:10000}]) {
    let accepted = false;
    if (action.op === 'grant') { accepted = !closed && e.state.value === 0 && same(action.identity); if (accepted) e.grant.value = 1; }
    else if (action.op === 'revoke') { accepted = !closed; if (accepted) { e.grant.value = 0; e.state.value = -2; } }
    else if (action.op === 'close') { e.grant.value = 0; e.state.value = -9; closed = true; accepted = true; }
    else if (action.op === 'begin') {
      accepted = !closed && same(action.identity) && Number.isSafeInteger(action.request) && action.request > event &&
        (e.state.value === 2 || (e.state.value === 0 && e.steps.value === 0));
      if (accepted) {
        event = action.request;
        // Entry is derived from the validated ASV2, never an action-supplied PC.
        e.pc.value = Buffer.from(request.asv2,'base64').readUInt32LE(8);
        e.frame.value = 0; e.result.value = 0n; e.state.value = 0;
        new Uint8Array(e.memory.buffer,0,16384).fill(0);
      }
    } else if (action.op === 'reply') {
      accepted = !closed && e.state.value === 3 && same(action.identity) && action.request === event && action.call === e.calls.value &&
        typeof action.value === 'string' && /^-?\d{1,20}$/.test(action.value) && BigInt(action.value) >= -(2n**63n) && BigInt(action.value) < 2n**63n;
      if (accepted) { new DataView(e.memory.buffer).setBigInt64(e.destination.value,BigInt(action.value),true); e.pending.value = 0; e.state.value = 0; }
    } else if (action.op === 'tick') {
      if (!Number.isInteger(action.quantum) || action.quantum < 1 || action.quantum > 10000) throw Error('quantum');
      accepted = e.tick(action.quantum);
    } else throw Error('action');
    snapshots.push({accepted,state:e.state.value,result:String(e.result.value),steps:e.steps.value,calls:e.calls.value,
      counter:String(e.counter.value),pending:e.pending.value,arg:String(e.arg.value),second:String(e.second.value)});
  }
  }
  process.stdout.write(JSON.stringify({status:'executed',snapshots,compile_ms:loaded-start,validator_ms:validated-start,engine_compile_ms:loaded-validated,execute_ms:performance.now()-loaded,repeats,
    linear_bytes:linearBytes,module_bytes:bytes.length,rss_bytes:process.memoryUsage().rss,node:process.version,v8:process.versions.v8}));
} catch (error) { reject(error.message); }
