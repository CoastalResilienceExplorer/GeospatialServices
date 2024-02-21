# Blockgroup and Census Tract Risk
## Data Description
### Summary
This README describes the data columns included in the following files:

Marsh Restoration
- BCDC_results.gpkg
- CES4_results.gpkg

Horizontal Levees
- BCDC_hl_results.gpkg
- CES4_hl_results.gpkg

### AEV (Annual Expected Value) - Marsh Restoration
This is the annual expected value at risk under a given sea level rise and adaptation scenario.

AEV is calculated using trapezoidal integration across three return periods (1, 20, and 100 year storms), to get to an annualized value that weights storm intensity by expected frequency.  For example `AEV_Econ_05e` is the Annual Expected Value at Risk, in dollars, in the event of 0.5m sea level rise, existing marsh.  

### AEB (Annual Expected Benefit)
This is the annual expected benefit of an adaptation scenario under a given sea level rise.  AEB is calculated by subtracting the control scenario from the adaptation scenario.  For example `AEB_Econ_sl1` is the Annual Expected Benefit from marshes under 1m sea level rise.

### EconFlooded
This is the dollar value at risk in the event of a particular storm severity under a given sea level rise and adaptation scenario.  For example, `EconFlooded_0e20` is the expected economic damage under 0m sea level rise, existing marsh condition, for the 1 in 20 year storm.  These values are integrated across return periods to produce AEV, which is then differenced across adaptation scenarios to produce AEB.

### PopFlooded
This is the dollar value at risk in the event of a particular storm severity under a given sea level rise and adaptation scenario.  For example, `PopFlooded_0e20` is the expected population at risk under 0m sea level rise, existing marsh condition, for the 1 in 20 year storm.  These values are integrated across return periods to produce AEV, which is then differenced across adaptation scenarios to produce AEB.

### HighVuln
This is a binary variable indicating if a geography qualifies as being highly socially vulnerable.  

For CES4, it uses the SB535 Disadvantaged Communities dataset.  

For BCDC, it uses a similar calculation, defining High Vulnerability using the number of social vulnerability indicators above the 70th and 90th percentile.  If BCDC defines a Blockgroup as having 6 indicators in the 90th percentile, or 8 indicators in the 70th percentile, it is considered Highly Vulnerable.

### AEV (Annual Expected Value) - Horizontal Levees
For Horizontal Levees, the Annual Expected Value was calculated only as the difference between two storms.  This is because return periods were not used to model horizontal levees.  Rather, a synthetic storm was picked out as using an extreme value distribution that accounted for both wave height and storm surge.  