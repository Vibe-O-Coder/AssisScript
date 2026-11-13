"""Native HTTP service acceptance with an independent raw socket client."""

from contextlib import contextmanager
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import platform
import queue
import socket
import subprocess
import tempfile
import threading
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUFFIX = ".exe" if os.name == "nt" else ""
COMPILER = Path(os.environ.get("ASSIS_BIN", ROOT / "bin" / f"assis{SUFFIX}")).resolve()
KEY = b"0123456789abcdef" * 4
OTHER_KEY = b"abcdef0123456789" * 4
CORPUS = "1\tcafé chá café\n2\tchá café\n3\tchá e bolo\n4\toutro\n".encode()
QUERY = "or\t0\tcafé".encode()


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def reply(peer):
    with peer.makefile("rb") as stream:
        line = stream.readline(1024)
        status = int(line.split()[1])
        fields = {}
        while (line := stream.readline(1024)) != b"\r\n":
            assert line, "truncated response headers"
            name, value = line.split(b":", 1)
            assert name.lower() not in fields
            fields[name.lower()] = value.strip()
        body = stream.read(int(fields[b"content-length"]))
        assert len(body) == int(fields[b"content-length"])
        assert fields[b"cache-control"] == b"no-store"
        assert fields[b"connection"] == b"close"
        assert b"access-control-allow-origin" not in fields
        return status, body


