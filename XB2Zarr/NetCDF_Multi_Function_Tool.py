import os
import xarray as xr
import rioxarray
import numpy as np
import warnings
import rasterio
from PIL import Image
import numpy as np
import time
import dask
from dask.diagnostics import ProgressBar
# import matplotlib.pyplot as plt
warnings.filterwarnings("ignore", category=rasterio.errors.NotGeoreferencedWarning)



start_time_total = time.time()

start_time_idx = 0
end_time_idx = 10

drive_letter = 'W:\\'
input_relative_path_reef_1s = r'Documents\Projects\Coastal_Resilience_Lab\04_USVI\01_Data\XBeach\Longreef\rp_100_1s\xboutput.nc'
input_relative_path_no_reef_1s = r'Documents\Projects\Coastal_Resilience_Lab\04_USVI\01_Data\XBeach\Longreef\No_Reef\rp_100_1s\xboutput.nc'
input_relative_path_reef_100s = r'Documents\Projects\Coastal_Resilience_Lab\04_USVI\01_Data\XBeach\Longreef\rp_100\xboutput.nc'
output_relative_path_general = r'Documents\Projects\Coastal_Resilience_Lab\04_USVI\03_Houdini\98_Input\XB'


def get_bounds(ds):
    print(ds.isel(nx=0).globalx.min().compute())
    print(ds.isel(nx=-1).globalx.min().compute())


def write_timestep_images(rds, full_output_path, start_time, end_time, variable, time_method):

    # Construct the full file path for the input and output

    # Define spacing for the grid
    x_spacing = 10  # Adjust this value as needed
    y_spacing = 10  # Adjust this value as needed

    # Open the dataset with Dask using xarray
    # rds = xr.open_dataset(full_input_path, chunks={time_method: 500})

    # Extract 'globalx', 'globaly', and the selected variable
    globalx = rds['globalx']
    globaly = rds['globaly']
    selected_var = rds[variable]

    # Perform flattening and index calculations once
    globalx_flat = globalx.values.flatten()
    globaly_flat = globaly.values.flatten()

    x_min, x_max = np.min(globalx_flat), np.max(globalx_flat)
    y_min, y_max = np.min(globaly_flat), np.max(globaly_flat)
    num_points_x = int((x_max - x_min) / x_spacing) + 1
    num_points_y = int((y_max - y_min) / y_spacing) + 1

    x_indices = ((globalx_flat - x_min) / x_spacing).astype(int)
    y_indices = ((globaly_flat - y_min) / y_spacing).astype(int)
    valid_indices = (x_indices >= 0) & (x_indices < num_points_x) & (y_indices >= 0) & (y_indices < num_points_y)

    # Create a template grid
    template_grid = np.full((num_points_y, num_points_x), np.nan, dtype=float)

    # Iterate over each specified timestep
    for timestep in range(start_time, end_time + 1):
        print(f"Processing timestep {timestep}...")

        # Copy the template grid for current timestep
        grid_values = template_grid.copy()

        # Extract data for the current timestep and flatten
        timestep_flattened = selected_var.isel({time_method: timestep}).values.flatten()

        # Populate grid_values using pre-calculated indices
        grid_values[y_indices[valid_indices], x_indices[valid_indices]] = timestep_flattened[valid_indices]

        # Replace NaN values with -1000 (or another value if needed)
        grid_values[np.isnan(grid_values)] = -1000

        # Save the image for the current timestep
        tiff_filename = os.path.join(full_output_path, f'{variable}_timestep_{timestep}.tiff')
        image = Image.fromarray(grid_values.astype('float32'), 'F')
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(tiff_filename, 'TIFF', compression=None)

        # # Save PNG Image
        # png_filename = os.path.join(full_output_path, f'{variable}_timestep_{timestep}.png')
        # image_png = Image.fromarray(normalized_values, 'L')
        # image_png = image_png.transpose(Image.FLIP_TOP_BOTTOM)
        # image_png.save(png_filename, 'PNG')

    print("Timesteps processed.")



