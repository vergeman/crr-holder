# CRR holdings explorer development

Prerequisite: ports 8000 and 5173 must be available.

1. Install Docker with Docker Compose and start Docker.
2. Clone this repository and open Bash in the repository root.
3. Prepare the database (skip if `db/crr/crr.sqlite` already exists):

   The database build step is defined in [db/crr/Dockerfile](db/crr/Dockerfile),
   which runs `prepare_dataset.py` to create `crr.sqlite`.

   ```sh
   docker build -t crr-dataset db/crr
   docker run --rm --user "$(id -u):$(id -g)" \
     --mount type=bind,src="$(pwd)/data",dst=/data,readonly \
     --mount type=bind,src="$(pwd)/db/crr",dst=/output \
     crr-dataset --data-dir /data --output /output/crr.sqlite
   ```

4. Build and start the app:

   ```sh
   docker compose ps
   docker compose build
   docker compose up --remove-orphans
   ```

5. Wait for Vite to report ready, then open http://localhost:5173.
6. Stop with Ctrl+C, then remove the containers:

   ```sh
   docker compose down
   ```
