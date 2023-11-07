echo Running with $@
for f in /data/*.csv; do
  echo "Running: $f"
  python3 mesh2tiff.py $f $@
done
