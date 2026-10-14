# Prepare the dataset

From the repository root:

```sh
docker build -t crr-dataset db/crr
docker run --rm --user "$(id -u):$(id -g)" \
  --mount type=bind,src="$(pwd)/data",dst=/data,readonly \
  --mount type=bind,src="$(pwd)/db/crr",dst=/output \
  crr-dataset
```

Local commands with the pinned requirements installed:

```sh
python3 db/crr/prepare_dataset.py
python3 -m unittest discover -s db/crr/tests -v
```

Validation compares raw row counts, required TOU coverage, and monthly MW/MWh by
report, hedge type, month, and TOU. Tolerance: `1e-6 + 1e-10 * abs(expected)`.
