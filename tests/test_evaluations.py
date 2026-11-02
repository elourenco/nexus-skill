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
        cell = next(c for c in report(self.run)['cells']
                    if (c['scenario'], c['variant'], c['sample']) == ('core-question', 'nexus', 1))
        self.assertEqual(cell['status'], 'inconclusive')
        observation = self.observation()
        observation['grades']['evidence'] = {'verdict': 'pass', 'evidence': 'observed'}
        record(self.run, 'core-question', 'nexus', 2, observation)
        cell = next(c for c in report(self.run)['cells']
                    if (c['scenario'], c['variant'], c['sample']) == ('core-question', 'nexus', 2))
        self.assertEqual(cell['status'], 'pass')
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


    def comparative(self, **expectations):
        suite = json.loads((self.run / 'manifest.json').read_text())['suite']
        suite['scenarios'] = [{**suite['scenarios'][0], **expectations}]
        suite_path = Path(self.tmp.name) / 'subset.json'
        suite_path.write_text(json.dumps(suite))
        output = Path(self.tmp.name) / 'comparison'
        from scripts.evaluate import ROOT
        manifest = prepare(output, 'comparison', 2, suite_path, ROOT / 'skills')
        return output, manifest

    def complete_observation(self, **values):
        observation = self.observation()
        observation['model'] = 'observed-model'
        observation['comparison_context'] = {
            'executor': 'verified-test-executor-v1', 'configuration': 'verified-test-config-v1',
            'input_context': 'verified-common-fixture-v1', 'effort': 'medium',
            'evidence': 'Synthetic unittest fixture; not real host evidence'}
        observation['grades']['evidence'] = {'verdict': 'pass', 'evidence': 'observed'}
        return {**observation, **values}

    def test_comparative_prompts_snapshots_and_order(self):
        run, manifest = self.comparative()
        self.assertEqual(manifest['variants'], ['previous', 'candidate'])
        self.assertEqual([c['variant'] for c in manifest['execution_order']],
                         ['previous', 'candidate', 'candidate', 'previous'])
        for sample in (1, 2):
            self.assertEqual((run / f'contexts/core-question/previous/{sample}/prompt.txt').read_bytes(),
                             (run / f'contexts/core-question/candidate/{sample}/prompt.txt').read_bytes())
        for variant in manifest['variants']:
            snapshot = run / manifest['conditions'][variant]['snapshot'] / 'nexus/SKILL.md'
            original = snapshot.read_bytes()
            snapshot.write_bytes(b'tampered')
            with self.assertRaises(ValueError):
                report(run)
            snapshot.write_bytes(original)
        self.assertEqual(report(run)['missing'], 4)

    def test_required_profile_and_persistence(self):
        run, _ = self.comparative(expected_profile='FAST', expected_persistence='direct')
        record(run, 'core-question', 'previous', 1, self.complete_observation())
        record(run, 'core-question', 'candidate', 1,
               self.complete_observation(profile='DEEP', persistence='direct'))
        record(run, 'core-question', 'candidate', 2,
               self.complete_observation(profile='FAST', persistence='direct'))
        statuses = {(c['variant'], c['sample']): c['status'] for c in report(run)['cells']}
        self.assertEqual(statuses[('previous', 1)], 'inconclusive')
        self.assertEqual(statuses[('candidate', 1)], 'fail')
        self.assertEqual(statuses[('candidate', 2)], 'pass')

    def test_optional_measurements_validate_without_rejecting_provenance(self):
        from scripts.evaluate import validate_observation, validate_suite
        scenario = json.loads((self.run / 'manifest.json').read_text())['suite']['scenarios'][0]
        for patch in ({'profile': 'fast'}, {'persistence': False}, {'tokens': 12},
                      {'tokens': {'total': True, 'source': 'trace', 'scope': 'all-agents', 'unit': 'tokens'}},
                      {'tokens': {'total': 1, 'source': 'trace', 'scope': 'main-agent', 'unit': 'tokens'}},
                      {'tool_calls': {'total': -1, 'source': 'trace', 'scope': 'all', 'unit': 'calls'}},
                      {'llm_calls': {'total': float('nan'), 'source': 'trace', 'scope': 'all', 'unit': 'calls'}},
                      {'tool_calls': {'total': 1, 'source': 'trace', 'scope': 'all', 'unit': 'tokens'}}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate_observation({**self.observation(), **patch}, scenario)
        validate_observation({**self.observation(), 'profile': None, 'persistence': None,
                              'tokens': None, 'session_id': 'extra-provenance'}, scenario)
        for field in ('expected_profile', 'expected_persistence'):
            with self.assertRaises(ValueError):
                validate_suite({'schema_version': 1, 'scenarios': [{**scenario, field: 'invalid'}]})

    def test_partial_metrics_pair_only_comparable_observations(self):
        run, _ = self.comparative()
        measurement = lambda total: {'total': total, 'source': 'trace', 'scope': 'all-agents', 'unit': 'tokens'}
        record(run, 'core-question', 'previous', 1,
               self.complete_observation(latency_ms=100, tokens=measurement(40)))
        record(run, 'core-question', 'candidate', 1,
               self.complete_observation(latency_ms=80, tokens=measurement(30)))
        record(run, 'core-question', 'previous', 2,
               self.complete_observation(latency_ms=500, tokens=measurement(90)))
        record(run, 'core-question', 'candidate', 2,
               self.complete_observation(latency_ms=10, model='different-model'))
        result = report(run)
        pairs = result['paired_by_scenario']['core-question']
        self.assertEqual(pairs['latency_ms']['comparable_pairs'], 1)
        self.assertEqual(pairs['latency_ms']['mean_delta'], -20)
        self.assertEqual(pairs['tokens']['mean_delta'], -10)
        self.assertEqual(pairs['tokens']['expected_pairs'], 2)
        candidate = result['metrics_by_scenario_variant']['core-question']['candidate']
        self.assertEqual(candidate['tokens']['observed'], 1)
        self.assertIsNone(candidate['llm_calls']['mean'])
        self.assertIsNone(result['quality_improvement'])

    def test_receipt_identity_tamper_rejected(self):
        record(self.run, 'core-question', 'nexus', 1, self.observation())
        path = self.run / 'observations/core-question--nexus--1.json'
        receipt = json.loads(path.read_text())
        receipt['variant'] = 'baseline'
        path.write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):
            report(self.run)


    def test_comparative_missing_core_inventory_and_workspace_isolation(self):
        run, manifest = self.comparative()
        first = run / 'contexts/core-question/previous/1/workspace/local.txt'
        first.write_text('isolated change')
        self.assertFalse((run / 'contexts/core-question/candidate/1/workspace/local.txt').exists())
        for variant in manifest['variants']:
            snapshot = run / manifest['conditions'][variant]['missing_core_snapshot']
            self.assertFalse((snapshot / 'nexus').exists())
            extra = snapshot / 'unexpected.txt'
            extra.write_text('tampered inventory')
            with self.assertRaises(ValueError):
                report(run)
            extra.unlink()
        self.assertEqual(report(run)['missing'], 4)

    def test_pairing_rejects_different_scope_source_and_unknown_model(self):
        run, _ = self.comparative()
        def calls(scope, source):
            return {'total': 1, 'source': source, 'scope': scope, 'unit': 'calls'}
        record(run, 'core-question', 'previous', 1, self.complete_observation(
            tool_calls=calls('all-agents', 'trace'), llm_calls=calls('main-agent', 'trace')))
        record(run, 'core-question', 'candidate', 1, self.complete_observation(
            tool_calls=calls('main-agent', 'trace'), llm_calls=calls('main-agent', 'different-source')))
        for variant in ('previous', 'candidate'):
            record(run, 'core-question', variant, 2, self.complete_observation(model=None, latency_ms=10))
        pairs = report(run)['paired_by_scenario']['core-question']
        for metric in ('tool_calls', 'llm_calls', 'latency_ms'):
            self.assertEqual(pairs[metric]['comparable_pairs'], 0)
            self.assertIsNone(pairs[metric]['mean_delta'])


    def test_old_manifest_without_execution_order_remains_readable(self):
        from scripts.evaluate import digest
        path = self.run / 'manifest.json'
        manifest = json.loads(path.read_text())
        del manifest['execution_order']
        path.write_text(json.dumps(manifest))
        (self.run / 'manifest.sha256').write_text(digest(manifest))
        record(self.run, 'core-question', 'baseline', 1, self.observation())
        self.assertEqual(report(self.run)['missing'], 43)

    def test_heterogeneous_paired_measurement_scopes_have_no_combined_delta(self):
        run, _ = self.comparative()
        for sample, scope in ((1, 'all-agents'), (2, 'main-agent')):
            for variant in ('previous', 'candidate'):
                measurement = {'total': 4, 'source': 'trace', 'scope': scope, 'unit': 'calls'}
                record(run, 'core-question', variant, sample,
                       self.complete_observation(tool_calls=measurement))
        result = report(run)
        pairs = result['paired_by_scenario']['core-question']['tool_calls']
        self.assertEqual(pairs['comparable_pairs'], 2)
        self.assertEqual(len(pairs['measurement_signatures']), 2)
        self.assertIsNone(pairs['mean_delta'])
        grouped = result['metrics_by_scenario_variant']['core-question']['candidate']['tool_calls']
        self.assertIsNone(grouped['mean'])


    def test_unknown_or_divergent_execution_context_does_not_produce_delta(self):
        from scripts.evaluate import summarize_metrics
        manifest = {'variants': ['previous', 'candidate'], 'samples': 1,
                    'suite': {'scenarios': [{'id': 'case'}]}}
        base = self.complete_observation(latency_ms=100)
        for overrides in (
                {'comparison_context': None},
                {'context': 'extra preloaded summary and previous solution'},
                {'effort': 'high'},
                {'configuration': {'different': True}},
                {'comparison_context': {**base['comparison_context'], 'input_context': 'other-fixture'}},
                {'comparison_context': {**base['comparison_context'], 'executor': 'other-executor'}},
                {'comparison_context': {**base['comparison_context'], 'configuration': 'other-config'}},
                {'comparison_context': {**base['comparison_context'], 'effort': 'high'}}):
            with self.subTest(overrides=overrides):
                candidate = {**base, 'latency_ms': 20, **overrides}
                grouped, paired = summarize_metrics(manifest, {
                    ('case', 'previous', 1): base, ('case', 'candidate', 1): candidate})
                self.assertEqual(grouped['case']['candidate']['latency_ms']['mean'], 20)
                self.assertEqual(paired['case']['latency_ms']['comparable_pairs'], 0)
                self.assertIsNone(paired['case']['latency_ms']['mean_delta'])
        unknown = {**base, 'comparison_context': None}
        _, paired = summarize_metrics(manifest, {
            ('case', 'previous', 1): unknown, ('case', 'candidate', 1): unknown})
        self.assertIsNone(paired['case']['latency_ms']['mean_delta'])

    def test_comparison_context_requires_explicit_known_identities_and_evidence(self):
        from scripts.evaluate import validate_observation
        scenario = json.loads((self.run / 'manifest.json').read_text())['suite']['scenarios'][0]
        base = self.complete_observation()
        for context in ({}, 'identity', {**base['comparison_context'], 'effort': None},
                        {**base['comparison_context'], 'effort': 'unknown'},
                        {**base['comparison_context'], 'executor': 'unavailable'},
                        {**base['comparison_context'], 'configuration': ' '},
                        {**base['comparison_context'], 'executor': {}},
                        {**base['comparison_context'], 'input_context': None},
                        {**base['comparison_context'], 'evidence': ''}):
            with self.subTest(context=context), self.assertRaises(ValueError):
                validate_observation({**base, 'comparison_context': context}, scenario)
        validate_observation({**base, 'comparison_context': None}, scenario)
