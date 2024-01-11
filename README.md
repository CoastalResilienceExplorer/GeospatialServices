## Services
This directory holds services relevant to working with the GlobalFloodExplorer.  To add new services, modify either `cloudbuild.yaml` or `deploy_all.sh`.

Currently, there isn't much need to have both `cloudbuild.yaml` and `deploy_all.sh`, since the YAML is simple.  However it's nice to keep it anyway, since it's often a little easier to manage deployments with bash commands instead of pure YAML.  

The gist of this root build should just kick off builds of the other services, not build anything of its own.

## Principles
This repository aims to be useful for working with geospatial data for analytics and visualization purposes in a cloud-native manner.  To this end, there are a few principles to follow as it continues to grow:

### Access Patterns
We aim to support 2-4 primary access patterns per service:
- API calls with an associated file input.  For example, supply a floodmap in a `curl` command and get back associated data
- API calls with a reference to a cloud-storage file.  This will often be a little simpler for chaining results
- Python interface on common functions.  Able to run locally, leveraging Docker.  May consider conda, but in general not a fan of its integrations with microservices-based cloud functionality, so more likely using pip and managing GDAL binaries ourselves.
- Drag-and-drop, cloud storage triggers, often useful for simple triggers.