#!/usr/bin/env python3
"""Prepare paired manual host evaluations; never infer quality from keywords."""
import argparse
import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ('baseline', 'nexus')
COMPARATIVE_VARIANTS = ('previous', 'candidate')
PROFILES = ('FAST', 'BALANCED', 'DEEP')
PERSISTENCE = ('direct', 'tracked')
COMPARISON_IDENTITIES = ('executor', 'configuration', 'input_context', 'effort')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def validate_suite(suite):
    if not isinstance(suite, dict) or suite.get('schema_version') != 1 or not isinstance(suite.get('scenarios'), list) or not suite['scenarios']:
        raise ValueError('suite requires schema_version 1 and scenarios')
    identifiers = set()
    for scenario in suite['scenarios']:
        if not isinstance(scenario, dict):
            raise ValueError('scenario must be an object')
        identifier = scenario.get('id')
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', identifier) or identifier in identifiers:
            raise ValueError('scenario IDs must be unique safe identifiers')
        identifiers.add(identifier)
        if scenario.get('entry') not in {'nexus', 'nexus-brainstorming', 'nexus-plan', 'nexus-build', 'nexus-debug', 'nexus-review'}:
            raise ValueError('unknown entry')
        for field in ('prompt', 'baseline_prompt'):
            if not isinstance(scenario.get(field), str) or not scenario[field].strip():
                raise ValueError(f'{field} is required')
        rubric = scenario.get('rubric')
        if not isinstance(rubric, dict) or not rubric or any(not isinstance(k, str) or not k or not isinstance(v, str) or not v.strip() for k, v in rubric.items()):
            raise ValueError('rubric requires named nonempty criteria')
        for field, allowed in (('expected_profile', PROFILES), ('expected_persistence', PERSISTENCE)):
            if field in scenario and scenario[field] not in allowed:
                raise ValueError(f'{field} has invalid value')
        fixture = scenario.get('fixture')
        if fixture is not None and (not isinstance(fixture, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', fixture)
                                    or not (ROOT / 'evals/fixtures' / fixture).is_dir()):
            raise ValueError('fixture must name an existing fixture directory')


def prepare(output, run_id, samples, suite_path=None, previous_skills=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', run_id):
        raise ValueError('run-id must be a safe identifier')
    if type(samples) is not int or samples < 1:
        raise ValueError('samples must be a positive integer')
    suite_path = suite_path or ROOT / 'evals/suite.json'
    suite = json.loads(Path(suite_path).read_text())
    validate_suite(suite)
    package = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT / 'skills').rglob('*')) if p.is_file()
               and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    manifest = {'schema_version': 1, 'run_id': run_id, 'samples': samples,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'suite': suite, 'package_sha256': package, 'variants': list(VARIANTS)}
    if previous_skills is not None:
        previous_skills = Path(previous_skills)
        if not (previous_skills / 'nexus/SKILL.md').is_file():
            raise ValueError('previous-skills must contain nexus/SKILL.md')
        manifest['variants'] = list(COMPARATIVE_VARIANTS)
        manifest['conditions'] = {}
        for variant, source in (('previous', previous_skills), ('candidate', ROOT / 'skills')):
            files = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(source.rglob('*')) if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc'}
            manifest['conditions'][variant] = {'snapshot': f'{variant}-skill-snapshot',
                'missing_core_snapshot': f'{variant}-missing-core-snapshot',
                'files_sha256': files, 'identity_sha256': digest(files)}
    manifest['execution_order'] = [
        {'scenario': scenario['id'], 'variant': variant, 'sample': sample}
        for index, scenario in enumerate(suite['scenarios'])
        for sample in range(1, samples + 1)
        for variant in (manifest['variants'] if (index + sample) % 2 else list(reversed(manifest['variants'])))
    ]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'manifest.json', manifest)
    (output / 'manifest.sha256').write_text(digest(manifest) + '\n')
    if previous_skills is None:
        shutil.copytree(ROOT / 'skills', output / 'skill-snapshot',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copytree(output / 'skill-snapshot', output / 'missing-core-snapshot')
        shutil.rmtree(output / 'missing-core-snapshot/nexus')
    for variant, condition in manifest.get('conditions', {}).items():
        source = previous_skills if variant == 'previous' else ROOT / 'skills'
        shutil.copytree(source, output / condition['snapshot'],
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copytree(output / condition['snapshot'], output / condition['missing_core_snapshot'])
        shutil.rmtree(output / condition['missing_core_snapshot'] / 'nexus')
    (output / 'observations').mkdir()
    for scenario in suite['scenarios']:
        for variant in manifest['variants']:
            for sample in range(1, samples + 1):
                cell = output / 'contexts' / scenario['id'] / variant / str(sample)
                cell.mkdir(parents=True)
                prefix = (f"Use {scenario['entry']}.\n" if variant != 'baseline' else '')
                prompt = scenario['prompt'] if variant != 'baseline' else scenario['baseline_prompt']
                (cell / 'prompt.txt').write_text(prefix + prompt + '\n')
                if scenario.get('fixture'):
                    shutil.copytree(ROOT / 'evals/fixtures' / scenario['fixture'], cell / 'workspace')
                else:
                    (cell / 'workspace').mkdir()
    manifest_for(output)
    return manifest


def manifest_for(run):
    run = Path(run)
    manifest = json.loads((run / 'manifest.json').read_text())
    if digest(manifest) != (run / 'manifest.sha256').read_text().strip():
        raise ValueError('manifest changed after preparation')
    validate_suite(manifest['suite'])
    for directory in (() if 'conditions' in manifest else ('skill-snapshot', 'missing-core-snapshot')):
        expected_files = {str(Path(p).relative_to('skills')): value
                          for p, value in manifest['package_sha256'].items()
                          if directory != 'missing-core-snapshot' or Path(p).parts[1] != 'nexus'}
        actual = {str(p.relative_to(run / directory)) for p in (run / directory).rglob('*') if p.is_file()}
        if actual != set(expected_files):
            raise ValueError(f'{directory} file inventory changed after preparation')
        for relative, expected in expected_files.items():
            snapshot = run / directory / relative
            if hashlib.sha256(snapshot.read_bytes()).hexdigest() != expected:
                raise ValueError(f'{directory} changed after preparation')
    for condition in manifest.get('conditions', {}).values():
        if digest(condition['files_sha256']) != condition['identity_sha256']:
            raise ValueError('condition identity changed')
        for key in ('snapshot', 'missing_core_snapshot'):
            directory = run / condition[key]
            expected = {p: h for p, h in condition['files_sha256'].items()
                        if key == 'snapshot' or Path(p).parts[0] != 'nexus'}
            actual = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in directory.rglob('*') if p.is_file()}
            if actual != expected:
                raise ValueError(f'{key} changed after preparation')
    return manifest


def validate_observation(observation, scenario):
    if not isinstance(observation, dict):
        raise ValueError('observation must be an object')
    for field in ('host', 'response', 'reviewer'):
        if not isinstance(observation.get(field), str) or not observation[field].strip():
            raise ValueError(f'{field} must identify observed evidence')
    if observation.get('fresh_context') is not True:
        raise ValueError('each sample requires a fresh independent context')
    for field in ('model',):
        if field not in observation or (observation[field] is not None and not isinstance(observation[field], str)):
            raise ValueError(f'{field} must be observed text or null')
    for field in ('latency_ms', 'calls'):
        value = observation.get(field)
        if field not in observation or (value is not None and
                (type(value) not in (float, int) or value < 0 or not math.isfinite(value))):
            raise ValueError(f'{field} must be nonnegative observed number or null')
        if field == 'calls' and value is not None and type(value) is not int:
            raise ValueError('calls must be an observed integer or null')
    for field in ('commands', 'reference_reads'):
        if field not in observation or (observation[field] is not None and not isinstance(observation[field], list)):
            raise ValueError(f'{field} must be observed list or null')
        if observation[field] is not None and any(not isinstance(item, str) or not item.strip() for item in observation[field]):
            raise ValueError(f'{field} items must be observed nonempty strings')
    for field, allowed in (('profile', PROFILES), ('persistence', PERSISTENCE)):
        if observation.get(field) is not None and observation[field] not in allowed:
            raise ValueError(f'{field} has invalid value')
    for field in ('tokens', 'tool_calls', 'llm_calls'):
        measurement = observation.get(field)
        if measurement is None:
            continue
        unit = 'tokens' if field == 'tokens' else 'calls'
        if (not isinstance(measurement, dict) or type(measurement.get('total')) is not int
                or measurement['total'] < 0 or measurement.get('unit') != unit
                or any(not isinstance(measurement.get(k), str) or not measurement[k].strip()
                       for k in ('source', 'scope'))
                or (field == 'tokens' and measurement['scope'] != 'all-agents')):
            raise ValueError(f'{field} requires observed integer total, source, scope and unit')
    comparison = observation.get('comparison_context')
    if comparison is not None and not valid_comparison_context(comparison):
        raise ValueError('comparison_context requires known executor, configuration, input_context, effort and evidence')
    grades = observation.get('grades')
    if not isinstance(grades, dict) or not grades or set(grades) - set(scenario['rubric']):
        raise ValueError('grades must use scenario rubric identifiers')
    for grade in grades.values():
        if not isinstance(grade, dict) or grade.get('verdict') not in ('pass', 'fail', 'inconclusive') or not isinstance(grade.get('evidence'), str) or not grade['evidence'].strip():
            raise ValueError('each manual grade requires verdict and evidence')


def record(run, scenario_id, variant, sample, observation):
    run = Path(run)
    manifest = manifest_for(run)
    expected_receipts = {f"{scenario['id']}--{variant}--{sample}.json"
                         for scenario in manifest['suite']['scenarios'] for variant in manifest['variants']
                         for sample in range(1, manifest['samples'] + 1)}
    if {p.name for p in (run / 'observations').iterdir()} - expected_receipts:
        raise ValueError('unexpected receipt outside the evaluation matrix')
    scenarios = {s['id']: s for s in manifest['suite']['scenarios']}
    if scenario_id not in scenarios or variant not in manifest['variants'] or type(sample) is not int or not 1 <= sample <= manifest['samples']:
        raise ValueError('unknown evaluation cell')
    validate_observation(observation, scenarios[scenario_id])
    receipt = {'scenario': scenario_id, 'variant': variant, 'sample': sample,
               'recorded_at': datetime.now(timezone.utc).isoformat(), 'observation': observation}
    write_new(run / 'observations' / f'{scenario_id}--{variant}--{sample}.json', receipt)


def report(run):
    run = Path(run)
    manifest = manifest_for(run)
    expected_receipts = {f"{scenario['id']}--{variant}--{sample}.json"
                         for scenario in manifest['suite']['scenarios'] for variant in manifest['variants']
                         for sample in range(1, manifest['samples'] + 1)}
    if {p.name for p in (run / 'observations').iterdir()} - expected_receipts:
        raise ValueError('unexpected receipt outside the evaluation matrix')
    cells, latencies, observations = [], [], {}
    missing = 0
    for scenario in manifest['suite']['scenarios']:
        for variant in manifest['variants']:
            for sample in range(1, manifest['samples'] + 1):
                path = run / 'observations' / f"{scenario['id']}--{variant}--{sample}.json"
                status = 'inconclusive'
                observation = {}
                expectation_results = {}
                if not path.exists():
                    missing += 1
                else:
                    receipt = json.loads(path.read_text())
                    if type(receipt['sample']) is not int or (receipt['scenario'], receipt['variant'], receipt['sample']) != (scenario['id'], variant, sample):
                        raise ValueError('receipt identity differs from evaluation cell')
                    observation = receipt['observation']
                    validate_observation(observation, scenario)
                    observations[(scenario['id'], variant, sample)] = observation
                    grades = observation['grades']
                    verdicts = [g['verdict'] for g in grades.values()]
                    if 'fail' in verdicts:
                        status = 'fail'
                    elif set(grades) == set(scenario['rubric']) and set(verdicts) == {'pass'}:
                        status = 'pass'
                    for field in ('profile', 'persistence'):
                        expected = scenario.get('expected_' + field)
                        if expected is not None:
                            observed = observation.get(field)
                            expectation_results[field] = {
                                'expected': expected, 'observed': observed,
                                'status': 'inconclusive' if observed is None else ('pass' if observed == expected else 'fail')}
                            if observed is not None and observed != expected:
                                status = 'fail'
                            elif observed is None and status != 'fail':
                                status = 'inconclusive'
                    if observation['latency_ms'] is not None:
                        latencies.append(observation['latency_ms'])
                cells.append({'scenario': scenario['id'], 'variant': variant, 'sample': sample, 'status': status,
                              'profile': observation.get('profile'), 'persistence': observation.get('persistence'),
                              'expectations': expectation_results})
    statuses = [c['status'] for c in cells]
    status = 'fail' if 'fail' in statuses else ('inconclusive' if 'inconclusive' in statuses else 'pass')
    by_variant = {variant: {verdict: sum(c['variant'] == variant and c['status'] == verdict for c in cells)
                            for verdict in ('pass', 'fail', 'inconclusive')} for variant in manifest['variants']}
    metrics, paired = summarize_metrics(manifest, observations)
    return {'metrics_by_scenario_variant': metrics, 'paired_by_scenario': paired,
            'legacy_latency_scope': 'All observed cells pooled; descriptive only, not a variant comparison.',
            'run_id': manifest['run_id'], 'status': status, 'expected': len(cells),
            'missing': missing, 'cells': cells, 'latency_observations': len(latencies),
            'by_variant': by_variant,
            'latency_ms_mean': sum(latencies) / len(latencies) if latencies else None,
            'quality_improvement': None,
            'note': 'Manual rubric receipts; no statistical improvement inferred.'}


def metric_value(observation, metric):
    if observation is None:
        return None
    if metric == 'reference_reads':
        value = observation.get(metric)
        return len(value) if value is not None else None
    value = observation.get(metric)
    return value.get('total') if isinstance(value, dict) else value


def known_identity(value):
    return (isinstance(value, str) and bool(value.strip())
            and value.strip().lower() not in {'unknown', 'unobserved', 'unavailable', 'n/a', 'null'})


def valid_comparison_context(context):
    return isinstance(context, dict) and all(
        known_identity(context.get(key)) for key in COMPARISON_IDENTITIES + ('evidence',))


def comparable_execution(a, b):
    """Require explicit common input/executor evidence; unknown equality proves nothing."""
    if a is None or b is None:
        return False
    if any(a.get(key) != b.get(key)
           for key in ('host', 'model', 'configuration', 'effort', 'context', 'executor')):
        return False
    if not known_identity(a.get('model')):
        return False
    ac, bc = a.get('comparison_context'), b.get('comparison_context')
    if not valid_comparison_context(ac) or not valid_comparison_context(bc):
        return False
    # Evidence locations may differ; the declared common identities must match.
    return ({k: v for k, v in ac.items() if k != 'evidence'} ==
            {k: v for k, v in bc.items() if k != 'evidence'})


def summarize_metrics(manifest, observations):
    """Keep coverage local to each scenario; pair only equivalent measurement scopes."""
    metrics = ('latency_ms', 'calls', 'reference_reads', 'tokens', 'tool_calls', 'llm_calls')
    grouped, paired = {}, {}
    left, right = manifest['variants']
    for scenario in manifest['suite']['scenarios']:
        sid = scenario['id']
        grouped[sid], paired[sid] = {}, {}
        for variant in manifest['variants']:
            grouped[sid][variant] = {}
            for metric in metrics:
                values = [metric_value(observations.get((sid, variant, sample)), metric)
                          for sample in range(1, manifest['samples'] + 1)]
                known = [v for v in values if v is not None]
                # Structured measurements with differing scopes stay separately identifiable.
                signatures = sorted({tuple(observations[(sid, variant, sample)][metric][k]
                                           for k in ('scope', 'unit', 'source'))
                                 for sample in range(1, manifest['samples'] + 1)
                                 if metric in ('tokens', 'tool_calls', 'llm_calls')
                                 and observations.get((sid, variant, sample), {}).get(metric) is not None})
                grouped[sid][variant][metric] = {
                    'observed': len(known), 'expected': manifest['samples'],
                    'measurement_signatures': [dict(zip(('scope', 'unit', 'source'), signature))
                                               for signature in signatures],
                    'unit': 'ms' if metric == 'latency_ms' else ('tokens' if metric == 'tokens' else 'count'),
                    'mean': sum(known) / len(known) if known and len(signatures) <= 1 else None}
        for metric in metrics:
            differences, pair_signatures = [], set()
            for sample in range(1, manifest['samples'] + 1):
                a, b = (observations.get((sid, variant, sample)) for variant in (left, right))
                if not comparable_execution(a, b) or metric == 'calls':
                    continue
                if metric in ('tokens', 'tool_calls', 'llm_calls'):
                    am, bm = a.get(metric), b.get(metric)
                    if not am or not bm or any(am[k] != bm[k] for k in ('scope', 'unit', 'source')):
                        continue
                av, bv = metric_value(a, metric), metric_value(b, metric)
                if av is not None and bv is not None:
                    differences.append(bv - av)
                    if metric in ('tokens', 'tool_calls', 'llm_calls'):
                        pair_signatures.add(tuple(a[metric][k] for k in ('scope', 'unit', 'source')))
            paired[sid][metric] = {'left': left, 'right': right,
                'comparable_pairs': len(differences), 'expected_pairs': manifest['samples'],
                'measurement_signatures': [dict(zip(('scope', 'unit', 'source'), signature))
                                           for signature in sorted(pair_signatures)],
                'mean_delta': sum(differences) / len(differences)
                              if differences and len(pair_signatures) <= 1 else None}
    return grouped, paired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_parser = commands.add_parser('prepare')
    prepare_parser.add_argument('--output', type=Path, required=True)
    prepare_parser.add_argument('--run-id', required=True)
    prepare_parser.add_argument('--samples', type=int, default=2)
    prepare_parser.add_argument('--previous-skills', type=Path, help='Previous skills directory for previous/candidate comparison')
    prepare_parser.add_argument('--suite', type=Path, help='Optional versioned subset suite JSON')
    record_parser = commands.add_parser('record')
    record_parser.add_argument('--run', type=Path, required=True)
    record_parser.add_argument('--scenario', required=True)
    record_parser.add_argument('--variant', choices=VARIANTS + COMPARATIVE_VARIANTS, required=True)
    record_parser.add_argument('--sample', type=int, required=True)
    record_parser.add_argument('--observation', type=Path, required=True)
    report_parser = commands.add_parser('report')
    report_parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(args.output, args.run_id, args.samples, args.suite, args.previous_skills)
        elif args.command == 'record':
            record(args.run, args.scenario, args.variant, args.sample, json.loads(args.observation.read_text()))
            result = {'status': 'recorded'}
        else:
            result = report(args.run)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f'{error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
