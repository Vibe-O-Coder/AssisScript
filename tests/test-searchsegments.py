"""Check ASIS with an independent format and ranking oracle."""

from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import random
import struct
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUFFIX = ".exe" if os.name == "nt" else ""
COMPILER = Path(os.environ.get("ASSIS_BIN", ROOT / "bin" / f"assis{SUFFIX}")).resolve()
HEADER = b"ASIS\x01\x10\x00\x00"


def digest(data):
    return sha256(data).hexdigest()


def model_parts(data):
    if not data.startswith(HEADER):
        raise ValueError("header")
    parts = []
    cursor = len(HEADER)
    for part in range(1, 17):
        magic, version, count, rows, length = struct.unpack_from("<4s4I", data, cursor)
        if (magic, version) != (b"ASIX", 1):
            raise ValueError("part header")
        frame = data[cursor:cursor + length]
        cursor += length
        check = 2166136261 ^ part
        for byte in frame[:-4]:
            check = ((check ^ byte) * 16777619) & 0xffffffff
        if check != struct.unpack_from("<I", frame, length - 4)[0]:
            raise ValueError("part checksum")
        offset = 20 + 4 * count
        ids = struct.unpack_from(f"<{count}I", frame, 20)
        postings = []
        for _ in range(rows):
            doc, ordinal, pos, size = struct.unpack_from("<4I", frame, offset)
            offset += 16
            term = frame[offset:offset + size]
            offset += size
            postings.append((doc, ordinal, pos, term))
        if offset != len(frame) - 4:
            raise ValueError("part length")
        parts.append((ids, postings, frame))
    if cursor != len(data):
        raise ValueError("trailing bytes")
    return parts


