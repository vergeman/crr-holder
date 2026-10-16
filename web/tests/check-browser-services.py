"""Catch differences between Python and generated JavaScript when queries change.

Also check browser provider interactions and collect fixed-sample timings.

Requires the running Compose services and an existing local Chromium CDP session.
Results and raw captures are written to /tmp/0017-browser-services/.
"""

import argparse
import json
import statistics
import subprocess
import time
import urllib.request
from pathlib import Path

import websocket


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path('/tmp/0017-browser-services')
METHODS = {
    'metadata': 'getMetadata', 'summary': 'getSummary',
    'sources': 'getSourceHoldings', 'sinks': 'getSinkHoldings',
    'contracts': 'getContractHoldings',
}

# Capture the existing fixture databases at their service boundaries. Expected
# responses still come from committed JSON, never from this Python execution.
FIXTURES = '''
import base64
import inspect
import json

import test_service_responses as fixtures

records = []
databases = {}
functions = {
    'metadata': 'get_metadata', 'summary': 'get_summary',
    'sources': 'get_source_holdings', 'sinks': 'get_sink_holdings',
    'contracts': 'get_contract_holdings',
}

def capture(service, function):
    def execute(db, *args, **kwargs):
        content = base64.b64encode(db.serialize()).decode()
        database = next(
            (key for key, value in databases.items() if value == content),
            str(len(databases)),
        )
        databases[database] = content
        bound = inspect.signature(function).bind(db, *args, **kwargs)
        parameters = dict(bound.arguments)
        del parameters['db']

        result = function(db, *args, **kwargs)
        records.append((service, database, parameters, result))
        return result
    return execute

for service, name in functions.items():
    setattr(fixtures, name, capture(service, getattr(fixtures, name)))
fixtures.test_contracts.get_contract_holdings = fixtures.get_contract_holdings
responses = fixtures.fixture_responses()
cases = []
for service, database, parameters, result in records:
    scenario = next(
        name for name, response in responses[service].items() if response is result
    )
    cases.append(dict(
        service=service, database=database, parameters=parameters, scenario=scenario,
    ))
print(json.dumps(dict(databases=databases, cases=cases)))
'''


class Browser:
    def __init__(self, cdp):
        pages = json.load(urllib.request.urlopen(cdp + '/json'))
        page = next(page for page in pages if page['type'] == 'page')
        self.socket = websocket.create_connection(
            page['webSocketDebuggerUrl'], origin=cdp, timeout=180,
        )
        self.next_id = 0
        self.events = []
        self.call('Page.enable')
        self.call('Network.enable')

    def call(self, method, parameters=None):
        self.next_id += 1
        request = self.next_id
        self.socket.send(json.dumps(dict(
            id=request, method=method, params=parameters or {},
        )))
        while True:
            response = json.loads(self.socket.recv())
            if response.get('id') == request:
                if 'error' in response:
                    raise RuntimeError(response['error'])
                return response.get('result', {})
            self.events.append(response)

    def evaluate(self, expression):
        response = self.call('Runtime.evaluate', dict(
            expression=expression, returnByValue=True, awaitPromise=True,
        ))
        if 'exceptionDetails' in response:
            raise RuntimeError(response['exceptionDetails'])
        return response['result'].get('value')

    def wait(self, expression):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if self.evaluate(expression):
                return
            time.sleep(.1)
        raise RuntimeError('Timed out: ' + expression)

    def navigate(self, url):
        self.call('Page.navigate', dict(url=url))
        self.wait('document.readyState === "complete"')


def provider_parameters(parameters):
    names = {
        'report_id': 'reportId', 'account_holder': 'accountHolder',
        'settlement_point': 'settlementPoint', 'month': 'deliveryMonth',
        'hedge_type': 'hedgeType',
    }
    return {names.get(name, name): value for name, value in parameters.items()}


