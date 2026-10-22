"""Portable silver publication checks; not generation-time semantic or aesthetic gates."""
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

from compose_prompt import compose
from prepare_image_request import prepare_request, TEXT_OPENING
from validate_review import validate_review, verify_review_target

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/silver-six-scenes-20261022"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SilverReleaseTests(unittest.TestCase):
    def test_01_actual_versions_and_frozen_base(self):
        base, style = read(ROOT / "base-image-production/base.json"), read(ROOT / "styles/silver-window-v0.2.json")
        self.assertEqual(base["version"], "0.3.3")
        self.assertEqual((style["id"], style["version"], style["base_version"]), ("silver-window", "0.2.0", "0.3.3"))
        self.assertEqual(digest(ROOT / "base-image-production/base.json"), "dd349aca7c6075f57cd7d358d811e69aae308795bf958f9c7af4a694ccbadd9a")
        self.assertEqual(digest(ROOT / "compose_prompt.py"), "afcc26444355590616c1fbcab70f299f7a58b9cd5d17eee9f37595aa2e6792c8")

    def test_02_original_freeze_all_39_files_unchanged(self):
        freeze = read(RUN / "freeze-manifest.json")
        self.assertEqual(len(freeze["files"]), 39)
        self.assertEqual((freeze["base_version"], freeze["style_version"]), ("0.3.3", "0.2.0"))
        self.assertFalse(freeze["automatic_new_gates_implemented"])
        for item in freeze["files"]:
            with self.subTest(file=item["path"]):
                self.assertEqual(digest(ROOT / item["path"]), item["sha256"])

    def test_03_actual_six_requests_remain_pure_text_and_byte_exact(self):
        for index in range(1, 7):
            scene = f"scene-{index:02d}"
            output = RUN / "outputs" / scene
            with self.subTest(scene=scene):
                self.assertEqual((output / "actual-tool-request.json").read_bytes(), (output / "prepared-tool-request.json").read_bytes())
                request = read(output / "actual-tool-request.json")
                self.assertEqual(set(request), {"prompt", "transparent_background"})
                self.assertFalse(request["transparent_background"])
                self.assertEqual(request["prompt"].encode(), (output / "assembled-prompt.txt").read_bytes())
                self.assertTrue(request["prompt"].startswith(TEXT_OPENING))
                manifest = read(output / "assembly-manifest.json")
                self.assertEqual(manifest["mode"], "generate")
                self.assertEqual(manifest["input_images"], [])

    def test_04_six_prompts_recompile_exactly_from_any_working_directory(self):
        for index in range(1, 7):
            scene = f"scene-{index:02d}"
            with self.subTest(scene=scene), tempfile.TemporaryDirectory() as temporary:
                args = [sys.executable, "-B", str(ROOT / "compose_prompt.py"),
                        "--base", str(ROOT / "base-image-production/base.json"),
                        "--style", str(ROOT / "styles/silver-window-v0.2.json"),
                        "--input", str(RUN / "inputs" / (scene + ".json")),
                        "--review", str(RUN / "reviews" / (scene + "-before.json")),
                        "--out", temporary]
                result = subprocess.run(args, cwd=temporary, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((Path(temporary) / "assembled-prompt.txt").read_bytes(), (RUN / "outputs" / scene / "assembled-prompt.txt").read_bytes())

    def test_05_manual_rule_map_line_hashes_match_actual_prompt(self):
        for index in range(1, 7):
            scene = f"scene-{index:02d}"
            mapping = (RUN / "inputs" / (scene + "-rule-map.md")).read_text()
            lines = (RUN / "outputs" / scene / "assembled-prompt.txt").read_text().splitlines()
            pairs = re.findall(r"第(\d+)行，SHA256 ([0-9a-f]{64})", mapping)
            self.assertEqual(len(pairs), 7)
            for number, sha in pairs:
                self.assertEqual(hashlib.sha256(lines[int(number) - 1].encode()).hexdigest(), sha)

    def test_06_before_after_bindings_and_strict_failures_are_preserved(self):
        for index in range(1, 7):
            scene = f"scene-{index:02d}"
            for stage in ("before", "after"):
                review = read(RUN / "reviews" / f"{scene}-{stage}.json")
                summary = validate_review(review, stage)
                verify_review_target(review, ROOT)
                self.assertFalse(summary["visual_quality_automatically_evaluated"])
                self.assertEqual(summary["declared_outcome"], "pass" if stage == "before" else "fail")
            metadata = read(RUN / "outputs" / scene / "image-metadata.json")
            self.assertEqual(digest(RUN / "outputs" / scene / "original.png"), metadata["sha256"])
            self.assertEqual(metadata["image_inputs"], [])
            self.assertFalse(metadata["identity_locked"])

    def test_07_visual_evidence_complete_but_not_automatically_judged(self):
        for index in range(1, 7):
            scene = f"scene-{index:02d}"
            evidence = read(RUN / "reviews" / f"{scene}-visual-evidence.json")
            self.assertEqual(len(evidence["rule_evidence"]), 7)
            self.assertEqual(set(evidence["four_axes"]), {"aesthetic", "style", "brief", "natural"})
            self.assertEqual(evidence["image_sha256"], digest(RUN / "outputs" / scene / "original.png"))
            self.assertFalse(evidence["identity_locked"])
            self.assertFalse(evidence["image_reference_used"])
            for record in evidence["rule_evidence"].values():
                for key in ("verdict", "location", "evidence"):
                    self.assertTrue(record[key].strip())

    def test_08_eight_new_original_png_files_are_valid(self):
        images = sorted((RUN / "outputs").glob("*/original.png")) + sorted((ROOT / "style-reference-assets/apricot").glob("*.png"))
        self.assertEqual(len(images), 8)
        self.assertEqual(len({digest(path) for path in images}), 8)
        for path in images:
            with self.subTest(image=str(path.relative_to(ROOT))):
                data = path.read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                offset, chunks, compressed = 8, [], bytearray()
                while offset < len(data):
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
                self.assertEqual((chunks[0], chunks[-1]), (b"IHDR", b"IEND"))
                self.assertEqual(offset, len(data))
                self.assertEqual((depth, compression, filtering, interlace), (8, 0, 0, 0))
                self.assertIn(color, (2, 6))
                pixels = zlib.decompress(compressed)
                stride = width * (3 if color == 2 else 4) + 1
                self.assertEqual(len(pixels), stride * height)
                self.assertTrue(all(pixels[row * stride] <= 4 for row in range(height)))

    def test_09_curated_manifests_prepare_real_style_reference_requests(self):
        for path in ("styles/silver-window-v0.2/references.json", "styles/apricot-colonnade/references.json"):
            manifest = read(ROOT / path)
            self.assertFalse(manifest["reference_conditioned_visual_tested"])
            self.assertEqual(len(manifest["references"]), 2)
            prompt = TEXT_OPENING + "\n本次是仅用于请求结构检查的原创成年人物说明。保留自然纹理，不过度磨皮。"
            assembly = {"mode": "generate", "input_images": [], "style": manifest["style"],
                        "base": {"version": manifest["style"]["base_version"]},
                        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
            request = prepare_request(prompt, "style-reference", manifest, ROOT, assembly=assembly, skin_scope={"rendering_medium":"photoreal", "visible_humans":True})
            self.assertEqual(len(request["referenced_image_paths"]), 2)
            self.assertTrue(all(Path(p).is_file() for p in request["referenced_image_paths"]))
            self.assertNotIn("没有任何参考图输入", request["prompt"])
        apricot = read(ROOT / "styles/apricot-colonnade/references.json")
        self.assertIn("No native close-up", apricot["coverage_limit"])
        self.assertTrue(all("series-001" not in r["file"] and "series-002" not in r["file"] for r in apricot["references"]))

    def test_10_four_historical_demo_prompts_replay_without_old_images(self):
        for index in range(1, 5):
            demo = ROOT / f"runs/silver-window-demo-{index:02d}"
            style = ROOT / ("versions/silver-window/0.1.0/style.json" if index == 1 else "styles/silver-window-v0.2.json")
            prompt, manifest = compose(read(ROOT / "base-image-production/base.json"), read(style),
                                       read(demo / "inputs" / f"demo-{index:02d}.json"),
                                       design_review=read(demo / "reviews" / f"demo-{index:02d}-before.json"))
            self.assertEqual(prompt.encode(), (demo / "outputs/assembled-prompt.txt").read_bytes())
            self.assertEqual(prompt, read(demo / "outputs/actual-tool-request.json")["prompt"])
            self.assertEqual(manifest["mode"], "generate")


if __name__ == "__main__":
    unittest.main()
