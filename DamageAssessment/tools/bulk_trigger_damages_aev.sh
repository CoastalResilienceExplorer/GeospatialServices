# ZARR=data/damages_test.zarr
ZARR=$1

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for clim in Future2050 Historic
do
    for scen in S1 S2 S3 S4
    do
        id=${clim}_${scen}_AEV_Damages
        python3 $SCRIPT_DIR/trigger.py -t damages_aev \
            --id $id \
            --damages_zarr $ZARR \
            --formatter ${clim}_${scen}_Tr{rp}_storm72h_hmax_masked
        echo $id
    done
done

