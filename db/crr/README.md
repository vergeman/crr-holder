# Prepare the dataset

Local commands with the pinned requirements installed:

```sh
python3 db/crr/prepare_dataset.py
python3 -m unittest discover -s db/crr/tests -v
```

## Final step: build and run prepare_dataset

From the repository root:

```sh
docker build -t crr-dataset db/crr
docker run --rm --user "$(id -u):$(id -g)" \
  --mount type=bind,src="$(pwd)/data",dst=/data,readonly \
  --mount type=bind,src="$(pwd)/db/crr",dst=/output \
  crr-dataset --data-dir /data --output /output/crr.sqlite
```

This runs `prepare_dataset.py`: reads the four inputs, streams contracts from the
ZIP, loads account and settlement-point enrichment, and calculates monthly MW/MWh.
It also materializes `crr_summary_holdings` at report/account/source/sink/hedge
grain, summing MWh across months for summary queries. Monthly matrices and
individual contract queries retain their existing inputs.
It compares raw counts, required TOU coverage, and monthly totals by report,
hedge type, month, and TOU, with tolerance `1e-6 + 1e-10 * abs(expected)`.
Summary path totals are compared with their monthly input using the same tolerance.
On success, it replaces `db/crr/crr.sqlite` and prints counts, including missing
account enrichment and coordinates.
Before publishing, it runs `ANALYZE` to persist optimizer statistics in the database.
