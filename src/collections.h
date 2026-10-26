/* Trusted source is parsed once into generic class ASTs. Concrete collections
 * use the common AST specializer; no textual substitution or per-instance parse. */
static const char array_template[] =
"ASSIS __assis_Array<T> {\n"
" private let _length: int; private let _capacity: int; private let _data: *T;\n"
" assis reserve(capacity: int): void {\n"
"  assert(capacity >= 0 && capacity <= 0x0fff_ffff_ffff_ffff);\n"
"  if (capacity <= self._capacity) { return; }\n"
"  let data: *T = alloc<T>(capacity); let i: int = 0;\n"
"  while (i < self._length) { data[i] = self._data[i]; i += 1; }\n"
"  free(self._data); self._data = data; self._capacity = capacity;\n"
" }\n"
" assis push(value: T): void {\n"
"  if (self._length == self._capacity) {\n"
"   if (self._capacity == 0) { self.reserve(8); } else { self.reserve(self._capacity * 2); }\n"
"  }\n"
"  self._data[self._length] = value; self._length += 1;\n"
" }\n"
" assis get(index: int): T { assert(index >= 0 && index < self._length); return self._data[index]; }\n"
" assis set(index: int, value: T): void { assert(index >= 0 && index < self._length); self._data[index] = value; }\n"
" assis pop(): T { assert(self._length > 0); self._length -= 1; return self._data[self._length]; }\n"
" assis try_get(index: int, output: *T): bool { if (index < 0 || index >= self._length || output == null) { return false; } *output = self._data[index]; return true; }\n"
" assis try_pop(output: *T): bool { if (self._length == 0 || output == null) { return false; } self._length -= 1; *output = self._data[self._length]; return true; }\n"
" assis insert(index: int, value: T): void {\n"
"  assert(index >= 0 && index <= self._length); self.push(value); let i: int = self._length - 1;\n"
"  while (i > index) { self._data[i] = self._data[i - 1]; i -= 1; } self._data[index] = value;\n"
" }\n"
" assis remove(index: int): T {\n"
"  let value: T = self.get(index); let i: int = index;\n"
"  while (i + 1 < self._length) { self._data[i] = self._data[i + 1]; i += 1; }\n"
"  self._length -= 1; return value;\n"
" }\n"
" assis contains(value: T): bool {\n"
"  let i: int = 0; while (i < self._length) { if (self._data[i] == value) { return true; } i += 1; } return false;\n"
" }\n"
" assis reverse(): void {\n"
"  let i: int = 0; let j: int = self._length - 1;\n"
"  while (i < j) { let value: T = self._data[i]; self._data[i] = self._data[j]; self._data[j] = value; i += 1; j -= 1; }\n"
" }\n"
" assis clear(): void { self._length = 0; }\n"
" assis dispose(): void { free(self._data); self._data = null; self._length = 0; self._capacity = 0; }\n"
"}\n";

