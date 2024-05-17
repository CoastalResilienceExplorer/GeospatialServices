# ZARR=data/damages_test.zarr
ZARR=$1

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for clim in Future2050 Historic
do
    for scen in S1 S2 S3 S4
    do
        id=AEV_${clim}_${scen}_AEV_t33
        python3 $SCRIPT_DIR/trigger.py -t damages_aev \
            --id $id \
            --damages_zarr $ZARR \
            --formatter WaterDepth_${clim}_${scen}_Tr{rp}_t33
        echo $id
    done
done