class Acceptance:
    flags = []

    @classmethod
    def setUpClass(cls):
        output = ROOT / "build"
        output.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix="searchservice-", dir=output)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.folder = Path(cls.temp.name)
        cls.service = cls.folder / f"search-service{SUFFIX}"
        cls.index = cls.folder / f"search-index{SUFFIX}"
        for example, target in [
            ("73_search_service.assis", cls.service),
            ("71_search_index.assis", cls.index),
        ]:
            run = subprocess.run(
                [COMPILER, "build", ROOT / "exemplos" / example, "--safe", "--debug",
                 *cls.flags, "-o", target],
                cwd=ROOT, capture_output=True, timeout=40,
            )
            if run.returncode:
                raise RuntimeError(run.stderr.decode(errors="replace"))
        cls.evidence = {
            "serviceSha256": digest(cls.service),
            "indexSha256": digest(cls.index),
        }

    def setUp(self):
        self.corpus = Path(self.temp.name) / self._testMethodName
        self.corpus.mkdir()
        self.write_index(self.corpus, "build", CORPUS)

    def write_index(self, root, command, data):
        run = subprocess.run([self.index, command], input=data, cwd=root, capture_output=True, timeout=15)
        self.assertEqual((run.returncode, run.stderr), (0, b""), run.stdout)

    @contextmanager
    def server(self, root=None, key=KEY, duration=0, port=0, segmented=False):
        arguments = [self.service, str(port), str(duration)]
        if segmented:
            arguments.append("--segments")
        process = subprocess.Popen(
            arguments, cwd=root or self.corpus,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        output = queue.Queue()
        reader = threading.Thread(target=lambda: output.put(process.stdout.readline()), daemon=True)
        try:
            process.stdin.write(key + b"\n")
            process.stdin.close()
            reader.start()
            line = output.get(timeout=10)
            self.assertRegex(line, rb"^READY [1-9][0-9]*\r?\n$")
            bound = int(line.split()[1])
            yield process, bound
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            if reader.ident is not None:
                reader.join(timeout=5)
            extra = process.stdout.read()
            error = process.stderr.read()
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
            self.assertNotIn(key, extra + error)
            self.assertNotIn(QUERY, extra + error)
            self.assertEqual((extra, error), (b"", b""))

    def headers(self, port, body=QUERY):
        return [
            ("Host", f"127.0.0.1:{port}".encode()),
            ("Content-Type", b"text/plain; charset=utf-8"),
            ("Content-Length", str(len(body)).encode()),
            ("X-Assis-Search-Key", KEY),
        ]

    def raw(self, port, fields=None, body=QUERY, start=b"POST /v1/search HTTP/1.1",
            fragments=False, half_close=False):
        if fields is None:
            fields = self.headers(port, body)
        request = start + b"\r\n" + b"".join(
            name.encode() + b": " + value + b"\r\n" for name, value in fields
        ) + b"\r\n" + body
        with socket.create_connection(("127.0.0.1", port), timeout=5) as peer:
            if fragments:
                # Include a CR/LF split and UTF-8 split in real socket writes.
                previous = 0
                for boundary in (1, 25, len(request) - len(body) - 1, len(request) - 1):
                    peer.sendall(request[previous:boundary])
                    previous = boundary
                    time.sleep(0.02)
                peer.sendall(request[previous:])
            else:
                peer.sendall(request)
            if half_close:
                peer.shutdown(socket.SHUT_WR)
            return reply(peer)

    def test_fragmented_requests_and_query_modes(self):
        with self.server() as (_, port):
            self.assertEqual(self.raw(port, fragments=True), (200, b"1 2 0\n2 1 5\n"))
            self.assertEqual(self.raw(port, body="phrase\t0\tchá café".encode()), (200, b"1 1 6\n2 1 0\n"))
            self.assertEqual(self.raw(port, body="and\t1\tchá café".encode()), (200, b"2 2 0\n"))
            self.assertEqual(self.raw(port, body=b"or\t255\tbolo"), (200, b""))
            client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            try:
                client.request("POST", "/v1/search", b"or\t0\tbolo", {
                    "Content-Type": "text/plain; charset=utf-8",
                    "X-Assis-Search-Key": KEY.decode(),
                })
                answer = client.getresponse()
                self.assertEqual((answer.status, answer.read()), (200, b"3 1 7\n"))
            finally:
                client.close()

    def test_authority_framing_and_authentication(self):
        with self.server() as (_, port):
            host, media, length, key = self.headers(port)
            variants = [
                ([media, length, key], 400),
                ([("Host", b"evil.example"), media, length, key], 400),
                ([host, media, length, key, ("hOsT", host[1])], 400),
                ([host, media, length], 403),
                ([host, media, length, (key[0], OTHER_KEY)], 403),
                ([host, media, length, key, key], 400),
                ([host, media, length, key, ("Origin", b"http://evil.example")], 403),
                ([host, media, length, key, ("Transfer-Encoding", b"chunked")], 400),
                ([host, media, length, key, ("Content-Encoding", b"gzip")], 400),
                ([host, media, length, key, ("Expect", b"100-continue")], 417),
                ([host, media, length, key, ("content-length", length[1])], 400),
                ([host, media, ("Content-Length", b"1, 1"), key], 400),
                ([host, media, ("Content-Length", b"9" * 40), key], 413),
                ([host, media, key], 411),
                ([host, length, key], 415),
                ([host, media, length, key, ("Bad ", b"x")], 400),
                ([host, media, length, key, ("Bad", b"x\r\n folded")], 400),
            ]
            for fields, expected in variants:
                with self.subTest(fields=[name for name, _ in fields], expected=expected):
                    self.assertEqual(self.raw(port, fields), (expected, b""))
            self.assertEqual(self.raw(port, start=b"GET /v1/search HTTP/1.1"), (404, b""))
            self.assertEqual(self.raw(port), (200, b"1 2 0\n2 1 5\n"))

    def test_invalid_body_and_header_limits(self):
        with self.server() as (_, port):
            for body in [b"", b"bad\t0\tbolo", b"or\t256\tbolo", b"or\t-1\tbolo",
                         b"or\t0\t\xff", b"or\t0\t\x00", b"or\t0\ta\tb", b"or\t0\ta\nb",
                         b"or\t0\t" + b"a" * 129, b"and\t0\t" + b"a " * 2040]:
                with self.subTest(length=len(body)):
                    if len(body) <= 2064:
                        self.assertEqual(self.raw(port, body=body), (400, b""))
                    else:
                        self.assertEqual(self.raw(port, self.headers(port, body), body=b""), (413, b""))
            with socket.create_connection(("127.0.0.1", port), timeout=5) as peer:
                peer.sendall(b"x" * 4096)
                self.assertEqual(reply(peer), (431, b""))
            self.assertEqual(self.raw(port, self.headers(port), body=QUERY[:-1], half_close=True), (400, b""))
            self.assertEqual(self.raw(port, self.headers(port), body=QUERY + b"!"), (400, b""))

    def test_slow_connections_do_not_block_and_expire(self):
        with self.server() as (_, port):
            with socket.create_connection(("127.0.0.1", port), timeout=5) as slow:
                slow.sendall(b"POST /v1/")
                started = time.perf_counter()
                self.assertEqual(self.raw(port), (200, b"1 2 0\n2 1 5\n"))
                self.evidence["queryWhilePeerPartialMs"] = round((time.perf_counter() - started) * 1000, 3)
                slow.sendall(b"search")
                self.assertEqual(reply(slow), (408, b""))
            self.assertEqual(self.raw(port), (200, b"1 2 0\n2 1 5\n"))

    def test_concurrent_writer_restart_and_snapshot_recovery(self):
        with self.server() as (_, port):
            writer = subprocess.Popen([self.index, "apply"], cwd=self.corpus, stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                writer.stdin.write("1\tmamão\n2\n".encode())
                writer.stdin.flush()
                self.assertEqual(self.raw(port), (200, b"1 2 0\n2 1 5\n"))
                stdout, stderr = writer.communicate(timeout=10)
                self.assertEqual((writer.returncode, stdout, stderr), (0, b"", b""))
            finally:
                if writer.poll() is None:
                    writer.kill()
                    writer.communicate(timeout=10)
            self.assertEqual(self.raw(port), (200, b""))
            path = self.corpus / "webassis.asix"
            valid = path.read_bytes()
            path.unlink()
            self.assertEqual(self.raw(port), (503, b""))
            path.write_bytes(valid[:-1])
            self.assertEqual(self.raw(port), (503, b""))
            path.write_bytes(valid)
            self.assertEqual(self.raw(port, body="and\t0\tmamão".encode()), (200, b"1 1 0\n"))
        with self.server() as (_, port):
            self.assertEqual(self.raw(port, body="and\t0\tmamão".encode()), (200, b"1 1 0\n"))

    def test_two_corpus_directories_and_distinct_keys(self):
        second = self.corpus / "other"
        second.mkdir()
        self.write_index(second, "build", "7\tcafé\n".encode())
        with self.server() as (_, first), self.server(second, OTHER_KEY) as (_, other):
            host, media, length, key = self.headers(other)
            self.assertEqual(self.raw(other), (403, b""))
            self.assertEqual(self.raw(other, [host, media, length, (key[0], OTHER_KEY)]), (200, b"7 1 0\n"))
            self.assertEqual(self.raw(first), (200, b"1 2 0\n2 1 5\n"))

    def test_segmented_service_observes_whole_bundle_replacement(self):
        self.write_index(self.corpus, "build-segmented", "4096\tcafé\n4097\tcafé café\n".encode())
        with self.server(segmented=True) as (_, port):
            self.assertEqual(self.raw(port), (200, b"4097 2 0\n4096 1 0\n"))
            self.write_index(self.corpus, "apply-segmented", "4096\n65535\tcafé\n".encode())
            self.assertEqual(self.raw(port), (200, b"4097 2 0\n65535 1 0\n"))
            bundle = self.corpus / "webassis.asis"
            bundle.write_bytes(bundle.read_bytes()[:-1])
            self.assertEqual(self.raw(port), (503, b""))

    def test_startup_conflict_key_and_graceful_exit(self):
        malformed = subprocess.run([self.service, "0"], input=b"bad\n", capture_output=True,
                                   cwd=self.corpus, timeout=10)
        self.assertEqual((malformed.returncode, malformed.stdout, malformed.stderr), (2, b"", b""))
        with self.server(duration=1500) as (process, port):
            conflict = subprocess.run([self.service, str(port)], input=KEY + b"\n", capture_output=True,
                                      cwd=self.corpus, timeout=10)
            self.assertEqual((conflict.returncode, conflict.stdout, conflict.stderr), (4, b"", b""))
            self.assertEqual(process.wait(timeout=5), 0)
        with self.server(duration=200, port=port) as (restarted, actual):
            self.assertEqual(actual, port)
            self.assertEqual(restarted.wait(timeout=5), 0)


class Optimized(Acceptance, unittest.TestCase):
    pass


class Reference(Acceptance, unittest.TestCase):
    flags = ["--no-opt"]


if __name__ == "__main__":
    results = unittest.main(exit=False, verbosity=2).result
    output = os.environ.get("ASSIS_SEARCH_SERVICE_EVIDENCE")
    if output and results.wasSuccessful():
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "command": "python tests/test-searchservice.py",
            "platform": platform.platform(),
            "python": platform.python_version(),
            "compilerSha256": digest(COMPILER),
            "executed": results.testsRun - len(results.skipped),
            "skipped": len(results.skipped),
            "optimized": Optimized.evidence,
            "reference": Reference.evidence,
        }, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if results.wasSuccessful() else 1)
