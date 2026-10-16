export function createSuite(inputs) {
  const filters = {
    market: {},
    account: { accountHolder: inputs.account_holder },
    point: { settlementPoint: inputs.source },
    combined: {
      accountHolder: inputs.account_holder,
      settlementPoint: inputs.source,
    },
  };
  const workloads = [];
  for (const service of [
    "getMetadata",
    "getSummary",
    "getSourceHoldings",
    "getSinkHoldings",
    "getContractHoldings",
  ]) {
    for (const [filter, selected] of Object.entries(filters)) {
      if (service === "getMetadata" && ["point", "combined"].includes(filter))
        continue;
      for (const offset of service === "getSourceHoldings" ? [0, 20] : [null]) {
        const parameters = { reportId: inputs.report_id, ...selected };
        if (["getSinkHoldings", "getContractHoldings"].includes(service))
          parameters.source = inputs.source;
        if (service === "getContractHoldings")
          Object.assign(parameters, {
            sink: inputs.sink,
            deliveryMonth: inputs.month,
            hedgeType: inputs.hedge_type,
          });
        if (offset !== null) Object.assign(parameters, { offset, limit: 20 });
        workloads.push({
          id: `${service}-${filter}${offset === null ? "" : `-${offset}`}`,
          service,
          parameters,
        });
      }
    }
  }
  return workloads;
}
