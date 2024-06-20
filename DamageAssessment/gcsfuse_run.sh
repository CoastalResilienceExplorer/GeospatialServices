#!/usr/bin/env bash
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# [START cloudrun_fuse_script]
#!/usr/bin/env bash
set -eo pipefail

echo "Mounting GCS Fuse."
for bucket in $(echo $MNT_BUCKETS | tr ";" "\n")
do
    echo ["$bucket"]
    mkdir -p $GCS_MNT_BASE/$bucket
    # gcsfuse --implicit-dirs --debug_gcs --debug_fuse $bucket $MNT_BASE/$bucket
    gcsfuse --implicit-dirs $bucket $GCS_MNT_BASE/$bucket
done

echo "Mounting completed."

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
exec python3 app.py
# [END cloudrun_fuse_script]

# exec  gunicorn app:app --bind 0.0.0.0:8080 --workers 40 --max-requests 3 --max-requests-jitter 3 --timeout 3600