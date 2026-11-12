"""Exercise the native search CLI and compare its index and rankings to a Python model."""
import hashlib
import json
import os
from pathlib import Path
import random
import re
import statistics
import struct
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPILER = Path(os.environ.get("ASSIS_BIN", ROOT / "bin" / ("assis.exe" if os.name == "nt" else "assis"))).resolve()
EXAMPLE = ROOT / "exemplos/71_search_index.assis"
# The test corpus uses these separators, which are within the declared profile.
WORDS = re.compile(r"[^\s,.;:?!—«»、。-]+")
LATIN_FOLD = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ",
                           "abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþ")
OBSERVATIONS = []


def tokens(source):
    return [(match[0].translate(LATIN_FOLD), len(source[:match.start()].encode()))
            for match in WORDS.finditer(source)]


def model(corpus, query, mode, offset=0):
    words = [word for word, _ in tokens(query)]
    if mode != "phrase":
        words = list(dict.fromkeys(words))
    rows = []
    for doc, source in corpus.items():
        parsed = tokens(source)
        if mode == "phrase":
            actual = [word for word, _ in parsed]
            positions = [parsed[i][1] for i in range(len(parsed))
                         if actual[i:i + len(words)] == words]
        else:
            matched = {word for word, _ in parsed if word in words}
            if mode == "and" and len(matched) != len(words):
                continue
            positions = [at for word, at in parsed if word in matched]
        if positions:
            rows.append((doc, len(positions), min(positions)))
    return sorted(rows, key=lambda row: (-row[1], row[0]))[offset:offset + 10]


def checksum(blob):
    result = 2166136261
    for value in blob:
        result = ((result ^ value) * 16777619) % (2**32)
    return result


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def decode(blob):
    magic, version, docs, count, size = struct.unpack_from("<4sIIII", blob)
    assert (magic, version, size) == (b"ASIX", 1, len(blob))
    assert checksum(blob[:-4]) == struct.unpack_from("<I", blob, len(blob) - 4)[0]
    ids = struct.unpack_from(f"<{docs}I", blob, 20)
    cursor = 20 + docs * 4
    rows = []
    for _ in range(count):
        doc, ordinal, position, length = struct.unpack_from("<4I", blob, cursor)
        cursor += 16
        term = blob[cursor:cursor + length]
        rows.append((checksum(term), doc, ordinal, position, term))
        cursor += length
    assert cursor == len(blob) - 4
    return ids, rows


def batch(corpus):
    return "".join(f"{doc}\t{source}\n" for doc, source in corpus.items()).encode()


def document(body):
    return ('<div type=document version=0.1 lang=pt-BR><div type=head>'
            '<div type=title>PrivateTitle</div><div type=script src=app.assis format=source></div></div>'
            '<div type=body>' + body + '</div></div>')


class SearchIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="assis-search-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.work = Path(cls.directory.name)
        cls.binaries = {}
        for name, flags in [("optimized", []), ("reference", ["--no-opt"])]:
            binary = cls.work / (name + ".exe")
            result = subprocess.run([COMPILER, "build", EXAMPLE, "--safe", "--debug",
                                     "-o", binary, *flags], cwd=ROOT, capture_output=True, timeout=60)
            if result.returncode:
                raise RuntimeError(result.stderr.decode())
            cls.binaries[name] = binary

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=self.work)
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)
        self.snapshot = self.folder / "webassis.asix"
        self.pending = self.folder / "webassis.asix.pending"
        self.lock = self.folder / "webassis.asix.lock"

    def run_cli(self, binary, *args, data=None, status=0, preexec_fn=None):
        started = time.perf_counter_ns()
        result = subprocess.run([binary, *args], cwd=self.folder, input=data, capture_output=True,
                                timeout=45, preexec_fn=preexec_fn)
        elapsed = (time.perf_counter_ns() - started) / 1e6
        self.assertEqual((result.returncode, result.stderr), (status, b""), result)
        rows = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
        return rows, elapsed

    def test_ten_thousand_documents_restart_updates_and_pagination(self):
        seed = 187
        rng = random.Random(seed)
        lexicon = ["ação", "rápida", "Atenção", "猫", "日本語", "текст", "δέλτα",
                   "percurso", "dados", "café", "cafe\u0301", "noite", "ação"]
        initial = {doc: ", ".join(rng.choices(lexicon, k=rng.randrange(2, 12)))
                   for doc in range(1, 10001)}
        initial[10000] = ""
        expected_bytes = None
        for mode, binary in self.binaries.items():
            with self.subTest(mode=mode):
                corpus = dict(initial)
                _, build_ms = self.run_cli(binary, "build", data=batch(corpus))
                snapshot = self.snapshot.read_bytes()
                if expected_bytes is None:
                    expected_bytes = snapshot
                self.assertEqual(snapshot, expected_bytes)
                ids, rows = decode(snapshot)
                self.assertEqual(ids, tuple(initial))
                expected = sorted((checksum(word.encode()), doc, ordinal, pos, word.encode())
                                  for doc, source in corpus.items()
                                  for ordinal, (word, pos) in enumerate(tokens(source)))
                self.assertEqual(rows, expected)
                times = []
                for method, query, offset in [
                    ("and", "AÇÃO texto", 0), ("and", "AÇÃO RÁPIDA", 0),
                    ("and", "ação AÇÃO", 10), ("or", "猫 текст", 10),
                    ("phrase", "café cafe\u0301", 0), ("phrase", "日本語 ação", 0),
                    ("phrase", "ação ação", 0), ("or", "café δέλτα", 20),
                ]:
                    actual, elapsed = self.run_cli(binary, "query", method, query, str(offset))
                    self.assertEqual(actual, model(corpus, query, method, offset))
                    times.append(elapsed)
                deleted = model(corpus, "ação", "and")[0][0]
                self.run_cli(binary, "apply", data=f"{deleted}\n1\tRápida rápida\n10001\tAção — café\n".encode())
                del corpus[deleted]
                corpus[1] = "Rápida rápida"
                corpus[10001] = "Ação — café"
                for query in ["ação", "rápida", "日本語"]:
                    actual, _ = self.run_cli(binary, "query", "and", query)
                    self.assertEqual(actual, model(corpus, query, "and"))
                final = self.snapshot.read_bytes()
                live, final_rows = decode(final)
                self.assertEqual(live, tuple(sorted(corpus)))
                self.assertEqual(final_rows, sorted(
                    (checksum(word.encode()), doc, ordinal, pos, word.encode())
                    for doc, source in corpus.items()
                    for ordinal, (word, pos) in enumerate(tokens(source))))
                OBSERVATIONS.append({
                    "mode": mode, "seed": seed, "documents": len(initial), "postings": len(rows),
                    "snapshot_bytes": len(snapshot), "snapshot_sha256": digest(snapshot),
                    "updated_sha256": digest(final), "binary_sha256": digest(binary.read_bytes()),
                    "build_ms": build_ms, "query_samples_ms": times,
                    "query_median_ms": statistics.median(times), "query_max_ms": max(times),
                })

    def test_hash_collision_is_resolved_by_normalized_term(self):
        left, right = "costarring", "liquid"
        self.assertEqual(checksum(left.encode()), checksum(right.encode()))
        corpus = {1: f"{left} café", 2: f"{right} café", 3: f"{left} {right}", 4: "café"}
        for binary in self.binaries.values():
            self.run_cli(binary, "build", data=batch(corpus))
            for mode, query in [("and", left), ("and", f"{left} {right}"),
                                ("or", right), ("phrase", f"{right} café"),
                                ("phrase", f"{left} {right}")]:
                actual, _ = self.run_cli(binary, "query", mode, query)
                self.assertEqual(actual, model(corpus, query, mode))

    def test_corruption_and_unsupported_version_fail_closed(self):
        for binary in self.binaries.values():
            self.run_cli(binary, "build", data=b"1\tcoffee\n")
            clean = self.snapshot.read_bytes()
            for bad in [clean[:19], clean[:-1], clean + b"x", bytes(30)]:
                self.snapshot.write_bytes(bad)
                self.run_cli(binary, "query", "and", "coffee", status=3)
            for offset, value in [(4, 2), (8, 65536), (12, 524289), (16, 2), (24, 2),
                                  (28, 16384), (32, 16384), (36, 129), (40, 0xFFFFFFFF)]:
                bad = bytearray(clean)
                struct.pack_into("<I", bad, offset, value)
                struct.pack_into("<I", bad, len(bad) - 4, checksum(bad[:-4]))
                self.snapshot.write_bytes(bad)
                self.run_cli(binary, "apply", data=b"2\tfresh\n", status=3)
                self.assertEqual(self.snapshot.read_bytes(), bad)
            self.run_cli(binary, "build", data=b"1\ta b\n")
            bad = bytearray(self.snapshot.read_bytes())
            # Different hash buckets still cannot claim the same doc/ordinal.
            struct.pack_into("<I", bad, 24 + 17 + 4, struct.unpack_from("<I", bad, 24 + 4)[0])
            struct.pack_into("<I", bad, len(bad) - 4, checksum(bad[:-4]))
            self.snapshot.write_bytes(bad)
            self.run_cli(binary, "query", "and", "a", status=3)
            self.run_cli(binary, "build", data=b"")
            self.assertEqual(decode(self.snapshot.read_bytes()), ((), []))
            self.assertEqual(self.run_cli(binary, "query", "and", "a")[0], [])

    def test_htdl_text_alt_and_links_use_catalog_semantics(self):
        source = document('<div type=paragraph>Olá &amp; co<div type=text>rpus</div></div>'
                          '<div type=section hidden=true><div type=paragraph>Secret</div>'
                          '<div type=link href="https://hidden.example/">HiddenLink</div></div>'
                          '<div type=link href="https://example.test/">Referência</div>'
                          '<div type=image src=asset.png alt="Ação acessível"></div>'
                          '<div type=input value=PrivateValue a11y-label=PrivateLabel></div>')
        expected = "Olá & corpus Referência Ação acessível"
        probe = self.folder / "extract.assis"
        probe.write_text(f'''
import "std/htdlsearch.assis";
safe fn main():int{{
    own store:documents::Store=try_new documents::Store(2000000,4000,8);
    assert(store!=null);
    val diagnostic:htdl::Diagnostic=htdl::stage_catalog(store,1,utf8({json.dumps(source, ensure_ascii=False)}),0);
    if(diagnostic.code!=0){{print(diagnostic.code,diagnostic.start,diagnostic.end);return 1;}}
    own page:htdlsearch::Page=try_new htdlsearch::Page(store.candidate(),128,4,128);
    assert(page!=null && page.current(store.candidate()) && page.link_count()==1);
    borrow wanted:slice<byte>=utf8("https://example.test/");
    assert(len(page.link(0))==len(wanted));
    for(let i:int=0;i<len(wanted);i++){{assert(page.link(0)[i]==wanted[i]);}}
    own limited:htdlsearch::Page=try_new htdlsearch::Page(store.candidate(),128,0,128);
    assert(limited!=null && limited.status()==401 && limited.link_count()==0);
    assert(store.abort(1));
    return 0;
}}
''', encoding="utf-8")
        for (mode, binary) in self.binaries.items():
            flags = ["--no-opt"] if mode == "reference" else []
            run = subprocess.run([COMPILER, "run", probe, "--safe", "--debug", *flags],
                                 cwd=ROOT, capture_output=True, timeout=45)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, b"", b""))
            self.run_cli(binary, "build-htdl", data=batch({1: source, 2: document("<div type=paragraph>Corpus</div>")}))
            actual, _ = self.run_cli(binary, "query", "phrase", "Corpus Referência AÇÃO")
            self.assertEqual(actual, model({1: expected, 2: "Corpus"}, "Corpus Referência AÇÃO", "phrase"))
            for query in ["Secret", "HiddenLink", "PrivateTitle", "PrivateValue", "PrivateLabel", "example"]:
                self.assertEqual(self.run_cli(binary, "query", "and", query)[0], [])
            stable = self.snapshot.read_bytes()
            self.run_cli(binary, "apply-htdl", data=batch({1: document("<div type=paragraph>Change</div>"), 2: "<broken>"}), status=1)
            self.assertEqual(self.snapshot.read_bytes(), stable)

    def test_invalid_batch_and_failed_staging_preserve_snapshot(self):
        for binary in self.binaries.values():
            self.run_cli(binary, "build", data=b"1\tstable\n")
            stable = self.snapshot.read_bytes()
            for suffix, status in [(b"0\toutside\n", 1), (b"2\t\xff\n", 2),
                                   (b"2\t" + b"x" * 129 + b"\n", 2),
                                   (b"2\t" + b"x" * 16391 + b"\n", 7)]:
                self.run_cli(binary, "apply", data=b"1\tnew\n" + suffix, status=status)
                self.assertEqual(self.snapshot.read_bytes(), stable)
            self.pending.mkdir()
            try:
                self.run_cli(binary, "apply", data=b"1\tnew\n", status=4)
                self.assertEqual(self.snapshot.read_bytes(), stable)
            finally:
                self.pending.rmdir()
            self.run_cli(binary, "apply", data=b"1\tnew\n")
            actual, _ = self.run_cli(binary, "query", "and", "new")
            self.assertEqual(actual, [(1, 1, 0)])

    def test_reader_sees_previous_snapshot_during_writer_and_after_kill(self):
        for binary in self.binaries.values():
            self.run_cli(binary, "build", data=b"1\tstable\n")
            stable = self.snapshot.read_bytes()
            self.lock.unlink()
            with subprocess.Popen([binary, "apply"], cwd=self.folder, stdin=subprocess.PIPE,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as writer:
                try:
                    writer.stdin.write(b"1\tunpublished\n")
                    writer.stdin.flush()
                    deadline = time.monotonic() + 10
                    while not self.lock.exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertTrue(self.lock.exists())
                    time.sleep(0.05)
                    self.assertIsNone(writer.poll())
                    self.run_cli(binary, "apply", data=b"2\tcompeting\n", status=8)
                    actual, _ = self.run_cli(binary, "query", "and", "stable")
                    self.assertEqual(actual, [(1, 1, 0)])
                finally:
                    if writer.poll() is None:
                        writer.kill()
                    writer.wait(timeout=10)
            self.assertEqual(self.snapshot.read_bytes(), stable)
            self.pending.write_bytes(b"partial snapshot")
            self.run_cli(binary, "apply", data=b"1\trecovered\n")
            self.assertFalse(self.pending.exists())
            actual, _ = self.run_cli(binary, "query", "and", "recovered")
            self.assertEqual(actual, [(1, 1, 0)])

    @unittest.skipIf(os.name == "nt", "POSIX file size limit only")
    def test_os_short_write_keeps_previous_snapshot(self):
        import resource
        import signal

        def limit():
            signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024, 1024))

        for binary in self.binaries.values():
            self.run_cli(binary, "build", data=b"1\tstable\n")
            stable = self.snapshot.read_bytes()
            self.run_cli(binary, "apply", data=b"2\t" + b"word " * 150 + b"\n", status=4, preexec_fn=limit)
            self.assertEqual(self.snapshot.read_bytes(), stable)
            self.assertFalse(self.pending.exists())


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    output = os.environ.get("ASSIS_SEARCH_EVIDENCE")
    if output:
        Path(output).write_text(json.dumps({
            "compiler_sha256": digest(COMPILER.read_bytes()), "cases": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
            "observations": OBSERVATIONS,
        }, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