static const char map_template[] =
"ASSIS __assis_Map<K,V> {\n"
" private let _length: int; private let _capacity: int; private let _used: int; private let _keys: *K; private let _values: *V; private let _states: *byte;\n"
" private assis _hash(key: K): int { return int(key) & 0x7fff_ffff_ffff_ffff; }\n"
" private assis _find(key: K): int {\n"
"  if (self._capacity == 0) { return -1; } let i: int = self._hash(key) & (self._capacity - 1); let probes: int = 0;\n"
"  while (probes < self._capacity) {\n"
"   if (self._states[i] == 0) { return -1; }\n"
"   if (self._states[i] == 1 && self._keys[i] == key) { return i; }\n"
"   i = (i + 1) & (self._capacity - 1); probes += 1;\n"
"  } return -1;\n"
" }\n"
" private assis _rehash(capacity: int): void {\n"
"  assert(capacity > 0 && capacity <= 0x0fff_ffff_ffff_ffff && (capacity & (capacity - 1)) == 0);\n"
"  let keys: *K = self._keys; let values: *V = self._values; let states: *byte = self._states; let old: int = self._capacity;\n"
"  self._keys = alloc<K>(capacity); self._values = alloc<V>(capacity); self._states = alloc<byte>(capacity);\n"
"  self._capacity = capacity; self._length = 0; self._used = 0; let i: int = 0;\n"
"  while (i < old) { if (states[i] == 1) { self.set(keys[i], values[i]); } i += 1; } free(keys); free(values); free(states);\n"
" }\n"
" assis set(key: K, value: V): void {\n"
"  let found: int = self._find(key); if (found >= 0) { self._values[found] = value; return; }\n"
"  if (self._capacity == 0) { self._rehash(8); } else if (self._used >= self._capacity / 2) { if (self._length < self._capacity / 4) { self._rehash(self._capacity); } else { self._rehash(self._capacity * 2); } }\n"
"  let i: int = self._hash(key) & (self._capacity - 1); let tombstone: int = -1;\n"
"  while (self._states[i] != 0) { if (self._states[i] == 2 && tombstone < 0) { tombstone = i; } i = (i + 1) & (self._capacity - 1); }\n"
"  if (tombstone >= 0) { i = tombstone; } else { self._used += 1; }\n"
"  self._keys[i] = key; self._values[i] = value; self._states[i] = byte(1); self._length += 1;\n"
" }\n"
" assis get(key: K): V { let i: int = self._find(key); assert(i >= 0); return self._values[i]; }\n"
" assis get_or(key: K, fallback: V): V { let i: int = self._find(key); if (i >= 0) { return self._values[i]; } return fallback; }\n"
" assis try_get(key: K, output: *V): bool { let i: int = self._find(key); if (i < 0 || output == null) { return false; } *output = self._values[i]; return true; }\n"
" assis has(key: K): bool { return self._find(key) >= 0; }\n"
" assis remove(key: K): bool {\n"
"  let i: int = self._find(key); if (i < 0) { return false; } self._states[i] = byte(2); self._length -= 1; return true;\n"
" }\n"
" assis clear(): void { let i: int = 0; while (i < self._capacity) { self._states[i] = byte(0); i += 1; } self._length = 0; self._used = 0; }\n"
" assis keys(): Array<K> {\n"
"  let result: Array<K> = new Array<K>(); result.reserve(self._length); let i: int = 0;\n"
"  while (i < self._capacity) { if (self._states[i] == 1) { result.push(self._keys[i]); } i += 1; } return result;\n"
" }\n"
" assis values(): Array<V> {\n"
"  let result: Array<V> = new Array<V>(); result.reserve(self._length); let i: int = 0;\n"
"  while (i < self._capacity) { if (self._states[i] == 1) { result.push(self._values[i]); } i += 1; } return result;\n"
" }\n"
" assis dispose(): void {\n"
"  free(self._keys); free(self._values); free(self._states); self._keys = null; self._values = null; self._states = null;\n"
"  self._length = 0; self._capacity = 0; self._used = 0;\n"
" }\n"
"}\n";

/* Hash choice is a type-directed AST choice, with both bodies parsed once.
 * Preserve the existing text hash and integer hash; this is not a hash redesign. */
static const char text_hash_template[] =
"\n\n{ let hash: int = 5381; let i: int = 0; let size: int = len(key); let data: *byte = bytes(key); while (i < size) { hash = (hash * 33 + data[i]) & 0x7fff_ffff_ffff_ffff; i += 1; } return hash; }";
static Class *array_ast,*map_ast;
static Node *text_hash_ast;
static void intrinsic_tokens(const char *text){
    SourceFile *file=mem(sizeof(*file));file->path="<colecoes>";file->text=(char*)text;file->state=2;file->internal=true;
    current_source=file;source=file->text;filename=file->path;tokens=(Vec){0};cursor=0;lex();
}
static void load_collection_templates(void){
    if(array_ast)return;
    Vec saved=tokens;int saved_cursor=cursor;SourceFile *previous=current_source;char *previous_source=source;const char *previous_filename=filename;
    intrinsic_tokens(array_template);parse();array_ast=generic_classes.v[generic_classes.n-1];
    intrinsic_tokens(map_template);parse();map_ast=generic_classes.v[generic_classes.n-1];
    intrinsic_tokens(text_hash_template);text_hash_ast=block();expect(T_EOF);
    tokens=saved;cursor=saved_cursor;current_source=previous;source=previous_source;filename=previous_filename;
}