def write_variable_max(input_relative_path, output_relative_path, start_time, end_time):

    # Construct the full file paths
    full_input_path = os.path.join(drive_letter, input_relative_path)
    full_output_path = os.path.join(drive_letter, output_relative_path)

    # Extract the last folder name from the input relative path
    last_folder_name = input_relative_path.split(os.sep)[-3]

    # Open the dataset without chunking to check dimensions
    temp_rds = rioxarray.open_rasterio(full_input_path)
    print("Dimensions of the dataset:", temp_rds.dims)

    # Open the dataset with Dask using xarray
    print("Opening dataset with Dask using xarray...")
    rds = xr.open_dataset(full_input_path, chunks={'globaltime': 500})
    print("Dataset opened with Dask.")

    # Extract 'globalx', 'globaly', and 'zs'
    globalx = rds['globalx']
    globaly = rds['globaly']
    zs = rds['zs']

    # Print initial dimensions
    print("globalx dimensions:", globalx.shape)
    print("globaly dimensions:", globaly.shape)
    print("zs dimensions:", zs.shape)

    # Convert indices to float
    start_time = float(zs['globaltime'].isel(globaltime=start_time).values)
    end_time = float(zs['globaltime'].isel(globaltime=end_time).values)

    # Select the subset of data
    subset_zs = zs.sel(globaltime=slice(start_time, end_time))

    with ProgressBar():
        max_values = subset_zs.max(dim='globaltime', skipna=True).compute()
    print("Maximum values calculated.")

    # Flatten the 'globalx' and 'globaly' arrays for the entire 2D space
    globalx_flat = globalx.values.flatten()
    globaly_flat = globaly.values.flatten()
    print("globalx_flat dimensions:", globalx_flat.shape)
    print("globaly_flat dimensions:", globaly_flat.shape)
    print("Arrays flattened.")

    # Print max_values dimensions
    print("max_values dimensions (before flatten):", max_values.shape)
    max_values_flattened = max_values.values.flatten()
    print("max_values dimensions (after flatten):", max_values_flattened.shape)

    # Calculate the extents (min and max values) of the flattened globalx and globaly
    x_min = np.min(globalx_flat)
    x_max = np.max(globalx_flat)
    y_min = np.min(globaly_flat)
    y_max = np.max(globaly_flat)

    # Specify the desired spacing between points for both axes
    x_spacing = 10  # Adjust as needed
    y_spacing = 10  # Adjust as needed

    # Calculate the number of points for each axis based on spacing
    num_points_x = int((x_max - x_min) / x_spacing) + 1
    num_points_y = int((y_max - y_min) / y_spacing) + 1

    # Create a 2D grid (grid_values) representing the values based on globalx and globaly
    grid_values = np.full((num_points_y, num_points_x), np.nan, dtype=float)

    # Optimized code to populate grid_values
    x_indices = ((globalx_flat - x_min) / x_spacing).astype(int)
    y_indices = ((globaly_flat - y_min) / y_spacing).astype(int)

    valid_indices = (x_indices >= 0) & (x_indices < num_points_x) & (y_indices >= 0) & (y_indices < num_points_y)

    grid_values[y_indices[valid_indices], x_indices[valid_indices]] = max_values_flattened[valid_indices]

    # Replace NaN values
    grid_values[np.isnan(grid_values)] = 0

    # Save the image as a 16-bit TIFF
    tiff_filename = os.path.join(full_output_path, f'Max_{last_folder_name}_{start_time_idx}_{end_time_idx}.tiff')
    image = Image.fromarray(grid_values.astype('float32'), 'F')
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.save(tiff_filename, 'TIFF', compression=None)
    print("Image saved.")

    # Return the array
    return grid_values



# Must be called directly after generating both max images, which populates the arrays to compare
def generate_difference_image(output_relative_path, start_time, end_time):
    grayscale_output_path = os.path.join(drive_letter, output_relative_path, f'difference_image_{start_time}_{end_time}_grayscale.tiff')
    color_output_path = os.path.join(drive_letter, output_relative_path, f'difference_image_{start_time}_{end_time}_color.tiff')

    # Ensure that both arrays have the same shape
    # if reef_grid_values.shape != no_reef_grid_values.shape:
    # raise ValueError("The two arrays must have the same dimensions for comparison.")

    # Calculate the difference between the two arrays (including both positive and negative differences)
    difference_array = no_reef_grid_values - reef_grid_values

    # Flip the difference array vertically to correct the orientation
    difference_array = np.flipud(difference_array)

    # Create a color difference image using a reversed colormap (coolwarm_r) with the specified range
    cmap = plt.get_cmap('RdBu_r')

    # Normalize the colormap around zero
    vmax = max(abs(difference_array.max()), abs(difference_array.min()))
    vmin = -vmax

    # Create color difference image
    rgba_image = cmap(np.clip((difference_array - vmin) / (vmax - vmin), 0, 1))

    # Create grayscale image from the difference array
    grayscale_difference_image = Image.fromarray(difference_array.astype('float32'), 'F')

    # Create color image from the RGBA array (as float32)
    color_difference_image = Image.fromarray((rgba_image[:, :, :3] * 255).astype('uint8'), 'RGB')

    # Print the minimum and maximum values of the difference array
    print("Minimum value in difference array:", difference_array.min())
    print("Maximum value in difference array:", difference_array.max())

    # Save the grayscale and color difference images as TIFF
    grayscale_difference_image.save(grayscale_output_path, 'TIFF', compression=None)
    color_difference_image.save(color_output_path, 'TIFF', compression=None)



# Call write timesteps zs
#write_timestep_images(input_relative_path=input_relative_path_reef_1s, output_relative_path=output_relative_path_general, start_time=start_time_idx, end_time=end_time_idx, variable='zs', time_method='globaltime')

# Call write timesteps zb_mean
# write_timestep_images(input_relative_path=input_relative_path_reef_100s, output_relative_path=output_relative_path_general, start_time=0, end_time=0, variable='zb_mean', time_method='meantime')

# # Call write_variable_max
# # Note, currently if called multiple times, it will overwrite the output. Only call multiple times if needed for the generate_difference_image function immediately after
# reef_grid_values = write_variable_max(input_relative_path=input_relative_path_reef_1s, output_relative_path=output_relative_path_general, start_time=start_time_idx, end_time=end_time_idx)

# no_reef_grid_values = write_variable_max(input_relative_path=input_relative_path_no_reef_1s, output_relative_path=output_relative_path_general, start_time=start_time_idx, end_time=end_time_idx)

# # Call generate_difference_image with grid values
# generate_difference_image(output_relative_path=output_relative_path_general, start_time=start_time_idx, end_time=end_time_idx)



# # End the timer and print the total runtime
# end_time_total = time.time()
# print(f"Total runtime: {end_time_total - start_time_total} seconds")
