# ERCOT CRR Holder  - Domain Question

This project attempts to provide an exploratory interface to following questions:

* Who / what entities participate in ERCOT CRR auctions.
* Where and what term are their hedges, and in what size?
* Do their profiles suggest certain operations (hedging, speculation)
* And are there different optimizations to access it across different
  representations [baseline API, sqlite in browser, sqlite vfs]

# Design Docs

Design and planning document.

* [data.md](./data.md): shape of data, what is available, fetch, persistence model.
* [web.md](./web.md): how data affects UI and what we see
* [api.md](./api.md): endpoint stuff

# Plan

* see `docs/plan/`

# Engineering Question

* What is sqlite in-browser like?

* ...actually what is sqlite-vfs like? If we control build ingestion of docs, can
  pages be optimized? Hasn't bandwidth become a dominant cost now? I guess this
  is the experiment.

* For these constant re-queries, does it offer a noticeable performance /
  bandwidth improvement vs an api?
  * Offload DB to Cloudflare S3 cheaper hosting than API Request
  * D1?

* The "business" question being are there large scale data consumers who would
  benefit from a prepared "view", dashboard?
  * Are there many smaller infrequent consumers where a range request could work?

* log front end bandwidth and query latency for both architectures
