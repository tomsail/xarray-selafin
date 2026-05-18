# API Reference

## Opening a SELAFIN file

```python
import xarray as xr

ds = xr.open_dataset(filename, engine="selafin", lang="en", lazy_loading=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filename` | `str` or path | -- | Path to the `.slf` file |
| `engine` | `str` | -- | Must be `"selafin"` |
| `lang` | `str` | `"en"` | Variable language: `"en"` or `"fr"` |
| `lazy_loading` | `bool` | `True` | If `True`, data is read on demand |
| `disable_lock` | `bool` | `False` | Disable thread-safe file locking |
| `chunks` | `dict` or `None` | `None` | Dask chunk sizes (e.g. `{"time": -1, "node": 50}`) |

## Dataset structure

### Dimensions

| Dimension | Description | Present in |
|-----------|-------------|------------|
| `time` | Time steps | 2D and 3D |
| `node` | Mesh nodes | 2D and 3D |
| `plan` | Vertical layers (sigma levels) | 3D only |

### Coordinates

| Coordinate | Dimension | Type | Description |
|------------|-----------|------|-------------|
| `x` | `(node,)` | `float32` | Easting / x mesh coordinates |
| `y` | `(node,)` | `float32` | Northing / y mesh coordinates |
| `time` | `(time,)` | `datetime64` | Time stamps |

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"Converted with xarray-selafin"` | File title (up to 80 chars) |
| `language` | `str` | `"en"` | Language for variable detection |
| `float_size` | `int` | `4` | Precision: `4` (single) or `8` (double) |
| `endian` | `str` | `">"` | Byte order: `">"` (big) or `"<"` (little) |
| `params` | `tuple` | *(rebuilt)* | Integer parameter table (10 values) |
| `ipobo` | `ndarray` | *(rebuilt)* | Boundary node pointer array |
| `ikle2` | `ndarray` | **required** | 2D connectivity, shape `(n_elements, 3)`, **1-indexed** |
| `ikle3` | `ndarray` | *(rebuilt)* | 3D connectivity, shape `(n_prisms, 6)`, 1-indexed |
| `variables` | `dict` | *(auto-detected)* | Maps short names to `(long_name, unit)` tuples |
| `date_start` | `tuple` | *(from first time)* | `(year, month, day, hour, minute, second)` |

---

## Writing a SELAFIN file

```python
from xarray_selafin.xarray_backend import SelafinAccessor  # registers .selafin accessor

ds.selafin.write("output.slf")
```

### Required attributes for export

!!! danger "Export will fail without these"
    The two attributes below **must** be set correctly before calling `ds.selafin.write()`:

**`ikle2`** -- triangular connectivity table, **1-based indexing**:

```python
from scipy.spatial import Delaunay

ikle = Delaunay(np.vstack((x, y)).T).simplices  # 0-based from scipy
ds.attrs["ikle2"] = ikle + 1                    # SELAFIN requires 1-based
```

**`variables`** -- dictionary mapping each data variable name to a `(long_name, unit)` tuple:

```python
ds.attrs["variables"] = {
    "WINDX": ("WINDX", "M/S"),
    "WINDY": ("WINDY", "M/S"),
    "PATM":  ("PATM", "PASCAL"),
    "TAIR":  ("TAIR", "DEGREES C"),
}
```

Each key **must match** a variable name in the dataset. Without this dict, variable metadata in the output file will be empty or the write will crash.

---

## Variable definitions

Built-in TELEMAC variable definitions (French and English):

### 2D variables (partial list)

| ID | English name | Unit |
|----|-------------|------|
| `U` | VELOCITY U | M/S |
| `V` | VELOCITY V | M/S |
| `H` | WATER DEPTH | M |
| `S` | FREE SURFACE | M |
| `B` | BOTTOM | M |
| `M` | SCALAR VELOCITY | M/S |
| `F` | FROUDE NUMBER | -- |
| `TAU` | BOTTOM SHEAR STRESS | PASCAL |

### 3D variables (partial list)

| ID | English name | Unit |
|----|-------------|------|
| `Z` | ELEVATION Z | M |
| `U` | VELOCITY U | M/S |
| `V` | VELOCITY V | M/S |
| `W` | VELOCITY W | M/S |
| `NUX` | NUX FOR VELOCITY | M2/S |

Full tables: `xarray_selafin/data/Serafin_var2D.csv` and `Serafin_var3D.csv`.
