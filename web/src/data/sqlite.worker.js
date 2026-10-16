import sqlite3InitModule from "@sqlite.org/sqlite-wasm";
import sqliteWasmUrl from "@sqlite.org/sqlite-wasm/sqlite3.wasm?url";

const statementNames = {
  source: [
    "resolve_report",
    "delivery_months",
    "source_portfolio_bounds",
    "source_portfolio_bounds_account",
    "source_portfolio_bounds_point",
    "ranked_sources",
    "ranked_sources_account",
    "ranked_sources_point",
    "ranked_sources_point_account",
    "source_month_cells",
    "source_month_cells_account",
    "ranked_sinks",
    "ranked_sinks_account",
    "sink_month_cells",
    "sink_month_cells_account",
    "contract_segments",
    "contract_segments_account",
  ],
  metadata: [
    "reports",
    "report_account_holders",
    "settlement_point_choices",
    "settlement_point_choices_account",
  ],
  summary: [
    "portfolio_metrics",
    "portfolio_metrics_account",
    "portfolio_metrics_point",
    "portfolio_metrics_point_account",
    "top_account_holders",
    "top_account_holders_account",
    "top_account_holders_point",
    "top_account_holders_point_account",
    "settlement_point_totals",
    "settlement_point_totals_account",
    "settlement_point_totals_point",
    "settlement_point_totals_point_account",
  ],
};
let database;

async function fetchResource(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok)
    throw new Error(`Request failed: ${response.status} (${url})`);
  return response;
}

async function initializeSQLite(backend) {
  if (backend === "vfs") {
    const { initSyncSQLite, createHttpBackend } =
      await import("sqlite-wasm-http");
    return initSyncSQLite({ http: createHttpBackend({ backendType: "sync" }) });
  }
  return sqlite3InitModule({ locateFile: () => sqliteWasmUrl });
}

async function loadDatabase(buffer, backend) {
  const started = performance.now();
  const [sqlite3, statements] = await Promise.all([
    initializeSQLite(backend),
    Promise.all(
      Object.entries(statementNames).flatMap(([service, names]) =>
        names.map(async (name) => [
          name,
          await (await fetchResource(`/api/${service}-sql/${name}`)).text(),
        ])
      )
    ),
  ]);
  const openStarted = performance.now();
  let db;
  if (backend === "vfs") {
    const url = new URL("/api/database", self.location.origin).href;
    db = new sqlite3.oo1.DB(`file:${encodeURI(url)}`, "r", "http");
  } else {
    const bytes = new Uint8Array(buffer);
    db = new sqlite3.oo1.DB();
    const pointer = sqlite3.wasm.allocFromTypedArray(bytes);
    const rc = sqlite3.capi.sqlite3_deserialize(
      db.pointer,
      "main",
      pointer,
      bytes.byteLength,
      bytes.byteLength,
      sqlite3.capi.SQLITE_DESERIALIZE_FREEONCLOSE |
        sqlite3.capi.SQLITE_DESERIALIZE_READONLY
    );
    if (rc) {
      sqlite3.wasm.dealloc(pointer);
      db.close();
      throw new Error(`SQLite database import failed: ${rc}`);
    }
  }
  db.exec("PRAGMA query_only = ON");
  console.info("SQLite WASM database ready", {
    backend,
    sqliteVersion: sqlite3.version.libVersion,
    openMs: performance.now() - openStarted,
    totalMs: performance.now() - started,
  });
  return { db, statements: Object.fromEntries(statements) };
}

function query(db, sql, parameters = {}) {
  const statement = db.prepare(sql);
  try {
    // Variants use different subsets of the shared bound values.
    for (const [name, value] of Object.entries(parameters)) {
      if (statement.getParamIndex(`:${name}`))
        statement.bind(`:${name}`, value);
    }
    const rows = [];
    while (statement.step()) rows.push(statement.get([]));
    return rows;
  } finally {
    statement.finalize();
  }
}

function selectStatement(statements, name, accountHolder) {
  return statements[accountHolder ? `${name}_account` : name];
}

