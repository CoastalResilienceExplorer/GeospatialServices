for i in `cat ncei.txt`
do
    curl -o data/$i https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/dem/NCEI_ninth_Topobathy_2014_8483/CA/$i
done