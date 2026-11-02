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
        fixture = scenario.get('fixture')
        if fixture is not None and (not isinstance(fixture, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', fixture)
                                    or not (ROOT / 'evals/fixtures' / fixture).is_dir()):
            raise ValueError('fixture must name an existing fixture directory')


def prepare(output, run_id, samples, suite_path=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', run_id):
        raise ValueError('run-id must be a safe identifier')
    if type(samples) is not int or samples < 1:
        raise ValueError('samples must be a positive integer')
    suite_path = suite_path or ROOT / 'evals/suite.json'
    suite = json.loads(Path(suite_path).read_text())
    validate_suite(suite)
    package = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT / 'skills').rglob('*')) if p.is_file()
               and '__pycache__' not in p.parts}
    manifest = {'schema_version': 1, 'run_id': run_id, 'samples': samples,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'suite': suite, 'package_sha256': package, 'variants': list(VARIANTS)}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'manifest.json', manifest)
    (output / 'manifest.sha256').write_text(digest(manifest) + '\n')
    shutil.copytree(ROOT / 'skills', output / 'skill-snapshot',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(output / 'skill-snapshot', output / 'missing-core-snapshot')
    shutil.rmtree(output / 'missing-core-snapshot/nexus')
    (output / 'observations').mkdir()
    for scenario in suite['scenarios']:
        for variant in VARIANTS:
            for sample in range(1, samples + 1):
                cell = output / 'contexts' / scenario['id'] / variant / str(sample)
                cell.mkdir(parents=True)
                prefix = (f"Use {scenario['entry']}.\n" if variant == 'nexus' else '')
                prompt = scenario['prompt'] if variant == 'nexus' else scenario['baseline_prompt']
                (cell / 'prompt.txt').write_text(prefix + prompt + '\n')
                if scenario.get('fixture'):
                    shutil.copytree(ROOT / 'evals/fixtures' / scenario['fixture'], cell / 'workspace')
                else:
                    (cell / 'workspace').mkdir()
    return manifest


def manifest_for(run):
    run = Path(run)
    manifest = json.loads((run / 'manifest.json').read_text())
    if digest(manifest) != (run / 'manifest.sha256').read_text().strip():
        raise ValueError('manifest changed after preparation')
    validate_suite(manifest['suite'])
    for directory in ('skill-snapshot', 'missing-core-snapshot'):
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
                         for scenario in manifest['suite']['scenarios'] for variant in VARIANTS
                         for sample in range(1, manifest['samples'] + 1)}
    if {p.name for p in (run / 'observations').iterdir()} - expected_receipts:
        raise ValueError('unexpected receipt outside the evaluation matrix')
    scenarios = {s['id']: s for s in manifest['suite']['scenarios']}
    if scenario_id not in scenarios or variant not in VARIANTS or type(sample) is not int or not 1 <= sample <= manifest['samples']:
        raise ValueError('unknown evaluation cell')
    validate_observation(observation, scenarios[scenario_id])
    receipt = {'scenario': scenario_id, 'variant': variant, 'sample': sample,
               'recorded_at': datetime.now(timezone.utc).isoformat(), 'observation': observation}
    write_new(run / 'observations' / f'{scenario_id}--{variant}--{sample}.json', receipt)


def report(run):
    run = Path(run)
    manifest = manifest_for(run)
    expected_receipts = {f"{scenario['id']}--{variant}--{sample}.json"
                         for scenario in manifest['suite']['scenarios'] for variant in VARIANTS
                         for sample in range(1, manifest['samples'] + 1)}
    if {p.name for p in (run / 'observations').iterdir()} - expected_receipts:
        raise ValueError('unexpected receipt outside the evaluation matrix')
    cells, latencies = [], []
    missing = 0
    for scenario in manifest['suite']['scenarios']:
        for variant in VARIANTS:
            for sample in range(1, manifest['samples'] + 1):
                path = run / 'observations' / f"{scenario['id']}--{variant}--{sample}.json"
                status = 'inconclusive'
                if not path.exists():
                    missing += 1
                else:
                    receipt = json.loads(path.read_text())
                    if (receipt['scenario'], receipt['variant'], receipt['sample']) != (scenario['id'], variant, sample):
                        raise ValueError('receipt identity differs from evaluation cell')
                    observation = receipt['observation']
                    validate_observation(observation, scenario)
                    grades = observation['grades']
                    verdicts = [g['verdict'] for g in grades.values()]
                    if 'fail' in verdicts:
                        status = 'fail'
                    elif set(grades) == set(scenario['rubric']) and set(verdicts) == {'pass'}:
                        status = 'pass'
                    if observation['latency_ms'] is not None:
                        latencies.append(observation['latency_ms'])
                cells.append({'scenario': scenario['id'], 'variant': variant, 'sample': sample, 'status': status})
    statuses = [c['status'] for c in cells]
    status = 'fail' if 'fail' in statuses else ('inconclusive' if 'inconclusive' in statuses else 'pass')
    by_variant = {variant: {verdict: sum(c['variant'] == variant and c['status'] == verdict for c in cells)
                            for verdict in ('pass', 'fail', 'inconclusive')} for variant in VARIANTS}
    return {'run_id': manifest['run_id'], 'status': status, 'expected': len(cells),
            'missing': missing, 'cells': cells, 'latency_observations': len(latencies),
            'by_variant': by_variant,
            'latency_ms_mean': sum(latencies) / len(latencies) if latencies else None,
            'quality_improvement': None,
            'note': 'Manual rubric receipts; no statistical improvement inferred.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_parser = commands.add_parser('prepare')
    prepare_parser.add_argument('--output', type=Path, required=True)
    prepare_parser.add_argument('--run-id', required=True)
    prepare_parser.add_argument('--samples', type=int, default=2)
    prepare_parser.add_argument('--suite', type=Path, help='Optional versioned subset suite JSON')
    record_parser = commands.add_parser('record')
    record_parser.add_argument('--run', type=Path, required=True)
    record_parser.add_argument('--scenario', required=True)
    record_parser.add_argument('--variant', choices=VARIANTS, required=True)
    record_parser.add_argument('--sample', type=int, required=True)
    record_parser.add_argument('--observation', type=Path, required=True)
    report_parser = commands.add_parser('report')
    report_parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(args.output, args.run_id, args.samples, args.suite)
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
