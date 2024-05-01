## Purpose
This service creates PMTiles from Geoparquet.  The tiles can then be consumed in web applications.

### Triggering builds
Trigger via API:

ie
```
ENDPOINT={{base_url}}/create_mbtiles/

POST_DATA={
    "bucket": "geopmaker-output-staging",
    "name": "vectors/cwon-teselas/RESULTS_TESELA_1996_reppts.parquet"
}
```

### Local Usage

Note that you'll also need to include ENV Variable for: `GS_SECRET_ACCESS_KEY` and `GS_ACCESS_KEY_ID`.  Those can be found at the relevant storage bucket console.

```
docker build -t gp2mb .
docker run -it -v $PWD:/app -v $HOME/.config/gcloud:/root/.config/gcloud --entrypoint bash -p 3000:8080 gp2mb
```

