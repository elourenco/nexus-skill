"""CLI adapter. Requests are data; never executable shell commands."""
import argparse
import json
import sys
from pathlib import Path

from .orchestrator import Orchestrator
from .presentation import markdown, metrics
from .store import StateStore, WorkflowError

TEMPLATES = Path(__file__).resolve().parents[2] / 'assets/templates'


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description='NEXUS local task state orchestrator (POSIX, Python 3.10+)')
    parser.add_argument('--state', type=Path, default=Path('.nexus/local/workflow.json'))
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Create an exclusive workflow; never overwrite existing state')
    init.add_argument('--workspace', type=Path, default=Path.cwd())
    init.add_argument('--mode', choices=['FAST', 'BALANCED', 'DEEP'], default='BALANCED')
    init.add_argument('--max-running', type=int, default=1)
    init.add_argument('--max-attempts', type=int, default=3)
    apply = sub.add_parser('apply', help='Apply one atomic, idempotent JSON operation')
    apply.add_argument('--request', required=True, help='JSON file or - for stdin')
    show = sub.add_parser('show', help='Fresh read-only presentation; Markdown is a projection')
    show.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    history = sub.add_parser('history', help='Committed operations; rejected requests are not successes')
    history.add_argument('--task')
    sub.add_parser('metrics', help='Measured receipt counts and wall-clock durations; unknown usage stays null')
    template = sub.add_parser('template', help='Export existing package template to stdout')
    template.add_argument('name', choices=['spec', 'plan', 'task', 'adr', 'memory'])
    demo = sub.add_parser('demo', help='Run a synthetic real red/green flow in a new directory')
    demo.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'template':
            print((TEMPLATES / (args.name + '.md')).read_text(encoding='utf-8'), end='')
            return 0
        if args.command == 'demo':
            from .demo import run_demo
            output(run_demo(args.output_dir))
            return 0
        store = StateStore(args.state)
        engine = Orchestrator(store)
        if args.command == 'init':
            state = engine.initialize(args.workspace, args.mode, args.max_running, args.max_attempts)
            output({'id': state['id'], 'revision': state['revision'], 'state': str(store.path)})
        elif args.command == 'apply':
            raw = sys.stdin.read() if args.request == '-' else Path(args.request).read_text(encoding='utf-8')
            request = json.loads(raw)
            state = engine.apply(request)
            output({'revision': state['revision'], 'operation_id': request['operation_id'], 'status': state['status']})
        else:
            state = store.read()
            if args.command == 'show':
                if args.format == 'json':
                    output(state)
                else:
                    print(markdown(state), end='')
            elif args.command == 'history':
                output([e for e in state['history'] if not args.task or e['task_id'] == args.task])
            elif args.command == 'metrics':
                output(metrics(state))
        return 0
    except (WorkflowError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'error': str(exc), 'outcome': 'rejected or uncertain; inspect state before retry'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
