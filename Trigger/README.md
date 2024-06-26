## Triggering a Full Run

```
export HOST=https://molokai.pbsci.ucsc.edu:3000
python3 tools/trigger.py \
    --data ../../TestData/Dom01.zip \
    --key Dom01 \
    --project NBS_ADAPTS \
    --template WaterDepth_\${clim}_\${scen}_Tr{rp}_t33 \
    --rps 10,25,50,100
```

The template controls the unique scenario combinations that will run AEV.  Note that `\${clim}` and `\${scen}` have a backslash and dollar sign.  To insert variables, use this format.  Leave `{rp}` as is, this is used to insert the `rps`.