def check_fixtures(browser):
    result = subprocess.run(
        ['docker', 'compose', 'exec', '-T', '-e', 'PYTHONPATH=/app:/app/tests',
         'api', 'python', '-c', FIXTURES],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    payload = json.loads(result.stdout)
    for case in payload['cases']:
        baseline = ROOT / 'api/tests/fixtures/service_responses' / (case['service'] + '.json')
        case['expected'] = json.loads(baseline.read_text())[case['scenario']]
        case['method'] = METHODS[case['service']]
        case['parameters'] = provider_parameters(case['parameters'])

    browser.evaluate('''window.checkWorker = async (worker, message, transfer = []) => {
  const id = (window.requestId = (window.requestId ?? 0) + 1);
  return new Promise((resolve, reject) => {
    worker.onmessage = ({ data }) => {
      if (data.id === id)
        data.error ? reject(new Error(data.error)) : resolve(data);
    };
    worker.onerror = (event) => reject(new Error(event.message));
    worker.postMessage({ id, ...message }, transfer);
  });
};
''')
    # Each fixture uses the production worker and SQLite adapter.
    for database, content in payload['databases'].items():
        cases = [case for case in payload['cases'] if case['database'] == database]
        actual = browser.evaluate('''(async () => {
  const worker = new Worker(
    "/src/data/sqlite.worker.js?worker_file&type=module",
    { type: "module" }
  );
  try {
    const buffer = Uint8Array.from(atob(CONTENT), (c) =>
      c.charCodeAt(0)
    ).buffer;
    await checkWorker(worker, { backend: "wasm", buffer }, [buffer]);
    const results = [];
    for (const test of CASES)
      results.push((await checkWorker(worker, test)).result);
    return results;
  } finally {
    worker.terminate();
  }
})();
'''.replace('CONTENT', json.dumps(content)).replace('CASES', json.dumps(cases)))
        for case, response in zip(cases, actual):
            assert response == case['expected'], (
                f"Fixture mismatch: {case['service']}/{case['scenario']}"
            )
    print(f"Fixtures: {len(payload['cases'])} passed", flush=True)


def check_real_data(browser):
    inputs = json.loads((ROOT / 'web/src/components/benchmark/measurement_inputs.json').read_text())
    result = browser.evaluate('''(async () => {
  const inputs = INPUTS;
  const methods = METHODS;
  const canonical = (value) =>
    JSON.stringify(value, (_, item) =>
      item && typeof item === "object" && !Array.isArray(item)
        ? Object.fromEntries(
            Object.entries(item).sort(([a], [b]) => a.localeCompare(b))
          )
        : item
    );
  const difference = (actual, expected, path = "$") => {
    if (
      actual &&
      expected &&
      typeof actual === "object" &&
      typeof expected === "object"
    ) {
      for (const key of new Set([
        ...Object.keys(actual),
        ...Object.keys(expected),
      ])) {
        if (canonical(actual[key]) !== canonical(expected[key]))
          return difference(actual[key], expected[key], path + "." + key);
      }
    }
    return (
      path + ": " + JSON.stringify(actual) + " != " + JSON.stringify(expected)
    );
  };
  const equal = (actual, expected, name) => {
    if (canonical(actual) !== canonical(expected))
      throw new Error(
        "Response mismatch: " + name + " at " + difference(actual, expected)
      );
  };
  const worker = new Worker(
    "/src/data/sqlite.worker.js?worker_file&type=module",
    { type: "module" }
  );
  const started = performance.now();
  const buffer = await (await fetch("/api/database")).arrayBuffer();
  const download = {
    bytes: buffer.byteLength,
    downloadMs: performance.now() - started,
  };
  const initialized = await checkWorker(worker, { backend: "wasm", buffer }, [
    buffer,
  ]);
  const workloads = {};
  try {
    const filters = {
      market: {},
      account: { accountHolder: inputs.account_holder },
      point: { settlementPoint: inputs.source },
      combined: {
        accountHolder: inputs.account_holder,
        settlementPoint: inputs.source,
      },
    };
    for (const [service, method] of Object.entries(methods)) {
      for (const [name, filter] of Object.entries(filters)) {
        if (service === "metadata" && ["point", "combined"].includes(name))
          continue;
        for (const offset of service === "sources" ? [0, 20] : [null]) {
          const parameters = { reportId: inputs.report_id, ...filter };
          if (["sinks", "contracts"].includes(service))
            parameters.source = inputs.source;
          if (service === "contracts")
            Object.assign(parameters, {
              sink: inputs.sink,
              deliveryMonth: inputs.month,
              hedgeType: inputs.hedge_type,
            });
          if (offset !== null) Object.assign(parameters, { offset, limit: 20 });
          const query = new URLSearchParams({ report_id: inputs.report_id });
          if (parameters.accountHolder)
            query.set("account_holder", parameters.accountHolder);
          if (parameters.settlementPoint)
            query.set("settlement_point", parameters.settlementPoint);
          if (offset !== null) {
            query.set("offset", offset);
            query.set("limit", 20);
          }
          if (service === "contracts") {
            query.set("source", parameters.source);
            query.set("sink", parameters.sink);
            query.set("month", parameters.deliveryMonth);
            query.set("hedge_type", parameters.hedgeType);
          }
          const path =
            service === "sources"
              ? "/api/holdings/sources"
              : service === "sinks"
                ? "/api/holdings/sources/" +
                  encodeURIComponent(inputs.source) +
                  "/sinks"
                : service === "contracts"
                  ? "/api/holdings/contracts"
                  : "/api/" + service;
          const response = await fetch(path + "?" + query);
          if (!response.ok)
            throw new Error("HTTP failed: " + path + " " + response.status);
          const expected = await response.json();
          const key =
            service + "-" + name + (offset !== null ? "-" + offset : "");
          equal(
            (await checkWorker(worker, { method, parameters })).result,
            expected,
            key
          );
          const samples = [];
          for (let sample = 0; sample < 3; sample++) {
            const before = performance.now();
            const actual = await checkWorker(worker, { method, parameters });
            const roundTripMs = performance.now() - before;
            equal(actual.result, expected, key);
            samples.push({ ...actual.timings, roundTripMs });
          }
          workloads[key] = samples;
        }
      }
    }
    // Omitted report and empty filters must retain default selection semantics.
    for (const [service, method] of Object.entries(methods)) {
      const parameters = { accountHolder: "", settlementPoint: "" };
      if (["sinks", "contracts"].includes(service))
        parameters.source = inputs.source;
      if (service === "contracts")
        Object.assign(parameters, {
          sink: inputs.sink,
          deliveryMonth: inputs.month,
          hedgeType: inputs.hedge_type,
        });
      const explicit = { ...parameters, reportId: inputs.report_id };
      equal(
        (await checkWorker(worker, { method, parameters })).result,
        (await checkWorker(worker, { method, parameters: explicit })).result,
        service + " defaults"
      );
    }
  } finally {
    worker.terminate();
  }

  return { download, initialization: initialized.timings, workloads };
})();
'''.replace('INPUTS', json.dumps(inputs)).replace('METHODS', json.dumps(METHODS)))
    (OUTPUT / 'measurements.json').write_text(json.dumps(result, indent=2) + '\n')
    medians = {name: statistics.median(sample['roundTripMs'] for sample in samples)
               for name, samples in result['workloads'].items()}
    print(f"Real-data comparisons: {len(medians)} workloads passed; defaults passed", flush=True)
    print(json.dumps(dict(download=result['download'], initialization=result['initialization'],
                         medians_ms=medians), indent=2), flush=True)


def check_vfs(browser):
    inputs = json.loads((ROOT / 'web/src/components/benchmark/measurement_inputs.json').read_text())
    result = browser.evaluate('''(async () => {
  const inputs = INPUTS;
  const equal = (actual, expected, name) => {
    if (JSON.stringify(actual) !== JSON.stringify(expected))
      throw new Error(name + " mismatch");
  };
  // An indexed contract query avoids VFS's known market-wide startup scan.
  const vfs = new Worker("/src/data/sqlite.worker.js?worker_file&type=module", {
    type: "module",
  });
  let vfsResult;
  try {
    await checkWorker(vfs, { backend: "vfs" });
    const parameters = {
      reportId: inputs.report_id,
      accountHolder: inputs.account_holder,
      source: inputs.source,
      sink: inputs.sink,
      deliveryMonth: inputs.month,
      hedgeType: inputs.hedge_type,
    };
    const query = new URLSearchParams({
      report_id: inputs.report_id,
      account_holder: inputs.account_holder,
      source: inputs.source,
      sink: inputs.sink,
      month: inputs.month,
      hedge_type: inputs.hedge_type,
    });
    const expected = await (
      await fetch("/api/holdings/contracts?" + query)
    ).json();
    const before = performance.now();
    const actual = await checkWorker(vfs, {
      method: "getContractHoldings",
      parameters,
    });
    equal(actual.result, expected, "VFS indexed contracts");
    vfsResult = { ...actual.timings, roundTripMs: performance.now() - before };
  } finally {
    vfs.terminate();
  }
  return vfsResult;
})();
'''.replace('INPUTS',json.dumps(inputs)))
    (OUTPUT / 'vfs.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Indexed generated VFS query: passed', result, flush=True)


def check_interactions(browser, web):
    start = len(browser.events)
    browser.navigate(web + '/?provider=wasm')
    ready = "document.querySelector('.portfolio-overview')?.getAttribute('aria-busy')==='false' && document.querySelectorAll('.source-row').length===20"
    browser.wait(ready)
    for width, height in ((1440, 1000), (390, 844)):
        browser.call('Emulation.setDeviceMetricsOverride', dict(width=width, height=height, deviceScaleFactor=1, mobile=False))
        assert browser.evaluate("""(() => {
          const select=[...document.querySelectorAll('header select')].find(select=>
            [...select.options].some(option=>option.value==='wasm'));
          const bounds=select.getBoundingClientRect();
          return bounds.left>=0 && bounds.right<=innerWidth && bounds.top>=0 && bounds.bottom<=innerHeight;
        })()""")
        browser.evaluate("""(() => {
          const select=document.querySelectorAll('.portfolio-filter-controls select')[0];
          select.value='XNRGLD';select.dispatchEvent(new Event('change',{bubbles:true}));
        })()""")
        browser.wait("document.querySelector('.portfolio-overview')?.getAttribute('aria-busy')==='false' && document.querySelectorAll('.source-row').length===4")
        browser.evaluate("document.querySelector('.source-expand').click()")
        browser.wait("document.querySelectorAll('.sink-row').length>0")
        browser.evaluate("[...document.querySelectorAll('.contract-cell')].find(button=>Number(button.textContent.replaceAll(',',''))>0).click()")
        browser.wait("document.querySelector('dialog[open] .contract-holder')!==null")
        browser.evaluate("document.querySelector('.contract-holder').open=true;document.querySelector('.contract-tou').open=true")
        assert browser.evaluate("document.querySelectorAll('[role=alert]').length===0")
        assert browser.evaluate("""(() => {
          const bounds=document.querySelector('[aria-label="Close contract details"]').getBoundingClientRect();
          return bounds.left>=0 && bounds.right<=innerWidth && bounds.top>=0 && bounds.bottom<=innerHeight;
        })()""")
        browser.evaluate("document.querySelector('[aria-label=\"Close contract details\"]').click()")
        browser.wait("!document.querySelector('dialog[open]')")
        browser.evaluate("document.querySelector('.source-expand[aria-expanded=true]').click();document.querySelector('.portfolio-filter-controls button').click()")
        browser.wait(ready)

    requests = [event['params']['request']['url'] for event in browser.events[start:]
                if event.get('method') == 'Network.requestWillBeSent']
    assert not any('/api/holdings/' in url or '/api/summary?' in url or '/api/metadata?' in url for url in requests), requests

    # Exercise every override through actual provider selection.
    start = len(browser.events)
    browser.navigate(web + '/?provider=http&metadata=wasm&summary=wasm&sources=wasm&sinks=wasm&contracts=wasm')
    browser.wait(ready)
    browser.evaluate('''(async () => {
  const { dataProvider } = await import("/src/data/provider.js");
  const controller = new AbortController();
  const pending = dataProvider.getSourceHoldings(
    { reportId: 1 },
    controller.signal
  );
  await Promise.resolve();
  controller.abort();
  try {
    await pending;
    throw new Error("Request was not cancelled");
  } catch (error) {
    if (error.name !== "AbortError") throw error;
  }
  const result = await dataProvider.getSourceHoldings({ reportId: 1 });
  if (result.sources.length !== 20)
    throw new Error("Provider did not recover after cancellation");
  const parameters = {
    reportId: 1,
    accountHolder: "XNRGLD",
    source: "HB_NORTH",
    sink: "LZ_NORTH",
    deliveryMonth: "2027-06-01",
    hedgeType: "OBL",
  };
  await dataProvider.getSinkHoldings(parameters);
  await dataProvider.getContractHoldings(parameters);
})();
''')
    requests = [event['params']['request']['url'] for event in browser.events[start:]
                if event.get('method') == 'Network.requestWillBeSent']
    assert not any('/api/holdings/' in url or '/api/summary?' in url or '/api/metadata?' in url for url in requests), requests

    for provider in ('http', 'wasm'):
        browser.evaluate("""(() => {
          const select=[...document.querySelectorAll('select')].find(select=>[...select.options].some(option=>option.value==='wasm'));
          select.value=PROVIDER;select.dispatchEvent(new Event('change',{bubbles:true}));
        })()""".replace('PROVIDER', json.dumps(provider)))
        browser.wait("new URLSearchParams(location.search).get('provider')===" + json.dumps(provider))
        browser.wait(ready)
        assert browser.evaluate("[...new URLSearchParams(location.search).keys()].every(key=>key==='provider')")
    print('Desktop/narrow drill-downs, provider switching, overrides, and cancellation: passed', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cdp', default='http://localhost:9235')
    parser.add_argument('--web', default='http://localhost:5173')
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    browser = Browser(args.cdp)
    try:
        browser.navigate(args.web + '/?provider=http')
        check_fixtures(browser)
        check_real_data(browser)
        check_vfs(browser)
        check_interactions(browser, args.web)
    finally:
        (OUTPUT / 'events.json').write_text(json.dumps(browser.events))
        browser.socket.close()


if __name__ == '__main__':
    main()
