import os
import logging
import flask
from flask import Flask, request, jsonify
import xarray as xr
import rioxarray as rxr
import io
import zipfile
import csv

from utils.dataset import makeSafe_rio, raster_stats

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)




@app.route('/raster_stats/', methods=["POST"])
def api_raster_stats():
    uploaded_file = request.files['data']
    print(request.form)

    thresh = float(request.form['threshold'])
    print(thresh)
    groupings = request.form['groupings']
    print(groupings )

    groupings = [
        j for j in 
        [
            i.split(',') for i in 
            request.form['groupings'].split(';')
        ]
    ]

    print(groupings)

    if not uploaded_file.filename.endswith('.zip'):
        return jsonify({'error': 'Uploaded file is not a ZIP archive'}), 400
    zip_data = io.BytesIO(uploaded_file.read())
    
    try:
        # Open the ZIP archive
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            # Extract all files to a temporary directory
            tmpdir = '/tmp/extracted_files'
            zip_ref.extractall(tmpdir)
            dirname = uploaded_file.filename.split('/')[-1].split('.')[0]
            zipdir = os.path.join(tmpdir, dirname)
            allfiles = os.listdir(zipdir)
            data = [file for file in allfiles if file.endswith('.tif')]
            results = []
            for d in data:
                flooding = rxr.open_rasterio(os.path.join(zipdir, d)).isel(band=0)
                k = []
                print(d)
                for l0 in groupings:
                    for l1 in l0:
                        if f"_{l1}_" in d:
                            if l1 == "structural_125" and "structural_125_w5" in d:
                                continue
                            else:
                                k += [l1]
                print(k)
                stat = raster_stats(flooding)
                results.append(k + [stat])

        with open(f'/tmp/{dirname}.csv', 'w') as f:
            csvwriter = csv.writer(f)
            csvwriter.writerows(results)
        
        return flask.send_from_directory('/tmp', f"{dirname}.csv")
            

    except zipfile.BadZipFile:
        return jsonify({'error': 'Invalid ZIP archive'}), 400
    
    return jsonify({'message': 'ZIP archive extracted successfully'}), 200
    flooding = rxr.open_rasterio(
        io.BytesIO(request.files['flooding'].read())
    ).isel(band=0)
    x = makeSafe_rio(flooding)
    if 'window_size' in request.form:
        return damage_assessment(
            x, 
            float(request.form['window_size']),
            float(request.form['population_min'])
        )
    return damage_assessment(x)


@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
