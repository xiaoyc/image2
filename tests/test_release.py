"""Offline release regression checks. No image generation or aesthetic scoring."""
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from compose_prompt import compose, validate_image_metadata, verify_source
from validate_review import CHECKS, validate_review, verify_review_target


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.base = load("base-image-production/base.json")
        self.style = load("styles/apricot-colonnade.json")
        self.inputs = load("inputs/series-004-r3.json")
        self.edit = load("inputs/series-004-r3-edit.json")
        self.before = load("examples/series-004-r3-before.json")
        self.after = load("examples/series-004-r3-after.json")

    def assemble(self, **changes):
        args = dict(base=self.base, style=self.style, inputs=self.inputs,
                    edit=self.edit, design_review=self.before)
        args.update(changes)
        return compose(**args)

    def test_current_versions_match(self):
        self.assertEqual(self.base["version"], "0.3.3")
        self.assertEqual(self.style["version"], "0.3.3")
        self.assertEqual(self.style["base_version"], self.base["version"])
        for file in ("base-image-production/SKILL.md", "styles/apricot-colonnade/SKILL.md"):
            self.assertIn('version: "0.3.3"', (ROOT / file).read_text())

    def test_generic_action_rules_reach_assembled_prompt(self):
        prompt, manifest = self.assemble()
        for category in ("physics", "anatomy"):
            self.assertIn(self.base["quality_rules"][category], prompt)
        for phrase in ("目的和单一动作阶段", "抓握或接触", "物体受力", "脚或座面支撑",
                       "骨盆肩肘连动", "目光与颈肩放松", "空闲肢体", "路径不穿过身体或场景结构"):
            self.assertIn(phrase, prompt)
        self.assertEqual(manifest["execution_status"], "assembled_only")
        self.assertFalse(manifest["generation_performed_by_script"])
        self.assertEqual(manifest["network_calls"], 0)
        self.assertEqual(manifest["image_count_requested"], 1)
        self.assertEqual(manifest["prompt_sha256"], hashlib.sha256(prompt.encode()).hexdigest())

    def test_historical_prompt_replay_is_byte_exact(self):
        prompt, manifest = self.assemble(
            base=load("versions/0.3.2/base-image-production/base.json"),
            style=load("versions/0.3.2/styles/apricot-colonnade.json"))
        self.assertEqual(prompt.encode("utf-8"), (ROOT / "examples/series-004-r3-actual-prompt.txt").read_bytes())
        self.assertEqual(manifest["base"]["version"], "0.3.2")
        self.assertNotEqual(prompt, self.assemble()[0])

    def test_source_image_hash(self):
        validate_image_metadata(self.edit, "edit")
        self.assertEqual(verify_source(self.edit, ROOT), ROOT / "examples/series-004-r2.png")

    def test_wrong_source_hash_is_rejected(self):
        self.edit["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            verify_source(self.edit, ROOT)

    def test_before_and_after_are_bound_to_exact_files(self):
        self.assertEqual(validate_review(self.before, "before")["generation_gate"], "declared_pass")
        self.assertEqual(validate_review(self.after, "after")["generation_gate"], "not_applicable")
        self.assertEqual(verify_review_target(self.before, ROOT, ROOT / "inputs/series-004-r3.json"),
                         ROOT / "inputs/series-004-r3.json")
        self.assertEqual(verify_review_target(self.after, ROOT), ROOT / "examples/series-004-r3.png")

    def test_wrong_review_hash_is_rejected(self):
        for original in (self.before, self.after):
            record = copy.deepcopy(original)
            record["target"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                verify_review_target(record, ROOT)

    def test_review_cannot_bind_another_input(self):
        with self.assertRaisesRegex(ValueError, "not the requested input"):
            verify_review_target(self.before, ROOT, ROOT / "inputs/series-004-r3-edit.json")

    def test_missing_and_incomplete_before_are_rejected(self):
        with self.assertRaises(ValueError):
            self.assemble(design_review=None)
        for key in CHECKS:
            record = copy.deepcopy(self.before)
            del record["checks"][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.assemble(design_review=record)

    def test_each_failed_before_check_blocks_assembly(self):
        for key in CHECKS:
            record = copy.deepcopy(self.before)
            record["checks"][key]["status"] = "fail"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "do not generate"):
                self.assemble(design_review=record)

    def test_review_requires_evidence_and_applicable_check(self):
        self.before["checks"]["pose_and_support"]["evidence"] = " "
        with self.assertRaises(ValueError):
            validate_review(self.before)
        for check in self.after["checks"].values():
            check["status"] = "not_applicable"
        with self.assertRaises(ValueError):
            validate_review(self.after)

    def test_after_cannot_replace_before(self):
        with self.assertRaisesRegex(ValueError, "stage mismatch"):
            self.assemble(design_review=self.after)

    def test_failed_after_is_explicit_not_automatic_retry(self):
        self.after["checks"]["pose_and_support"]["status"] = "fail"
        summary = validate_review(self.after)
        self.assertEqual(summary["declared_outcome"], "fail")
        self.assertFalse(summary["automatic_retry"])
        self.assertFalse(summary["visual_quality_automatically_evaluated"])

    def test_modes_are_exclusive(self):
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            self.assemble(reference=self.edit)

    def test_generate_and_identity_reference_are_distinct(self):
        generate_prompt, generated = self.assemble(edit=None)
        self.assertEqual(generated["mode"], "generate")
        self.assertEqual(generated["input_images"], [])
        self.assertIn("没有任何参考图输入", generate_prompt)
        reference = {key: self.edit[key] for key in ("source_kind", "source_file", "source_sha256", "provenance")}
        prompt, manifest = self.assemble(edit=None, reference=reference)
        self.assertEqual(manifest["mode"], "identity_reference")
        self.assertEqual(len(manifest["input_images"]), 1)
        self.assertIn("明确释放旧图", prompt)
        self.assertIn("不是旧画面编辑", prompt)

    def test_version_mismatch_and_illegal_overrides_are_rejected(self):
        self.style["base_version"] = "0.0.0"
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            self.assemble()
        self.style["base_version"] = self.base["version"]
        self.style["overrides"]["anatomy"] = "skip"
        self.style["override_reasons"]["anatomy"] = "not permitted"
        with self.assertRaisesRegex(ValueError, "allowed aesthetic"):
            self.assemble()

    def test_fixed_style_cannot_be_overridden_by_input(self):
        self.inputs["palette"] = "replace"
        with self.assertRaisesRegex(ValueError, "override fixed style"):
            self.assemble()

    def test_non_original_and_escaping_paths_are_rejected(self):
        self.edit["source_kind"] = "third_party_reference"
        with self.assertRaises(ValueError):
            validate_image_metadata(self.edit, "edit")
        self.edit["source_kind"] = "our_generated_original"
        for path in ("../outside.png", "https://example.invalid/source.png"):
            self.edit["source_file"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate_image_metadata(self.edit, "edit")

    def test_cli_current_and_historical_assembly(self):
        for version in ("current", "0.3.2"):
            prefix = ROOT if version == "current" else ROOT / "versions/0.3.2"
            with self.subTest(version=version), tempfile.TemporaryDirectory() as output:
                result = subprocess.run([
                    sys.executable, "-B", str(ROOT / "compose_prompt.py"),
                    "--base", str(prefix / "base-image-production/base.json"),
                    "--style", str(prefix / "styles/apricot-colonnade.json"),
                    "--input", str(ROOT / "inputs/series-004-r3.json"),
                    "--edit", str(ROOT / "inputs/series-004-r3-edit.json"),
                    "--review", str(ROOT / "examples/series-004-r3-before.json"),
                    "--out", output], capture_output=True, text=True, cwd=output)
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = json.loads((Path(output) / "assembly-manifest.json").read_text())
                self.assertTrue(manifest["reference_bytes_verified"])
                self.assertTrue(manifest["design_review"]["summary"]["target_bytes_verified"])

    def test_all_six_png_files_have_valid_structure_crc_and_pixels(self):
        files = sorted((ROOT / "examples").glob("*.png"))
        self.assertEqual(len(files), 6)
        for path in files:
            with self.subTest(file=path.name):
                data = path.read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                offset, chunks, compressed = 8, [], bytearray()
                while offset < len(data):
                    self.assertGreaterEqual(len(data) - offset, 12)
                    length = struct.unpack_from(">I", data, offset)[0]
                    kind = data[offset + 4:offset + 8]
                    payload = data[offset + 8:offset + 8 + length]
                    crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
                    self.assertEqual(zlib.crc32(kind + payload) & 0xffffffff, crc)
                    chunks.append(kind)
                    if kind == b"IHDR":
                        width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
                    if kind == b"IDAT":
                        compressed.extend(payload)
                    offset += length + 12
                self.assertEqual(offset, len(data))
                self.assertEqual(chunks[0], b"IHDR")
                self.assertEqual(chunks[-1], b"IEND")
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)
                self.assertEqual((depth, compression, filtering, interlace), (8, 0, 0, 0))
                self.assertIn(color, (2, 6))
                channels = 3 if color == 2 else 4
                pixels = zlib.decompress(compressed)
                stride = width * channels + 1
                self.assertEqual(len(pixels), stride * height)
                self.assertTrue(all(pixels[row * stride] <= 4 for row in range(height)))

    def test_local_markdown_links_exist(self):
        for path in ROOT.rglob("*.md"):
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                local = target.split("#", 1)[0]
                with self.subTest(file=str(path.relative_to(ROOT)), link=target):
                    self.assertTrue((path.parent / local).exists(), target)


if __name__ == "__main__":
    unittest.main()
