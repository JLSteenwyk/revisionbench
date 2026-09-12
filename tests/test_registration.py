import datetime
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from safety_study.registration import source_hash, file_hash, validate_registration


class RegistrationTests(unittest.TestCase):
    def test_freeze_matches_code_config_and_run(self):
        old = Path.cwd()
        with TemporaryDirectory() as temp:
            try:
                os.chdir(temp)
                for directory in ("configs", "docs", "safety_study"):
                    Path(directory).mkdir()
                Path("configs/models.json").write_text("{}")
                Path("docs/protocol.md").write_text("protocol")
                Path("safety_study/world.py").write_text("# frozen simulation")
                plan = dict(tasks=12, repeats=2, max_steps=8, temperature=.7, max_tokens=512, seed=42)
                args = SimpleNamespace(model="qwen", experiment="peer", **plan)
                reg = dict(status="frozen", frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           hypotheses=["source-by-claim effect"], primary_comparisons=["interaction"],
                           sample_size_justification="precision target", exclusions="infrastructure failures",
                           stopping_rules="fixed schedule", multiplicity="one primary contrast", models=["qwen"],
                           experiments={"peer": plan}, code_sha256=source_hash(),
                           file_hashes={f: file_hash(f) for f in ("configs/models.json", "docs/protocol.md")})
                Path("registration.json").write_text(json.dumps(reg))
                validate_registration("registration.json", args)
                args.tasks = 13
                with self.assertRaisesRegex(ValueError, "tasks"):
                    validate_registration("registration.json", args)
                args.tasks = 12
                Path("configs/models.json").write_text('{"changed":true}')
                with self.assertRaisesRegex(ValueError, "file changed"):
                    validate_registration("registration.json", args)
                Path("configs/models.json").write_text("{}")
                Path("safety_study/world.py").write_text("# changed")
                with self.assertRaisesRegex(ValueError, "code differs"):
                    validate_registration("registration.json", args)
            finally:
                os.chdir(old)

    def test_arbitrary_file_is_not_a_registration(self):
        with TemporaryDirectory() as temp:
            f = Path(temp) / "fake.json"
            f.write_text("{}")
            with self.assertRaisesRegex(ValueError, "not frozen"):
                validate_registration(f, SimpleNamespace())
