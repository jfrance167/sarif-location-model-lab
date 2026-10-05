"""Stdin/stdout adapter; no filename, artifact, schema or network access."""
import sys
from model import Invalid, decode, failure, interpret, serialize, MAX_INPUT

HELP = b'Usage: python cli.py < synthetic.json\nOffline supplied SARIF metadata only; no artifact access.\n'


def deliver(stream, payload):
    """A short or failed write is failure even if some bytes escaped."""
    written = stream.write(payload)
    if type(written) is not int or written != len(payload):
        raise OSError('short output')
    stream.flush()


def diagnostic(stream, text):
    """Return delivery success; a failed diagnostic is an operation failure."""
    try:
        deliver(stream, text)
        return True
    except (OSError, ValueError):
        return False


def main(argv=None, source=None, output=None, errors=None):
    """Inject streams for delivery tests; defaults are process stdio only."""
    argv = sys.argv[1:] if argv is None else argv
    source = sys.stdin.buffer if source is None else source
    output = sys.stdout.buffer if output is None else output
    errors = sys.stderr if errors is None else errors
    if argv == ['--help']:
        try:
            deliver(output, HELP)
            return 0
        except (OSError, ValueError):
            diagnostic(errors, 'Output delivery failed.\n')
            return 3
    if argv:
        delivered = diagnostic(errors, 'Usage: python cli.py < synthetic.json\n')
        return 2 if delivered else 3
    try:
        raw = source.read(MAX_INPUT + 1)
        try:
            report = interpret(decode(raw))
        except Invalid as error:
            report = failure(error.code, error.pointer)
        payload = serialize(report)
        deliver(output, payload)
        return 0 if report['status'] == 'interpreted' else 2
    except (OSError, ValueError):
        diagnostic(errors, 'Input or output operation failed.\n')
        return 3


if __name__ == '__main__':
    exit_code = main()
    if exit_code == 3:
        # Failed buffered stdout/stderr must not flush again on interpreter exit.
        # No replacement file/device is opened; stdio delivery already failed.
        sys.stdout = None
        sys.stderr = None
    raise SystemExit(exit_code)
