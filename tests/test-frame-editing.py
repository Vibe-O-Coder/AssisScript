"""HTDL editing transactions and real Win32 text envelopes."""
import ctypes
import importlib.util
import os
from pathlib import Path
import unittest


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog = load("catalog", Path(__file__).with_name("test-catalog-frame.py"))
PROFILE = "framehost::editing_versions()"
BODY = ('<div type=form id=form a11y-label=Form>'
        '<div type=label for=entry>Name</div><div type=input id=entry value="á🌻" required=true></div>'
        '<div type=input kind=number id=amount a11y-label=Amount value="-"></div>'
        '<div type=input kind=number disabled=true a11y-label=Locked value="x"></div>'
        '<div type=button id=submit action=submit>Send</div></div>')
PREFS = "reader::default_preferences(),metric"
ROOT = Path(__file__).resolve().parents[1]


def prepare(body=BODY, **args):
    return catalog.prepare(body, version=PROFILE, **args)


def start(body=BODY):
    return catalog.host.setup() + f"assert({prepare(body)}==0);assert(s.commit(1));"


class FrameEditing(unittest.TestCase):
    setUpClass = classmethod(catalog.CatalogFrame.setUpClass.__func__)
    tearDownClass = classmethod(catalog.CatalogFrame.tearDownClass.__func__)
    setUp = catalog.CatalogFrame.setUp
    invoke = catalog.CatalogFrame.invoke
    source = catalog.CatalogFrame.source
    accepted = catalog.CatalogFrame.accepted
    execute = catalog.CatalogFrame.execute

    def test_grapheme_deletion_and_extension_preserve_other_fields(self):
        self.execute(start() + f"""
            val entry:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("entry"));
            val amount:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("amount"));
            assert(s.snapshot().fields.selection(entry).caret==7);
            assert(s.dispatch(1,ev(3,9,1,1)).kind==1);
            assert(s.dispatch(1,ev(3,8,1,2)).kind==12);
            assert(s.edit_field(1,2,entry,320,200,0,65536,{PREFS})==0);
            assert(len(s.snapshot().fields.value(entry))==7);
            s.abort_reflow();
            assert(s.edit_field(1,2,entry,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(len(s.snapshot().fields.value(entry))==3 && s.snapshot().fields.selection(entry).caret==3);
            assert(s.edit_field(2,2,entry,320,200,0,65536,{PREFS})==204);
            s.dispatch(2,ev(3,16,1,3));
            assert(s.dispatch(2,ev(3,37,1,4)).kind==12);
            assert(s.edit_field(2,4,entry,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(s.snapshot().fields.selection(entry).anchor==3 && s.snapshot().fields.selection(entry).caret==0);
            assert(s.dispatch(3,ev(14,233,1,5)).kind==12);
            assert(s.edit_field(3,5,entry,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(len(s.snapshot().fields.value(entry))==2 && s.snapshot().fields.value(entry)[0]==195);
            assert(s.snapshot().fields.value(amount)[0]==45);
            assert(len(s.snapshot().reading.selected_text())==0);
            assert(s.reflow(340,240,0,131072,0,true,{PREFS})==0 && s.commit_reflow());
            assert(s.snapshot().fields.value(entry)[1]==169 && s.snapshot().fields.selection(entry).caret==2);
        """)

    def test_numeric_validation_publishes_only_committed_state_and_resets_on_navigation(self):
        self.execute(start() + f"""
            val amount:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("amount"));
            s.dispatch(1,ev(3,9,1,1));s.dispatch(1,ev(3,9,1,2));s.dispatch(1,ev(3,9,1,3));
            val invalid:viewer::Change=s.dispatch(1,ev(3,13,1,4));
            assert(invalid.kind==11 && pageframe::same(invalid.node,amount));
            s.dispatch(1,ev(3,13,0,5));
            s.dispatch(1,ev(3,9,1,6));s.dispatch(1,ev(3,9,1,7));
            assert(s.dispatch(1,ev(14,51,1,8)).kind==12);
            assert(s.edit_field(1,8,amount,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            s.dispatch(2,ev(3,9,1,9));
            assert(s.dispatch(2,ev(3,13,1,10)).kind==10);
            assert({prepare(instance=2, request=2)}==0 && s.commit(2));
            val next:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("amount"));
            assert(!s.snapshot().fields.has(amount) && len(s.snapshot().fields.value(next))==1);
            s.dispatch(3,ev(3,9,1,11));
            assert(s.dispatch(3,ev(14,88,1,12)).kind==0);
            assert(!pageedit::valid_number(utf8("+1")) && !pageedit::valid_number(utf8("9223372036854775808")));
            assert(pageedit::valid_number(utf8("-9223372036854775808")));
        """)

    def test_unrelated_input_cancels_edit_and_capacity_failures_are_atomic(self):
        full = '<div type=input id=entry a11y-label=Long value="' + "x" * 1024 + '"></div>'
        self.execute(start(full) + f"""
            val node:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("entry"));
            s.dispatch(1,ev(3,9,1,1));
            assert(s.dispatch(1,ev(14,89,1,2)).kind==12);
            assert(s.edit_field(1,2,node,320,200,0,65536,{PREFS})==401);
            assert(len(s.snapshot().fields.value(node))==1024);
            s.dispatch(1,ev(3,16,1,3));
            assert(s.edit_field(1,2,node,320,200,0,65536,{PREFS})==204);
            assert(s.dispatch(1,ev(14,55296,1,4)).kind==0);
            assert({prepare(full.replace("x" * 1024, "x" * 1025), instance=2, request=2)}==401);
            assert(s.has_active() && !s.has_pending());
        """)

    def test_click_label_focus_and_enter_revalidation(self):
        self.execute(start() + f"""
            val label:pageframe::Rect=s.snapshot().frame.box(2).bounds;
            val entry:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("entry"));
            assert(s.dispatch(1,ev(7,label.x+1,label.y+1,1)).kind==0);
            val click:viewer::Change=s.dispatch(1,ev(8,label.x+1,label.y+1,2));
            assert(click.kind==12 && pageframe::same(click.node,entry));
            assert(s.edit_field(1,2,entry,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(s.dispatch(2,ev(3,13,1,3)).kind==0);
            assert(s.dispatch(2,ev(3,32,1,4)).kind==0);
            assert(s.dispatch(2,ev(14,32,1,5)).kind==12);
            assert(s.edit_field(2,5,entry,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(s.snapshot().fields.value(entry)[7]==32);
        """)

    def test_paste_replaces_selection_once_and_rejects_invalid_or_stale_requests(self):
        self.execute(start() + f"""
            val node:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("entry"));
            val amount:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("amount"));
            assert(s.dispatch(1,ev(3,86,1,1)).kind==0);
            assert(s.dispatch(1,ev(3,9,1,2)).kind==1);
            s.dispatch(1,ev(3,17,1,3));
            assert(s.dispatch(1,ev(3,65,1,4)).kind==12);
            assert(s.edit_field(1,4,node,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(s.dispatch(2,ev(3,86,1,5)).kind==13);
            assert(s.edit_field(2,5,node,320,200,0,65536,{PREFS})==204);
            assert(s.paste_field(2,5,amount,320,200,0,65536,{PREFS},utf8("3"))==204);
            assert(s.paste_field(2,5,node,320,200,0,65536,{PREFS},utf8("a\\nb"))==206);
            assert(s.paste_field(2,5,node,320,200,0,65536,{PREFS},utf8("{'x' * 1025}"))==401);
            assert(len(s.snapshot().fields.value(node))==7 && s.snapshot().fields.selection(node).anchor==0);
            assert(s.paste_field(2,5,node,320,200,0,65536,{PREFS},utf8("Júlia🙂"))==0);
            assert(len(s.snapshot().fields.value(node))==7);
            s.abort_reflow();
            assert(s.paste_field(2,5,node,320,200,0,65536,{PREFS},utf8("Júlia🙂"))==0);
            assert(s.commit_reflow());
            assert(len(s.snapshot().fields.value(node))==10 && s.snapshot().fields.value(node)[0]==74);
            assert(s.snapshot().fields.selection(node).anchor==10 && s.snapshot().fields.selection(node).caret==10);
            assert(s.snapshot().fields.value(amount)[0]==45);
            assert(s.paste_field(3,5,node,320,200,0,65536,{PREFS},utf8("stale"))==204);
            assert(s.dispatch(3,ev(3,86,1,6)).kind==13);
            s.dispatch(3,ev(3,9,1,7));
            assert(s.paste_field(3,6,node,320,200,0,65536,{PREFS},utf8("late"))==204);
        """)


