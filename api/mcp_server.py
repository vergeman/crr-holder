from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from database import open_database
from mcp_usage import logged_tool
from models import (Metadata, Summary, SourceHoldings, SinkHoldings, ContractHoldings,
                    DeliveryMonth, HedgeType, SourceLimit, SourceOffset)
from services import crr_holdings, metadata, summary


mcp = MCPServer('CRR holdings')
read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)


# SDK 2.3.0 offloads synchronous tools with anyio.to_thread.run_sync.
@mcp.tool(annotations=read_only)
@logged_tool
def get_metadata(report_id: int | None = None,
                 account_holder: str | None = None) -> Metadata:
    """List reports, account holders, and settlement points for a portfolio."""
    with open_database() as db:
        return Metadata.model_validate(metadata.get_metadata(db, report_id, account_holder))


@mcp.tool(annotations=read_only)
@logged_tool
def get_summary(report_id: int | None = None, account_holder: str | None = None,
                settlement_point: str | None = None) -> Summary:
    """Summarize exposure, rankings, and geography for a portfolio."""
    with open_database() as db:
        return Summary.model_validate(summary.get_summary(
            db, report_id, account_holder, settlement_point))


@mcp.tool(annotations=read_only)
@logged_tool
def get_source_holdings(report_id: int | None = None,
                        account_holder: str | None = None,
                        settlement_point: str | None = None,
                        limit: SourceLimit = 20, offset: SourceOffset = 0) -> SourceHoldings:
    """Page through source holdings and monthly exposure; follow nextOffset."""
    with open_database() as db:
        return SourceHoldings.model_validate(crr_holdings.get_source_holdings(
            db, report_id, account_holder, settlement_point, limit, offset))


@mcp.tool(annotations=read_only)
@logged_tool
def get_sink_holdings(source: str, report_id: int | None = None,
                      account_holder: str | None = None,
                      settlement_point: str | None = None) -> SinkHoldings:
    """Expand a source into sink holdings and monthly exposure."""
    with open_database() as db:
        return SinkHoldings.model_validate(crr_holdings.get_sink_holdings(
            db, source, report_id, account_holder, settlement_point))


@mcp.tool(annotations=read_only)
@logged_tool
def get_contract_holdings(source: str, sink: str, month: DeliveryMonth,
                          hedge_type: HedgeType, report_id: int | None = None,
                          account_holder: str | None = None,
                          settlement_point: str | None = None) -> ContractHoldings:
    """Inspect contracts for a source, sink, delivery month, and hedge type."""
    with open_database() as db:
        return ContractHoldings.model_validate(crr_holdings.get_contract_holdings(
            db, source, sink, month, hedge_type, report_id, account_holder, settlement_point))
