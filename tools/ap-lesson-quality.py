"""Validate, register or report exact independently reviewed AP lesson batches."""
import argparse
import json
from pathlib import Path
from ap_lesson_quality import check_batch, check_drafts, accept_batch, progress, validate_workspace, claim_batch, write, WORK

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=ROOT)
sub = parser.add_subparsers(dest='command', required=True)
sub.add_parser('check-drafts')
check = sub.add_parser('check'); check.add_argument('batch', nargs='?'); check.add_argument('--reviewed', action='store_true')
accept = sub.add_parser('accept'); accept.add_argument('batch')
claim = sub.add_parser('claim'); claim.add_argument('batch'); claim.add_argument('--author', required=True); claim.add_argument('--reviewer')
status = sub.add_parser('status'); status.add_argument('--write-progress', action='store_true')
args = parser.parse_args()
try:
    root = args.root.resolve()
    if args.command == 'check-drafts':
        result = check_drafts(root)
    elif args.command == 'check':
        result = check_batch(root, args.batch, args.reviewed) if args.batch else validate_workspace(root)
    elif args.command == 'claim':
        result = claim_batch(root, args.batch, args.author, args.reviewer)
    elif args.command == 'accept':
        result = accept_batch(root, args.batch)
        write(root / WORK / 'progress.json', progress(root))
    else:
        result = progress(root)
        if args.write_progress:
            write(root / WORK / 'progress.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
except (ValueError, KeyError, TypeError, OSError) as error:
    parser.exit(1, f'AP quality check failed: {error}\n')
