### Workflow
The code generates a Raster Stats CSV for a collection of inputs supplied as a ZIP.

### To Run From Server
See `tools/trigger.py`

### Building Locally
```
ENV=staging
IMAGE=us-west1-docker.pkg.dev/global-mangroves/rasterstats/rasterstats-${ENV}
docker build \
    --build-arg BASE_IMAGE=us-west1-docker.pkg.dev/global-mangroves/base/python_gis_base_${ENV} \
    -t $IMAGE .

docker run -it \
    -v $PWD:/app \
    -v $HOME/.config/gcloud/:/root/.config/gcloud \
    -p 3001:8080 \
    $IMAGE
```

After doing this, you can test with the same trigger script by attaching `--local` to the call.

### Triggering
```
python3 tools/trigger.py --data /Users/chlowrie/Downloads/deliverables_1_and_2_CSIR_damages/StJohn_results_corrected.zip --local --output StJohn.csv --threshold 0.1 --groupings "rp10,rp50,rp100,rp500;base,ecological,structural_125,structural_125_w5,NoReef,PostStorm"

python3 tools/trigger.py --data /Users/chlowrie/Downloads/deliverables_1_and_2_CSIR_damages/StCroix_results_corrected.zip --local --output StCroix.csv --threshold 0.1 --groupings "rp10,rp50,rp100,rp500;base,ecological,structural_125,structural_125_w5,NoReef,PostStorm"

python3 tools/trigger.py --data /Users/chlowrie/Downloads/deliverables_1_and_2_CSIR_damages/StThomas_results_corrected.zip --local --output StThomas.csv --threshold 0.1 --groupings "rp10,rp50,rp100,rp500;base,ecological,structural_125,structural_125_w5,NoReef,PostStorm"
```