#!/usr/bin/env bash
set -eo pipefail

export PATH=${PATH}:`go env GOPATH`/bin
# Create mount directory for service
mkdir -p $MNT_DIR

echo "Mounting GCS Fuse."
gcsfuse --implicit-dirs --debug_gcs --debug_fuse $BUCKET $MNT_DIR 
echo "Mounting completed."

# Start the application
exec mbtileserver --dir $MNT_DIR --port 8080 --host 0.0.0.0 --verbose

# Exit immediately when one of the background processes terminate.
wait -n