function sourceHoldings(
  { db, statements },
  { reportId, accountHolder, settlementPoint, offset = 0 }
) {
  reportId ??= query(db, statements.resolve_report)[0][0];
  const parameters = {
    report_id: reportId,
    account_holder: accountHolder || null,
    settlement_point: settlementPoint || null,
    limit: 21,
    offset,
  };
  const months = query(db, statements.delivery_months, parameters).map(
    ([month]) => month
  );
  const boundsStatement =
    settlementPoint && !accountHolder
      ? "source_portfolio_bounds_point"
      : "source_portfolio_bounds";
  const [firstMonth, lastMonth] = query(
    db,
    selectStatement(statements, boundsStatement, accountHolder),
    parameters
  )[0];
  const rankingStatement = settlementPoint
    ? "ranked_sources_point"
    : "ranked_sources";
  const rankedSources = query(
    db,
    selectStatement(statements, rankingStatement, accountHolder),
    parameters
  );
  const sources = rankedSources
    .slice(0, 20)
    .map(([source, totalOptMwh, totalOblMwh]) => ({
      source,
      totalOptMwh,
      totalOblMwh,
      months: months.map((deliveryMonth) => ({
        deliveryMonth,
        OPT: 0,
        OBL: 0,
      })),
    }));

  if (sources.length) {
    const cells = new Map(
      sources.map((source) => [
        source.source,
        new Map(source.months.map((month) => [month.deliveryMonth, month])),
      ])
    );
    parameters.sources = JSON.stringify(sources.map(({ source }) => source));
    for (const [source, month, hedgeType, mwh] of query(
      db,
      selectStatement(statements, "source_month_cells", accountHolder),
      parameters
    )) {
      cells.get(source).get(month)[hedgeType] = mwh;
    }
  }

  return {
    reportId,
    deliveryMonths: months,
    holdingsRange: firstMonth ? { firstMonth, lastMonth } : null,
    sources,
    nextOffset: rankedSources.length > 20 ? offset + 20 : null,
  };
}

function metadata({ db, statements }, { reportId, accountHolder }) {
  reportId ??= query(db, statements.resolve_report)[0][0];
  const parameters = {
    report_id: reportId,
    account_holder: accountHolder || null,
  };
  return {
    reportId,
    reports: query(db, statements.reports).map(
      ([reportId, publicationDate]) => ({ reportId, publicationDate })
    ),
    accountHolders: query(
      db,
      statements.report_account_holders,
      parameters
    ).map(([accountHolder, legalName]) => ({ accountHolder, legalName })),
    settlementPoints: query(
      db,
      selectStatement(statements, "settlement_point_choices", accountHolder),
      parameters
    ).map(([point]) => point),
  };
}

function summary(
  { db, statements },
  { reportId, accountHolder, settlementPoint }
) {
  reportId ??= query(db, statements.resolve_report)[0][0];
  const parameters = {
    report_id: reportId,
    account_holder: accountHolder || null,
    settlement_point: settlementPoint || null,
  };
  const metricsStatement = settlementPoint
    ? "portfolio_metrics_point"
    : "portfolio_metrics";
  const [totalMwh, accountHolderCount, directedPathCount, OPT, OBL] = query(
    db,
    selectStatement(statements, metricsStatement, accountHolder),
    parameters
  )[0];
  const pointStatement = settlementPoint
    ? "settlement_point_totals_point"
    : "settlement_point_totals";
  const points = query(
    db,
    selectStatement(statements, pointStatement, accountHolder),
    parameters
  );
  const geographicFootprint = points.map(
    ([settlementPoint, longitude, latitude, sourceMwh, sinkMwh]) => ({
      settlementPoint,
      longitude,
      latitude,
      sourceMwh,
      sinkMwh,
    })
  );

  // Match Python's numeric ranking and identifier ordering for ties.
  const rankedPoints = [...points].sort(
    (a, b) => b[5] - a[5] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0)
  );
  const topSettlementPoints = rankedPoints
    .slice(0, 100)
    .map(([settlementPoint, , , , , totalMwh]) => ({
      settlementPoint,
      totalMwh,
    }));
  const accountStatement = settlementPoint
    ? "top_account_holders_point"
    : "top_account_holders";
  const topAccountHolders = query(
    db,
    selectStatement(statements, accountStatement, accountHolder),
    parameters
  ).map(([accountHolder, legalName, totalMwh]) => ({
    accountHolder,
    legalName,
    totalMwh,
  }));
  return {
    reportId,
    totalMwh,
    geographicFootprint,
    accountHolderCount,
    settlementPointCount: geographicFootprint.length,
    directedPathCount,
    hedgeTypeMwh: { OPT, OBL },
    topAccountHolders,
    topSettlementPoints,
  };
}