class Acceptance:
    flags = []

    @classmethod
    def setUpClass(cls):
        output = ROOT / "build"
        output.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix="searchsegments-", dir=output)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.binary = Path(cls.temp.name) / f"search-index{SUFFIX}"
        result = subprocess.run([COMPILER, "build", ROOT / "exemplos/71_search_index.assis",
                                 "--safe", "--debug", *cls.flags, "-o", cls.binary],
                                cwd=ROOT, capture_output=True, timeout=40)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace"))
        cls.evidence = {"binarySha256": digest(cls.binary.read_bytes())}

    def setUp(self):
        self.folder = Path(self.temp.name) / self._testMethodName
        self.folder.mkdir()
        self.bundle = self.folder / "webassis.asis"

    def execute(self, *arguments, data=None, code=0, **options):
        result = subprocess.run([self.binary, *arguments], cwd=self.folder,
                                input=data, capture_output=True, timeout=80, **options)
        self.assertEqual((result.returncode, result.stderr), (code, b""), result.stdout)
        return result.stdout

    def test_global_ranking_and_offsets_against_independent_model(self):
        source = {}
        generator = random.Random(190)
        corpus = bytearray()
        for part in range(16):
            ids = list(range(1, 27)) + [4095]
            generator.shuffle(ids)
            for local in ids:
                doc = part * 4096 + local
                words = generator.choices((b"agua", b"lua", b"rosa", b"eco"), k=9)
                source[doc] = words
                corpus.extend(str(doc).encode() + b"\t" + b" ".join(words) + b"\n")
        self.execute("build-segmented", data=bytes(corpus))
        snapshot = self.bundle.read_bytes()
        self.evidence["modelBundleSha256"] = digest(snapshot)
        self.evidence["modelBundleBytes"] = len(snapshot)
        for part, (ids, postings, _) in enumerate(model_parts(snapshot)):
            expected_ids = sorted(doc - part * 4096 for doc in source if (doc - 1) // 4096 == part)
            self.assertEqual(list(ids), expected_ids)
            expected_rows = set()
            for local in expected_ids:
                position = 0
                for ordinal, token in enumerate(source[part * 4096 + local]):
                    expected_rows.add((local, ordinal, position, token))
                    position += len(token) + 1
            self.assertEqual(len(postings), len(expected_rows))
            self.assertEqual(set(postings), expected_rows)
        for mode in ("and", "or", "phrase"):
            ranked = []
            for doc, words in source.items():
                if mode == "phrase":
                    positions = [i for i in range(len(words) - 1) if words[i:i + 2] == [b"lua", b"eco"]]
                elif mode == "and" and (b"lua" not in words or b"eco" not in words):
                    continue
                else:
                    positions = [i for i, word in enumerate(words) if word in (b"lua", b"eco")]
                if positions:
                    ranked.append((doc, len(positions), sum(len(word) + 1 for word in words[:positions[0]])))
            ranked.sort(key=lambda row: (-row[1], row[0]))
            for offset in (0, 9, 127, 248, 255):
                with self.subTest(mode=mode, offset=offset):
                    expected = ranked[offset:min(offset + 10, 256)]
                    output = self.execute("query-segmented", mode, "lua eco", str(offset))
                    self.assertEqual([tuple(map(int, line.split())) for line in output.splitlines()], expected)

    def test_cross_segment_update_and_failed_later_batch(self):
        self.execute("build-segmented", data=b"1\tlua\n4096\tlua\n4097\tlua\n65535\tlua\n")
        saved = self.bundle.read_bytes()
        self.execute("apply-segmented", data=b"4097\tnova\n1\tinvalido\n", code=1)
        self.assertEqual(self.bundle.read_bytes(), saved)
        self.execute("apply-segmented", data=b"1\tnova\n65535\t\xff\n", code=2)
        self.assertEqual(self.bundle.read_bytes(), saved)
        self.execute("apply-segmented", data=b"1\tnova\n4096\n65535\tnova lua\n")
        self.assertEqual(self.execute("query-segmented", "and", "lua"), b"4097 1 0\n65535 1 5\n")
        self.assertEqual(self.execute("query-segmented", "and", "nova"), b"1 1 0\n65535 1 0\n")
        self.assertFalse((self.folder / "webassis.asis.pending").exists())
        self.execute("build", data=b"1\tlegacy\n")
        self.assertEqual(self.execute("query", "and", "legacy"), b"1 1 0\n")
        self.assertEqual(self.execute("query-segmented", "and", "lua"), b"4097 1 0\n65535 1 5\n")

    def test_corruption_reorder_and_trailing_bytes_fail_closed(self):
        self.execute("build-segmented", data=b"1\tlua\n4097\tlua\n65535\tlua\n")
        saved = self.bundle.read_bytes()
        frames = [part[2] for part in model_parts(saved)]
        swapped = HEADER + frames[1] + frames[0] + b"".join(frames[2:])
        broken = bytearray(saved)
        broken[-5] ^= 1
        for candidate in (saved[:7], saved[:-1], saved + b"x", swapped, bytes(broken),
                          saved[:4] + b"\x02" + saved[5:]):
            with self.subTest(length=len(candidate)):
                self.bundle.write_bytes(candidate)
                self.assertEqual(self.execute("query-segmented", "and", "lua", code=3), b"")
                self.assertEqual(self.execute("apply-segmented", data=b"1\tnova\n", code=3), b"")
                self.assertEqual(self.bundle.read_bytes(), candidate)
        self.bundle.write_bytes(saved)
        self.assertEqual(self.execute("query-segmented", "and", "lua"), b"1 1 0\n4097 1 0\n65535 1 0\n")

    def test_kill_after_writing_segment_and_recover(self):
        self.execute("build-segmented", data=b"1\tlua\n4097\tlua\n")
        before = self.bundle.read_bytes()
        pending = self.folder / "webassis.asis.pending"
        with subprocess.Popen([self.binary, "apply-segmented"], cwd=self.folder, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as writer:
            try:
                writer.stdin.write(b"1\tpending\n4097\tpending\n")
                writer.stdin.flush()
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if pending.exists() and pending.stat().st_size > len(HEADER):
                        break
                    time.sleep(0.02)
                else:
                    self.fail("writer did not finish a candidate segment")
                self.assertEqual(self.execute("query-segmented", "and", "lua"), b"1 1 0\n4097 1 0\n")
                self.execute("apply-segmented", data=b"1\tconcurrent\n", code=8)
            finally:
                writer.kill()
                writer.communicate(timeout=8)
        self.assertEqual(self.bundle.read_bytes(), before)
        self.assertGreater(pending.stat().st_size, len(HEADER))
        self.execute("apply-segmented", data=b"1\tfinal\n4097\n")
        self.assertEqual(self.execute("query-segmented", "and", "final"), b"1 1 0\n")
        self.assertFalse(pending.exists())

    def test_htdl_source_within_a_segment(self):
        htdl = (b"<div type=document version=0.1 lang=en><div type=head>"
                b"<div type=title>ignored</div></div><div type=body>"
                b"<div type=paragraph>lua <div type=text>eco</div></div></div></div>")
        self.execute("build-segmented-htdl", data=b"8193\t" + htdl + b"\n")
        self.assertEqual(self.execute("query-segmented", "phrase", "lua eco"), b"8193 1 0\n")
        self.execute("apply-segmented-htdl", data=b"8193\n")
        self.assertEqual(self.execute("query-segmented", "and", "lua"), b"")


class Optimized(Acceptance, unittest.TestCase):
    @unittest.skipUnless(platform.system() == "Linux", "Linux RLIMIT_AS only")
    def test_bundle_larger_than_process_address_space(self):
        import resource

        cap = 32 * 1024 * 1024

        def limit():
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))

        payload = b"needle " + b" ".join((f"term{i:03d}".encode() + b"x" * 111) for i in range(100))
        source = b"".join(str(part * 4096 + doc).encode() + b"\t" + payload + b"\n"
                          for part in range(16) for doc in range(1, 201))
        started = time.perf_counter()
        self.execute("build-segmented", data=source, preexec_fn=limit)
        built = time.perf_counter()
        size = self.bundle.stat().st_size
        self.assertGreater(size, cap)
        result = self.execute("query-segmented", "and", "needle", preexec_fn=limit)
        self.assertEqual(result, b"".join(f"{doc} 1 0\n".encode() for doc in range(1, 11)))
        queried = time.perf_counter()
        self.execute("apply-segmented", data=b"1\tupdated\n65535\tupdated\n", preexec_fn=limit)
        updated = time.perf_counter()
        self.assertEqual(self.execute("query-segmented", "and", "updated", preexec_fn=limit),
                         b"1 1 0\n65535 1 0\n")
        self.evidence["boundedRun"] = {
            "addressSpaceLimit": cap, "documents": 3200, "snapshotBytes": size,
            "updatedSnapshotSha256": digest(self.bundle.read_bytes()),
            "buildSeconds": round(built - started, 3),
            "querySeconds": round(queried - built, 3),
            "updateSeconds": round(updated - queried, 3),
        }


class Reference(Acceptance, unittest.TestCase):
    flags = ["--no-opt"]


if __name__ == "__main__":
    results = unittest.main(exit=False, verbosity=2).result
    output = os.environ.get("ASSIS_SEARCH_SEGMENTS_EVIDENCE")
    if output and results.wasSuccessful():
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "command": "python tests/test-searchsegments.py",
            "platform": platform.platform(),
            "python": platform.python_version(),
            "compilerSha256": digest(COMPILER.read_bytes()),
            "executed": results.testsRun - len(results.skipped),
            "skipped": len(results.skipped),
            "optimized": Optimized.evidence,
            "reference": Reference.evidence,
        }, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if results.wasSuccessful() else 1)
