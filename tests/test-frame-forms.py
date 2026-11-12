"""Checkbox state, submission and activation use one committed Frame."""
import importlib.util
import os
from pathlib import Path
import subprocess
import unittest

spec = importlib.util.spec_from_file_location("catalog", Path(__file__).with_name("test-catalog-frame.py"))
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

PROFILE = "framehost::forms_versions()"
BODY = ('<div type=form id=f a11y-label=Form>'
        '<div type=input kind=checkbox id=a required=true></div>'
        '<div type=label for=a>Read first</div>'
        '<div type=input kind=checkbox disabled=true checked=true required=true a11y-label=Locked id=b></div>'
        '<div type=button id=submit action=submit>Go</div></div>')
PREFS = "reader::default_preferences(),metric"


def prepare(body=BODY, **kwargs):
    return catalog.prepare(body, version=PROFILE, **kwargs)


def start(body=BODY, **kwargs):
    return catalog.host.setup() + f"assert({prepare(body, **kwargs)}==0);assert(s.commit(1));"


class FrameForms(unittest.TestCase):
    setUpClass = classmethod(catalog.CatalogFrame.setUpClass.__func__)
    tearDownClass = classmethod(catalog.CatalogFrame.tearDownClass.__func__)
    setUp = catalog.CatalogFrame.setUp
    invoke = catalog.CatalogFrame.invoke
    source = catalog.CatalogFrame.source
    accepted = catalog.CatalogFrame.accepted
    execute = catalog.CatalogFrame.execute

    def test_profile_is_explicit_and_rejects_unsupported_catalog_features(self):
        code = catalog.host.setup() + f"assert({catalog.prepare(BODY)}==203);"
        cases = [
            ("<div type=input a11y-label=Name></div>", 203),
            ("<div type=input kind=number a11y-label=Amount></div>", 203),
            ("<div type=image src=asset.png alt=Photo></div>", 203),
            ("<div type=section a11y-live=polite> </div>", 203),
            ("<div type=input kind=checkbox id=x></div><div type=label hidden=true for=x>Hidden</div>", 207),
        ]
        for i, (body, status) in enumerate(cases, 2):
            code += f"assert({prepare(body,instance=i,request=i)}=={status} && !s.has_pending());"
        self.execute(code)

    def test_keyboard_label_and_required_checkbox_use_committed_state(self):
        code = start() + f"""
            val a:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("a"));
            val b:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("b"));
            val f:doctree::NodeId=htdl::find_id(s.document().nodes(),utf8("f"));
            assert(s.snapshot().frame.checked(a)==0 && s.snapshot().frame.checked(b)==1);
            assert(len(s.snapshot().frame.name(2))==10 && s.snapshot().frame.name(2)[0]==82);
            assert(s.snapshot().frame.checkbox_mark(2).height==16);
            assert(pageframe::same(s.dispatch(1,ev(3,9,1,1)).node,a));
            assert(s.dispatch(1,ev(3,13,1,2)).kind==0);
            assert(s.dispatch(1,ev(3,13,0,3)).kind==0);
            s.dispatch(1,ev(3,9,1,4));
            val invalid:viewer::Change=s.dispatch(1,ev(3,13,1,5));
            assert(invalid.kind==11 && pageframe::same(invalid.node,a));
            s.dispatch(1,ev(3,13,0,6));
            val label:pageframe::Rect=s.snapshot().frame.box(3).bounds;
            val checkbox:pageframe::Rect=s.snapshot().frame.box(2).bounds;
            assert(s.dispatch(1,ev(7,label.x+1,label.y+1,7)).kind==0);
            assert(s.dispatch(1,ev(8,checkbox.x+1,checkbox.y+1,8)).kind==0);
            assert(!pageframe::same(s.snapshot().reading.focus_node(),a));
            s.dispatch(1,ev(7,label.x+1,label.y+1,9));
            val click:viewer::Change=s.dispatch(1,ev(8,label.x+1,label.y+1,10));
            assert(click.kind==9 && pageframe::same(click.node,a) && pageframe::same(s.snapshot().reading.focus_node(),a));
            assert(s.toggle_checkbox(1,b,320,200,0,65536,{PREFS})==204);
            assert(s.toggle_checkbox(1,a,320,200,0,65536,{PREFS})==0);
            assert(s.snapshot().frame.checked(a)==0);
            s.abort_reflow();
            assert(s.snapshot().frame.checked(a)==0);
            assert(s.toggle_checkbox(1,a,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(s.snapshot().frame.checked(a)==1 && s.snapshot().frame.checked(b)==1);
            assert(s.toggle_checkbox(1,a,320,200,0,65536,{PREFS})==204);
            assert(s.dispatch(2,ev(3,9,1,11)).kind==1);
            val submitted:viewer::Change=s.dispatch(2,ev(3,13,1,12));
            assert(submitted.kind==10 && pageframe::same(submitted.node,f));
            assert(s.reflow(320,200,0,131072,0,true,{PREFS})==0 && s.commit_reflow());
            assert(s.snapshot().frame.checked(a)==1 && s.snapshot().frame.checkbox_mark(2).width==32);
        """
        self.execute(code)

    def test_checkbox_space_repeats_and_navigation_revoke_state(self):
        code = start() + f"""
            val a:doctree::NodeId=s.snapshot().frame.box(2).node;
            assert(s.dispatch(1,ev(3,9,1,1)).kind==1);
            assert(s.dispatch(1,ev(3,32,1,2)).kind==0);
            assert(s.dispatch(1,ev(3,32,1,3)).kind==0);
            assert(s.dispatch(1,ev(3,32,0,4)).kind==9);
            assert(s.dispatch(1,ev(3,32,0,5)).kind==0);
            assert(s.toggle_checkbox(1,a,320,200,0,65536,{PREFS})==0 && s.commit_reflow());
            assert(s.snapshot().frame.checked(a)==1);
            assert({prepare(instance=2,request=2)}==0 && s.commit(2));
            assert(s.snapshot().frame.checked(a)== -1);
            assert(s.snapshot().frame.checked(s.snapshot().frame.box(2).node)==0);
            assert(s.toggle_checkbox(3,a,320,200,0,65536,{PREFS})==204);
        """
        self.execute(code)

    @unittest.skipUnless(os.name == "nt", "Windows forms provider unavailable")
    def test_provider_publication_failure_rolls_back_checked_state(self):
        source = catalog.host.setup() + f"""
            own w:window::Window=try_new window::Window(7,320,200,utf8("Forms failure oracle"));
            assert(w!=null && w.opened() && pagepresent::forms_available());
            assert({prepare()}==0 && s.publish(1,w)==0);
            val a:doctree::NodeId=s.snapshot().frame.box(2).node;
            assert(s.toggle_checkbox(1,a,320,200,0,65536,{PREFS})==0);
            unsafe {{assert(control(0,0)==0);}}
            assert(s.publish_reflow(w)== -4);
            unsafe {{assert(control(0,-1)==0);}}
            assert(s.snapshot().frame.version()==1 && s.snapshot().frame.checked(a)==0);
            s.abort_reflow();
            assert(s.toggle_checkbox(1,a,320,200,0,65536,{PREFS})==0 && s.publish_reflow(w)==0);
            assert(s.snapshot().frame.version()==2 && s.snapshot().frame.checked(a)==1);
        """
        self.execute(source, prefix='extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(op:int,arg:int):int;')

    @unittest.skipUnless(os.name == "nt", "Windows forms provider unavailable")
    def test_native_example_in_both_compiler_modes(self):
        for mode, flags in enumerate(([], ["--no-opt"])):
            binary = self.temp / f"forms-{mode}.exe"
            result = self.invoke("build", catalog.base.ROOT / "exemplos/72_local_forms_window.assis", "--debug", "-o", binary, *flags)
            self.assertEqual(result.returncode, 0, result.stderr)
            run = subprocess.run([binary, "--smoke"], cwd=self.temp, capture_output=True, text=True, timeout=30)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "FORMS WINDOW 3 1\n", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
