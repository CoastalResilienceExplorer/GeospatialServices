import pandas as pd

ddf_freq = 'data/bg_dmg_functions/building_freq_by_bg.csv'
avg_cost = 'data/bg_dmg_functions/avg_cost_by_bg.csv'
all_ddf = 'data/bg_dmg_functions/AllDDF/flBldgStructDmgFn-Table 1.csv'

ddf_freq = pd.read_csv(ddf_freq, dtype = {'Blockgroup': str, 'BDDF_ID': str})[['BDDF_ID', 'Blockgroup', 'Percent']]
all_ddf = pd.read_csv(all_ddf, dtype = {'BDDF_ID': str})
avg_cost = pd.read_csv(avg_cost, dtype = {'Blockgroup': str})
print(ddf_freq)

bgs = ddf_freq['Blockgroup'].unique()
buff = []
for bg in bgs:
    freqs = ddf_freq[ddf_freq['Blockgroup'] == bg]
    filtered_ddfs = pd.merge(all_ddf, freqs, left_on='BDDF_ID', right_on='BDDF_ID', how='inner')
    depth_cols = [i for i in filtered_ddfs.columns if i[0:2] == 'ft' and i[-1] != 'm']
    for col in depth_cols:
        filtered_ddfs[col] = filtered_ddfs[col] * filtered_ddfs['Percent'] / 100.0

    filtered_ddfs = filtered_ddfs[depth_cols + ['Blockgroup']].groupby('Blockgroup').sum()
    rename_cols = {
        i: f'm{round(float(i[2:]) * 0.3, 2)}' for i in depth_cols 
    }
    filtered_ddfs = filtered_ddfs.rename(columns=rename_cols)
    buff.append(filtered_ddfs)

pd.concat(buff).to_csv('data/composite_ddfs_by_bg.csv')