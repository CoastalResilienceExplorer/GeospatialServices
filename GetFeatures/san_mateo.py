@app.route("/san_mateo/", methods=["POST"])
@timeit
def san_mateo():
    """Handle tile requests."""
    logging.info(request.get_json())
    logging.info(type(request.get_json()))
    data = request.get_json()
    rasters = data["rasters"]
    rps = data["rps"]

    ### Get All Buildings from the Last Raster
    # This should be the largest extent
    last_raster = xr.open_dataarray(os.path.join(os.environ["MNT_BASE"], rasters[-1]))
    b = last_raster.rio.bounds()
    lower_left = transform_point(b[0], b[1], last_raster.rio.crs)
    upper_right = transform_point(b[2], b[3], last_raster.rio.crs)
    all_buildings = (
        get_bbox_filtered_gdf(
            os.path.join(os.environ["MNT_BASE"], data["features_file"]),
            lower_left,
            upper_right,
        )
        .set_crs("EPSG:4326")
        .to_crs(last_raster.rio.crs)
        .reset_index()
        .rename(columns={"index": "building_fid"})
    )
    all_buildings_polygons = copy.deepcopy(all_buildings)
    all_buildings.geometry = all_buildings.geometry.centroid
    all_buildings.sindex

    ## BCDC
    bgs = gpd.read_file("data/BCDC.gpkg").to_crs(
        last_raster.rio.crs
    )
    bcdc_buildings = gpd.sjoin(all_buildings, bgs, how="inner")
    bcdc_buildings = bcdc_buildings[list(all_buildings.columns) + ["GEOID"]]
    print(bcdc_buildings)

    ### Loop over all rasters
    all_damages = []
    damage_columns = []
    xid = str(uuid.uuid1())
    output_dir = f"/tmp/{xid}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for raster in rasters:
        id = raster.split("/")[-1].split(".")[0]
        raster = xr.open_dataarray(os.path.join(os.environ["MNT_BASE"], raster))
        print('calculating extent...')
        extent = xr_vectorize(raster, coarsen_by=50)
        extent.to_file(os.path.join(output_dir, f"extent_{id}.gpkg"), driver="GPKG")

        ###
        # Get Flood Depths by Building
        ###  
        features = copy.deepcopy(bcdc_buildings)
        print("extracting values at points...")
        extracted = extract_points(raster, features, column_name=id)
        extracted = extracted.drop(columns=[i for i in extracted.columns if i[0:5] == "index"])
        extracted = extracted[extracted[id] > 0]

        # Flooded Totals BCDC
        print("applying DDFs...")
        damages, col = apply_ddf(extracted, id)
        all_damages.append(damages[["building_fid", col]].set_index("building_fid"))
        damage_columns.append(col)

    all_damages = recursive_merge(*all_damages).fillna(0)
    all_damages["AED"] = all_damages.apply(
        lambda row: calculate_AEV(
            rps,
            [row[col] for col in damage_columns], 
        ),
        axis=1, 
    )
    # Combine Damages
    print('writing buildings file...')
    bcdc_buildings = pd.merge(bcdc_buildings, all_damages, on="building_fid", how="left").fillna(0)
    bcdc_buildings.to_file(os.path.join(output_dir, "building_damages.gpkg"), driver="GPKG")

    # # Get Blockgroup-Level Damage Statistics
    print('creating blockgroup summary statistics...')
    total_count_buildings = bcdc_buildings.groupby('GEOID').count().geometry.rename('total_buildings')
    total_damage = bcdc_buildings[['GEOID', 'AED']].groupby('GEOID').sum()['AED'].rename('total_damage')
    buildings_flooded_buff = []
    bldg_cnt_col_buff = []
    for dc in damage_columns:
        count_col = dc.replace('total_damage_', 'count_flooded_')
        buildings_flooded_buff.append(bcdc_buildings[bcdc_buildings[dc] > 0].groupby('GEOID').count().geometry.rename(count_col))
        bldg_cnt_col_buff.append(count_col)
    buildings_flooded = recursive_merge(*buildings_flooded_buff)
    buildings_flooded['Annual_Exp_Cnt_Bldgs_Flooded'] = buildings_flooded.apply(
        lambda row: calculate_AEV(
            rps,
            [row[col] for col in bldg_cnt_col_buff], 
        ),
        axis=1, 
    )
    # flooded_count_buildings = bcdc_buildings[bcdc_buildings["AED"] > 0].groupby('GEOID').count().geometry.rename('flooded_buildings')
    output = recursive_merge(total_count_buildings, total_damage, buildings_flooded)
    output = pd.merge(bgs, output, left_on="GEOID", right_index=True)
    output['annual_exp_percent_flooded'] = output['Annual_Exp_Cnt_Bldgs_Flooded'] / output['total_buildings']
    output['annual_exp_people_flooded'] = output['estimate_t'] * output['annual_exp_percent_flooded']
    output.to_file(
        os.path.join(output_dir, 'BCDC_flooded_statistics.gpkg'),
        driver="GPKG"
    )

    ################
    ##### CES4 #####
    ################
    print('running CES4...')
    ces4 = gpd.read_file("data/CES4.gpkg").to_crs(raster.rio.crs)

    # # Totals
    all_buildings = pd.merge(all_buildings, all_damages, on="building_fid", how="left").fillna(0)
    ces4_grouping_columns = ['Tract', 'AED'] + [i for i in all_buildings.columns if 'total_damage' in i]
    ces4_buildings = gpd.sjoin(all_buildings, ces4, how="inner")[ces4_grouping_columns]
    print(ces4_buildings)
    print(ces4_buildings.columns)

    ces4_statistics = ces4_buildings.groupby('Tract').sum()
    ces4_building_totals = ces4_buildings.groupby('Tract').count()['AED'].rename("total_buildings")
    print('getting annual expected buildings flooded...')
    buildings_flooded_buff = []
    bldg_cnt_col_buff = []
    for dc in damage_columns:
        count_col = dc.replace('total_damage_', 'count_flooded_')
        buildings_flooded_buff.append(ces4_buildings[ces4_buildings[dc] > 0].groupby('Tract').count()[dc].rename(count_col))
        bldg_cnt_col_buff.append(count_col)
    buildings_flooded = recursive_merge(*buildings_flooded_buff)
    buildings_flooded['Annual_Exp_Cnt_Bldgs_Flooded'] = buildings_flooded.apply(
        lambda row: calculate_AEV(
            rps,
            [row[col] for col in bldg_cnt_col_buff], 
        ),
        axis=1, 
    )
    ces4_statistics = recursive_merge(ces4.set_index("Tract"), ces4_statistics, ces4_building_totals, buildings_flooded).reset_index()
    ces4_statistics['annual_exp_percent_flooded'] = ces4_statistics['Annual_Exp_Cnt_Bldgs_Flooded'] / ces4_statistics['total_buildings']
    ces4_statistics['annual_exp_people_flooded'] = ces4_statistics['TotPop19'] * ces4_statistics['annual_exp_percent_flooded']
    ces4_statistics.to_file(
        os.path.join(output_dir, 'CES4_flooded_statistics.gpkg'),
        driver="GPKG"
    )

    print("file written, sending...")
    if not os.path.exists("/results"):
        os.makedirs("/results")
    results_dir = f"/results/{xid}"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    shutil.make_archive(os.path.join(results_dir, "results"), "zip", output_dir)
    return flask.send_from_directory(results_dir, "results.zip")

