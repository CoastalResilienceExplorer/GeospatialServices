
set -e; \
    apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    tini && \
    gcsFuseRepo=gcsfuse-`lsb_release -c -s` && \
    gcsFuseRepo=gcsfuse-bionic && \
    echo "deb https://packages.cloud.google.com/apt $gcsFuseRepo main" | \
    tee /etc/apt/sources.list.d/gcsfuse.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key add - && \
    apt-get update && \
    apt-get install -y gcsfuse && \
    apt-get clean