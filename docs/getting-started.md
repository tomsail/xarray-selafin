# Getting Started

## Installation

=== "pip"

    ```bash
    pip install xarray-selafin
    ```

=== "conda"

    ```bash
    conda install -c conda-forge xarray_selafin
    ```

The backend registers itself automatically with xarray via the `xarray.backends` entry point. No additional configuration is needed.

## Reading a SELAFIN file

```python
import xarray as xr

ds = xr.open_dataset("path/to/file.slf", engine="selafin")
print(ds)
```

Data is **lazily loaded** by default -- array values are only read from disk when you access them. This keeps memory usage low for large simulations.

### Using a context manager

```python
with xr.open_dataset("file.slf", engine="selafin") as ds:
    print(ds)
    # file is closed automatically at the end of the block
```

Without a context manager, call `ds.close()` when done to avoid a `ResourceWarning`.

### French variables

If the SELAFIN file uses French variable names, pass `lang="fr"`:

```python
ds = xr.open_dataset("file.slf", lang="fr", engine="selafin")
```

### Eager loading

To load all data into memory immediately (no lazy arrays):

```python
ds = xr.open_dataset("file.slf", lazy_loading=False, engine="selafin")
```

## Indexing and slicing

Standard xarray indexing works as expected:

```python
# Select last time step
ds_last = ds.isel(time=-1)

# Select a time range
ds_range = ds.isel(time=slice(0, 10))

# For 3D: select a specific vertical plan and time range
ds_slice = ds.isel(time=slice(0, 10), plan=0)
```

## Manipulating variables

```python
# Add a computed variable
ds = ds.assign(speed=lambda x: (x.U**2 + x.V**2) ** 0.5)

# Optionally register its name and unit for SELAFIN export
ds.attrs["variables"]["speed"] = ("SCALAR VELOCITY", "M/S")

# Remove a variable
ds = ds.drop_vars(["W"])
```

## Extracting a layer from 3D data

The `.selafin` accessor provides a method to extract a single vertical layer from a 3D dataset, producing a standard 2D dataset:

```python
ds_bottom = ds.selafin.get_dataset_as_2d(plan=0)   # bottom layer
ds_top = ds.selafin.get_dataset_as_2d(plan=-1)      # top layer
```

## Writing a SELAFIN file

```python
from xarray_selafin.xarray_backend import SelafinAccessor # important, otherwise export won't work
ds.selafin.write("output.slf")
```

This writes the full dataset (all time steps, all variables) back to the SELAFIN binary format, preserving mesh connectivity and metadata.

!!! warning
    It is important for the file to follow the correct structure, otherwise the export won't work. See details in the [API](./api/#required-attributes-for-export)

## Dask integration

For parallel processing with Dask, simply pass `chunks` to xarray:

```python
ds = xr.open_dataset("file.slf", engine="selafin", chunks={"time": -1, "node": 50})
result = ds.mean(dim="time").compute()
```
