"""Request structure and byte-safety tests, not reference-conditioned image quality tests."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from prepare_image_request import prepare_request, TEXT_OPENING

ROOT = Path(__file__).resolve().parents[1]


def prepare_visible_human_request(*args, **kwargs):
    """Existing adapter cases now explicitly declare the test portrait scope."""
    return prepare_request(*args, skin_scope={"rendering_medium": "photoreal", "visible_humans": True}, **kwargs)


class StyleReferenceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.prompt = TEXT_OPENING + "\n主体：新成年人物。保留自然纹理，不过度磨皮。"
        path = "examples/series-004-r3.png"
        self.manifest = {
            "schema_version": "style-reference-1",
            "style": {"id": "apricot-colonnade", "version": "0.3.3", "base_version": "0.3.3"},
            "inherit_style_only": ["奶白桃杏灰绿的关系", "柔亮面部与暖发缘"],
            "references": [{"id": "environment", "file": path,
                            "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                            "role": "style_reference", "source_kind": "our_generated_original",
                            "shot_scale": "full-body environment", "provenance": "Own original sample",
                            "limits": "Not a full-spec approval or identity lock"}],
        }

    def assembly(self):
        return {"mode": "generate", "input_images": [],
                "style": {"id": "apricot-colonnade", "version": "0.3.3"},
                "base": {"version": "0.3.3"},
                "prompt_sha256": hashlib.sha256(self.prompt.encode()).hexdigest()}

    def test_explicit_scope_pure_text_has_no_reference_parameters(self):
        request = prepare_visible_human_request(self.prompt)
        self.assertEqual(set(request), {"prompt", "transparent_background"})
        self.assertEqual(request["prompt"], self.prompt)
        self.assertFalse(request["transparent_background"])

    def test_explicit_reference_request_injects_real_paths_and_releases_identity(self):
        request = prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT, assembly=self.assembly())
        self.assertEqual(set(request), {"prompt", "transparent_background", "referenced_image_paths"})
        self.assertEqual(request["referenced_image_paths"], [str(ROOT / self.manifest["references"][0]["file"])])
        self.assertNotIn("本次没有任何参考图输入", request["prompt"])
        self.assertIn("不得继承参考图的人物身份", request["prompt"])
        self.assertIn("不是编辑目标", request["prompt"])
        self.assertIn("主体：新成年人物", request["prompt"])

    def test_wrong_hash_is_rejected(self):
        self.manifest["references"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT, assembly=self.assembly())

    def test_demo_identity_and_competitor_roles_are_rejected(self):
        for role in ("demo", "identity_reference", "third_party_reference"):
            manifest = copy.deepcopy(self.manifest)
            manifest["references"][0]["role"] = role
            with self.subTest(role=role), self.assertRaises(ValueError):
                prepare_visible_human_request(self.prompt, "style-reference", manifest, ROOT, assembly=self.assembly())
        self.manifest["references"][0]["source_kind"] = "competitor"
        with self.assertRaises(ValueError):
            prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT, assembly=self.assembly())

    def test_path_escape_urls_absolute_and_missing_files_are_rejected(self):
        for path in ("../outside.png", "https://example.invalid/image.png", str(ROOT / "examples/series-004-r3.png"), "C:\\outside.png", "missing.png"):
            manifest = copy.deepcopy(self.manifest)
            manifest["references"][0]["file"] = path
            with self.subTest(path=path), self.assertRaises((ValueError, OSError)):
                prepare_visible_human_request(self.prompt, "style-reference", manifest, ROOT, assembly=self.assembly())

    def test_symlink_cannot_escape_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "outside.png").symlink_to(ROOT / "examples/series-004-r3.png")
            self.manifest["references"][0]["file"] = "outside.png"
            with self.assertRaisesRegex(ValueError, "escapes"):
                prepare_visible_human_request(self.prompt, "style-reference", self.manifest, root, assembly=self.assembly())

    def test_text_mode_does_not_silently_ignore_reference_configuration(self):
        with self.assertRaises(ValueError):
            prepare_visible_human_request(self.prompt, "text", self.manifest, ROOT, assembly=self.assembly())
        with self.assertRaises(ValueError):
            prepare_visible_human_request(self.prompt, "text", reference_ids=["environment"])

    def test_reference_selection_requires_known_unique_ids(self):
        for selection in ([], ["missing"], ["environment", "environment"]):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT, selection, self.assembly())
        request = prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT, ["environment"], self.assembly())
        self.assertEqual(len(request["referenced_image_paths"]), 1)

    def test_edit_or_identity_prompts_cannot_be_reinterpreted_as_style_references(self):
        with self.assertRaisesRegex(ValueError, "generate-mode"):
            prepare_visible_human_request("只编辑提供的这一张我方原创图", "style-reference", self.manifest, ROOT, assembly=self.assembly())

    def test_reference_requires_matching_assembly_style_and_prompt(self):
        with self.assertRaises(ValueError):
            prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT)
        for target, key, value in (("style", "id", "silver-window"), ("style", "version", "0.2.0"), ("base", "version", "0.0.1")):
            assembly = self.assembly()
            assembly[target][key] = value
            with self.subTest(target=target, key=key), self.assertRaisesRegex(ValueError, "do not match"):
                prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT, assembly=assembly)
        assembly = self.assembly()
        assembly["prompt_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "prompt SHA256 mismatch"):
            prepare_visible_human_request(self.prompt, "style-reference", self.manifest, ROOT, assembly=assembly)

    def test_cli_refuses_to_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            prompt, output = Path(temp) / "prompt.txt", Path(temp) / "request.json"
            prompt.write_text(self.prompt, encoding="utf-8")
            output.write_text("preserve historical request", encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(ROOT / "prepare_image_request.py"),
                                     "--rendering-medium", "photoreal", "--visible-humans", "yes", "--prompt", str(prompt), "--out", str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(), "preserve historical request")

    def test_cli_reference_request_binds_real_assembly(self):
        with tempfile.TemporaryDirectory() as temp:
            prompt, assembly, output = (Path(temp) / name for name in ("prompt.txt", "assembly.json", "request.json"))
            prompt.write_text(self.prompt, encoding="utf-8")
            assembly.write_text(json.dumps(self.assembly()), encoding="utf-8")
            command = [sys.executable, "-B", str(ROOT / "prepare_image_request.py"), "--rendering-medium", "photoreal", "--visible-humans", "yes", "--prompt", str(prompt),
                       "--mode", "style-reference", "--manifest", str(ROOT / "styles/apricot-colonnade/references.json"),
                       "--assembly-manifest", str(assembly), "--out", str(output)]
            result = subprocess.run(command, cwd=temp, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            request = json.loads(output.read_text())
            self.assertEqual(len(request["referenced_image_paths"]), 2)
            self.assertTrue(all(Path(path).is_file() for path in request["referenced_image_paths"]))

    def test_cli_writes_request_only(self):
        with tempfile.TemporaryDirectory() as temp:
            prompt, output = Path(temp) / "prompt.txt", Path(temp) / "request.json"
            prompt.write_text(self.prompt, encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(ROOT / "prepare_image_request.py"),
                                     "--rendering-medium", "photoreal", "--visible-humans", "yes", "--prompt", str(prompt), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())["prompt"], self.prompt)
            self.assertIn("No image generation", result.stdout)


if __name__ == "__main__":
    unittest.main()