@unittest.skipUnless(os.name == "nt", "Windows text provider required")
class NativeInput(unittest.TestCase):
    def test_utf16_pairs_subscription_and_failed_commit(self):
        from ctypes import c_int32, c_int64, c_size_t, c_ssize_t, c_uint, c_void_p, POINTER
        import _ctypes
        import tempfile

        builder = load("platform_builder", ROOT / "tools/build-platform.py")
        with tempfile.TemporaryDirectory(prefix="assis-native-edit-") as temp:
            provider = Path(temp) / "assis_platform_v1.dll"
            builder.build(provider, testing=True)
            dll = ctypes.WinDLL(str(provider))
            integer = POINTER(c_int64)
            bindings = {
                "open": (c_int32, [c_int64, c_int32, c_int32, ctypes.c_char_p, c_int64, integer]),
                "poll": (c_int32, [c_int64, c_int32, integer, c_int64]),
                "close": (c_int32, [c_int64]),
                "text_events": (c_int32, [c_int64, c_int32]),
                "test_control": (c_int64, [c_int64, c_int64]),
                "frame_editing_commit": (c_int32, [c_int64, c_int64, c_int64, c_uint, integer,
                    c_int64, ctypes.c_char_p, c_int64, integer, c_int64, ctypes.c_char_p, c_int64]),
            }
            for name, (result, args) in bindings.items():
                fn = getattr(dll, "assisp_" + name)
                fn.restype, fn.argtypes = result, args
            token = c_int64()
            self.assertEqual(dll.assisp_open(1, 320, 200, b"Fixture", 7, ctypes.byref(token)), 0)
            hwnd = dll.assisp_test_control(4, token)
            native = ctypes.WinDLL("user32").SendMessageW
            native.argtypes, native.restype = [c_void_p, c_uint, c_size_t, c_ssize_t], c_ssize_t
            post = ctypes.WinDLL("user32").PostMessageW
            post.argtypes, post.restype = native.argtypes, c_int32
            words = (c_int64 * 8)()
            items = (c_int64 * 16)(1, 0, 0, 0, 320, 200, 0, 1, 24, 2, 1, 1, 60, 20, 1, 1)
            names = b"RN\x01\x00v"

            def commit(projection, instance, content=names):
                return dll.assisp_frame_editing_commit(token, projection, instance, 0xffffffff, None, 0, None, 0,
                    items, 2, content, len(content))

            def text_events():
                seen = []
                for _ in range(80):
                    code = dll.assisp_poll(token, 0, words, 8)
                    if code == 1:
                        return seen
                    self.assertEqual(code, 0)
                    if words[1] == 14:
                        seen.append((words[5], words[6]))
                self.fail("native events failed to drain")

            try:
                self.assertGreater(hwnd, 0)
                self.assertEqual(commit(1, 71), 0)
                native(hwnd, 0x0102, ord("A"), 0)
                self.assertEqual(text_events(), [])
                self.assertEqual(dll.assisp_text_events(token, 1), 0)
                native(hwnd, 0x0102, 0xd83c, 0)
                native(hwnd, 0x0102, 0xdf3b, 0)
                native(hwnd, 0x0102, 0xdf3b, 0)
                native(hwnd, 0x0109, 0x1f642, 0)
                native(hwnd, 0x0102, 9, 0)
                self.assertEqual(text_events(), [(0x1f33b, 71), (0x1f642, 71)])
                self.assertEqual(commit(2, 72, b"RN\x04\x00z"), -1)
                native(hwnd, 0x0102, ord("B"), 0)
                self.assertEqual(text_events(), [(ord("B"), 71)])
                native(hwnd, 0x0102, 0xd83c, 0)
                self.assertEqual(commit(2, 72), 0)
                native(hwnd, 0x0102, 0xdf3b, 0)
                native(hwnd, 0x0102, ord("C"), 0)
                self.assertEqual(text_events(), [(ord("C"), 72)])
                self.assertTrue(post(hwnd, 0x0100, ord("J"), 1))
                self.assertTrue(post(hwnd, 0x0100, 9, 1))
                self.assertEqual(dll.assisp_poll(token, 0, words, 8), 0)
                self.assertEqual((words[1], words[5]), (3, ord("J")))
                self.assertEqual(dll.assisp_poll(token, 0, words, 8), 0)
                self.assertEqual((words[1], chr(words[5]).casefold(), words[6]), (14, "j", 72))
                self.assertEqual(dll.assisp_poll(token, 0, words, 8), 0)
                self.assertEqual((words[1], words[5]), (3, 9))
                self.assertEqual(dll.assisp_text_events(token, 0), 0)
                native(hwnd, 0x0102, ord("D"), 0)
                self.assertEqual(text_events(), [])
            finally:
                self.assertEqual(dll.assisp_close(token), 0)
                _ctypes.FreeLibrary(dll._handle)


if __name__ == "__main__":
    unittest.main(verbosity=2)
