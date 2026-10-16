"""Manually benchmark services on the real database; normal tests never run this.

Load fixed request inputs from JSON, reuse them across steps, and save each
workload's final response, three timing samples, and median under OUTPUT_DIR.

Every invocation runs fresh measurements. --label names the output subdirectory
(default: baseline); use --label task-3 for a later optimization. Reusing a label
overwrites outputs for the workloads selected in that run.
"""

import argparse
import json
import logging
import os
from pathlib import Path
import re
import statistics
import sys

# Timing must be enabled before importing decorated services.
os.environ['ENABLED_TIMED'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import open_database
from services.crr_holdings import get_contract_holdings, get_sink_holdings, get_source_holdings
from services.metadata import get_metadata
from services.summary import get_summary


# CLI service names map to the same entry points called by the API routes.
SERVICES = {
    'metadata': get_metadata,
    'summary': get_summary,
    'sources': get_source_holdings,
    'sinks': get_sink_holdings,
    'contracts': get_contract_holdings,
}
# Fixed request inputs are versioned; large measured outputs stay outside Git.
INPUTS_FILE = Path(__file__).resolve().parent / 'fixtures/measurement_inputs.json'
OUTPUT_DIR = Path('/tmp/0013-query-performance')


class TimingCapture(logging.Handler):
    """Collect existing @timed log messages and their elapsed milliseconds."""

    def emit(self, record):
        message = record.getMessage()
        self.messages.append(message)
        self.elapsed.append(float(re.search(r'elapsed_ms=([\d.]+)', message)[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('services', nargs='*', metavar='service')
    parser.add_argument('--label', default='baseline')
    args = parser.parse_args()
    if set(args.services) - SERVICES.keys():
        parser.error('services must be: ' + ', '.join(SERVICES))
    # Save this run separately, e.g. baseline/ or task-3/.
    directory = OUTPUT_DIR / args.label
    directory.mkdir(parents=True, exist_ok=True)

    # Capture service execution times from the existing timing logger.
    handler = TimingCapture()
    logger = logging.getLogger('uvicorn.error')
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    with open_database() as db:
        # Keep the same publication, filters, and drill-down cell for every run.
        inputs = json.loads(INPUTS_FILE.read_text())

        # Four portfolio requests share the chosen report and identifiers.
        # "point" uses the chosen source as an inclusive source-or-sink filter.
        filters = {
            'market': {}, 'account': {'account_holder': inputs['account_holder']},
            'point': {'settlement_point': inputs['source']},
            'combined': {'account_holder': inputs['account_holder'],
                         'settlement_point': inputs['source']},
        }
        medians = {}  # Workload name -> median service execution time in ms.
        for service in args.services or SERVICES:
            for name, selected in filters.items():
                # Metadata dropdowns accept report/account filters only.
                if service == 'metadata' and name in ('point', 'combined'):
                    continue

                # Build the arguments for this service and portfolio request.
                parameters = dict(report_id=inputs['report_id'], **selected)
                # Sink drill-downs select a source; contracts select one cell.
                if service in ('sinks', 'contracts'):
                    parameters['source'] = inputs['source']
                if service == 'contracts':
                    parameters.update({k: inputs[k] for k in ('sink', 'month', 'hedge_type')})
                # Measure both the first and second source pages.
                pages = (0, 20) if service == 'sources' else (None,)
                for offset in pages:
                    if offset is not None:
                        parameters.update(limit=20, offset=offset)
                    key = f'{service}-{name}' + (f'-{offset}' if offset is not None else '')
                    function = SERVICES[service]

                    # Discard the warm-up timing, then collect three samples.
                    handler.messages, handler.elapsed = [], []
                    function(db, **parameters)
                    handler.messages, handler.elapsed = [], []
                    for _ in range(3):
                        response = function(db, **parameters)

                    # Retain the final complete response and all measured logs.
                    (directory / f'{key}.json').write_text(json.dumps(response) + '\n')
                    (directory / f'{key}.log').write_text('\n'.join(handler.messages) + '\n')
                    medians[key] = statistics.median(handler.elapsed)

        (directory / 'medians.json').write_text(json.dumps(medians, indent=2) + '\n')
        print(json.dumps({'inputs': inputs, 'medians_ms': medians}, indent=2))


if __name__ == '__main__':
    main()
