import geopandas as gpd
import os

BCDC_FIELDS = ['fid', 'GEOID', 'TRACTID', 'geometry', 'HighVuln']
CES4_FIELDS = ['fid', 'TRACT', 'geometry', 'HighVuln']

_BCDC = [
    '/Users/chlowrie/Desktop/OPC/results/hl_namefix/BCDC_hl_results.gpkg',
    '/Users/chlowrie/Desktop/OPC/results/BCDC_results.gpkg',
]

_CES4 = [
    '/Users/chlowrie/Desktop/OPC/results/hl_namefix/CES4_hl_results.gpkg',
    '/Users/chlowrie/Desktop/OPC/results/CES4_results.gpkg',
]

OUTPUT = '/Users/chlowrie/Desktop/OPC/results/fields_fix'

def highVulnCalc(midVuln, highVuln):
    value_to_return = 0
    if midVuln >= 8:
        value_to_return = 1
    if highVuln >= 6:
        value_to_return = 1
    if midVuln + highVuln >= 8:
        value_to_return = 1
    return(value_to_return)

def other_fields(i):
    return 'AEB' in i or 'AEV' in i or 'Flooded' in i

for BCDC_path in _BCDC:
    BCDC = gpd.read_file(BCDC_path)
    BCDC['HighVuln'] = BCDC.apply(lambda x: highVulnCalc(x['socVuln70'], x['socVuln90']), axis=1)
    BCDC = BCDC[[c for c in BCDC.columns if c in BCDC_FIELDS or other_fields(c)]]
    BCDC.to_file(os.path.join(OUTPUT, BCDC_path.split('/')[-1]))

for CES4_path in _CES4:
    CES4 = gpd.read_file(CES4_path)
    CES4 = CES4[[c for c in CES4.columns if c in CES4_FIELDS or other_fields(c)]]
    CES4.to_file(os.path.join(OUTPUT, CES4_path.split('/')[-1]))