function sinkHoldings(
  { db, statements },
  { reportId, accountHolder, settlementPoint, source }
) {
  reportId ??= query(db, statements.resolve_report)[0][0];
  const parameters = {
    report_id: reportId,
    account_holder: accountHolder || null,
    settlement_point: settlementPoint || null,
    source,
  };
  const deliveryMonths = query(db, statements.delivery_months, parameters).map(
    ([month]) => month
  );
  const sinks = query(
    db,
    selectStatement(statements, "ranked_sinks", accountHolder),
    parameters
  ).map(([sink, totalOptMwh, totalOblMwh]) => ({
    sink,
    totalOptMwh,
    totalOblMwh,
    months: deliveryMonths.map((deliveryMonth) => ({
      deliveryMonth,
      OPT: 0,
      OBL: 0,
    })),
  }));
  const cells = new Map(
    sinks.map(({ sink, months }) => [
      sink,
      new Map(months.map((month) => [month.deliveryMonth, month])),
    ])
  );
  for (const [sink, month, hedgeType, mwh] of query(
    db,
    selectStatement(statements, "sink_month_cells", accountHolder),
    parameters
  )) {
    cells.get(sink).get(month)[hedgeType] = mwh;
  }
  return { reportId, source, deliveryMonths, sinks };
}

function contractHoldings(
  { db, statements },
  {
    reportId,
    accountHolder,
    settlementPoint,
    source,
    sink,
    deliveryMonth,
    hedgeType,
  }
) {
  reportId ??= query(db, statements.resolve_report)[0][0];
  const parameters = {
    report_id: reportId,
    account_holder: accountHolder || null,
    settlement_point: settlementPoint || null,
    source,
    sink,
    month: deliveryMonth,
    hedge_type: hedgeType,
  };
  const holders = new Map();
  for (const [
    holder,
    legalName,
    timeOfUse,
    crrId,
    segmentId,
    crrType,
    startDate,
    endDate,
    mw,
    hours,
    monthMwh,
  ] of query(
    db,
    selectStatement(statements, "contract_segments", accountHolder),
    parameters
  )) {
    if (!holders.has(holder)) {
      holders.set(holder, {
        accountHolder: holder,
        legalName,
        totalMwh: 0,
        timeOfUseGroups: new Map(),
      });
    }
    const account = holders.get(holder);
    if (!account.timeOfUseGroups.has(timeOfUse)) {
      account.timeOfUseGroups.set(timeOfUse, {
        timeOfUse,
        hours,
        totalMwh: 0,
        contracts: [],
      });
    }
    const group = account.timeOfUseGroups.get(timeOfUse);
    group.contracts.push({
      crrId,
      segmentId,
      crrType,
      startDate,
      endDate,
      mw,
      monthMwh,
    });
    group.totalMwh += monthMwh;
    account.totalMwh += monthMwh;
  }

  // Preserve Python's time-of-use order and account ranking, including ties.
  const accountHolders = [...holders.values()].map((account) => ({
    ...account,
    timeOfUseGroups: ["PeakWD", "PeakWE", "Off-peak"]
      .filter((timeOfUse) => account.timeOfUseGroups.has(timeOfUse))
      .map((timeOfUse) => account.timeOfUseGroups.get(timeOfUse)),
  }));
  accountHolders.sort(
    (a, b) =>
      b.totalMwh - a.totalMwh ||
      (a.accountHolder < b.accountHolder
        ? -1
        : a.accountHolder > b.accountHolder
          ? 1
          : 0)
  );

  // Match Python 3.12 sum() compensation for the contract grand total.
  let total = 0;
  let correction = 0;
  for (const { totalMwh: value } of accountHolders) {
    const next = total + value;
    correction +=
      Math.abs(total) >= Math.abs(value)
        ? total - next + value
        : value - next + total;
    total = next;
  }
  const totalMwh = total + correction;
  return {
    reportId,
    source,
    sink,
    deliveryMonth,
    hedgeType,
    totalMwh,
    accountHolders,
  };
}

const methods = {
  getSourceHoldings: sourceHoldings,
  getMetadata: metadata,
  getSummary: summary,
  getSinkHoldings: sinkHoldings,
  getContractHoldings: contractHoldings,
};

self.onmessage = async ({
  data: { id, buffer, backend, method, parameters },
}) => {
  try {
    if (backend) {
      database = await loadDatabase(buffer, backend);
      self.postMessage({ id });
      return;
    }
    const started = performance.now();
    const result = methods[method](database, parameters);
    console.info("SQLite WASM query", {
      method,
      ...parameters,
      elapsedMs: performance.now() - started,
    });
    self.postMessage({ id, result });
  } catch (error) {
    self.postMessage({ id, error: error.message });
  }
};
