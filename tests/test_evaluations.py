"""Evaluation receipts must distinguish observed failure from missing evidence."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.evaluate import prepare, record, report


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name) / 'run'
        prepare(self.run, 'synthetic-test', 2)

    def observation(self, verdict='pass'):
        return {'host': 'synthetic-test-host', 'model': None, 'fresh_context': True,
                'response': 'Synthetic observation, not a real host result.',
                'commands': [], 'calls': None, 'reference_reads': None,
                'latency_ms': None, 'reviewer': 'unit-test',
                'grades': {'scope': {'verdict': verdict, 'evidence': 'response'}}}

    def test_missing_samples_are_inconclusive_and_unknown_metrics_stay_null(self):
        result = report(self.run)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertEqual(result['missing'], result['expected'])
        self.assertIsNone(result['latency_ms_mean'])

    def test_duplicate_and_unknown_cells_rejected(self):
        record(self.run, 'core-question', 'baseline', 1, self.observation())
        with self.assertRaises(FileExistsError):
            record(self.run, 'core-question', 'baseline', 1, self.observation())
        with self.assertRaises(ValueError):
            record(self.run, '../bad', 'baseline', 1, self.observation())

    def test_failure_is_not_hidden_by_missing_cells(self):
        record(self.run, 'core-question', 'baseline', 1, self.observation('fail'))
        result = report(self.run)
        self.assertEqual(result['status'], 'fail')
        self.assertGreater(result['missing'], 0)

    def test_unobserved_or_invalid_metrics_rejected(self):
        for patch in ({'fresh_context': False}, {'latency_ms': -1}, {'latency_ms': True},
                      {'reviewer': ''}, {'grades': {}}, {'calls': -2},
                      {'grades': {'scope': 'pass'}}, {'commands': [42]},
                      {'reference_reads': ['']}, {'grades': {'scope': {'verdict': 'pass', 'evidence': 1}}}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                record(self.run, 'core-question', 'baseline', 1, {**self.observation(), **patch})

    def test_manifest_tamper_and_missing_rubric_cannot_pass(self):
        record(self.run, 'core-question', 'nexus', 1, self.observation())
        self.assertEqual(report(self.run)['cells'][0]['status'], 'inconclusive')
        manifest = self.run / 'manifest.json'
        data = json.loads(manifest.read_text())
        data['samples'] = 1
        manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            report(self.run)

    def test_baseline_prompts_do_not_invoke_skills(self):
        for name in ('analysis-only', 'entry-override'):
            prompt = (self.run / 'contexts' / name / 'baseline/1/prompt.txt').read_text()
            self.assertNotIn('nexus-', prompt)

    def test_invalid_suite_does_not_create_output(self):
        suite = json.loads((self.run / 'manifest.json').read_text())['suite']
        for patch in ({'id': '../escape'}, {'fixture': '../escape'}, {'rubric': []},
                      {'entry': 'unknown'}, {'baseline_prompt': ''}):
            with self.subTest(patch=patch):
                broken = {**suite, 'scenarios': [{**suite['scenarios'][0], **patch}]}
                path = Path(self.tmp.name) / 'suite.json'
                path.write_text(json.dumps(broken))
                output = Path(self.tmp.name) / 'invalid'
                with self.assertRaises(ValueError):
                    prepare(output, 'invalid', 1, path)
                self.assertFalse(output.exists())

    def test_snapshot_extra_and_modified_files_rejected(self):
        snapshot = self.run / 'skill-snapshot'
        extra = snapshot / 'extra.txt'
        extra.write_text('changed')
        with self.assertRaises(ValueError):
            report(self.run)
        extra.unlink()
        (snapshot / 'nexus/SKILL.md').write_text('changed')
        with self.assertRaises(ValueError):
            report(self.run)

    def test_complete_matrix_and_unexpected_receipt(self):
        manifest = json.loads((self.run / 'manifest.json').read_text())
        for scenario in manifest['suite']['scenarios']:
            for variant in ('baseline', 'nexus'):
                for sample in (1, 2):
                    observation = self.observation()
                    observation['grades'] = {key: {'verdict': 'pass', 'evidence': 'Synthetic test observation'}
                                             for key in scenario['rubric']}
                    record(self.run, scenario['id'], variant, sample, observation)
        result = report(self.run)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['missing'], 0)
        self.assertEqual(result['by_variant']['baseline']['pass'], 22)
        (self.run / 'observations/unexpected.json').write_text('{}')
        with self.assertRaises(ValueError):
            report(self.run)

    def test_missing_core_snapshot_cannot_restore_core_or_change_wrapper(self):
        snapshot = self.run / 'missing-core-snapshot'
        restored = snapshot / 'nexus/SKILL.md'
        restored.parent.mkdir()
        restored.write_text('restored core')
        with self.assertRaises(ValueError):
            report(self.run)
        restored.unlink()
        restored.parent.rmdir()
        (snapshot / 'nexus-review/SKILL.md').write_text('altered wrapper')
        with self.assertRaises(ValueError):
            report(self.run)
