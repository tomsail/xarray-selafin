"""
Generate interactive HTML plots for the xarray-selafin documentation.

Each plot is exported as a standalone HTML file using holoviews + Panel,
then embedded in the mkdocs pages via <iframe> tags.

Usage:
    python scripts/generate_plots.py
"""
from pathlib import Path

import geoviews as gv
import holoviews as hv
import hvplot.pandas  # noqa: F401
import hvplot.xarray  # noqa: F401
import numpy as np
import pandas as pd
import panel as pn
import xarray as xr
from bokeh.models import HoverTool

hv.extension("bokeh")

DATA_DIR = Path("tests/data")
DOCS_DIR = Path("docs")


def plot_selafin(ds, var, geo=False, **kwargs):
    """Plot a 2D SELAFIN variable as a filled TriMesh."""
    if geo:
        lib = gv
    else:
        lib = hv
    simplices = pd.DataFrame(ds.attrs["ikle2"] - 1, columns=["v0", "v1", "v2"])
    nodes = np.column_stack([ds.x.values, ds.y.values, ds[var].values])
    nodes = lib.Points(nodes, vdims="z")
    trimesh = lib.TriMesh((simplices, nodes), name=var)
    hover = HoverTool(tooltips=[("x", "$x"), ("y", "$y"), (var, "@z"), ("tri", "@v0, @v1, @v2")])
    if geo:
        trimesh = trimesh * lib.WMTS("http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    return trimesh.opts(
        lib.opts.TriMesh(
            filled=True,
            colorbar=True,
            edge_color="z",
            inspection_policy="edges",
            node_size=0,
            tools=[hover],
            **kwargs,
        )
    )


def plot_quiver(ds, time_idx=0, scale=0.05, **kwargs):
    t = ds.isel(time=time_idx)

    x = t.x.values
    y = t.y.values
    u = t["WINDX"].values
    v = t["WINDY"].values

    angle = np.arctan2(v, u)
    mag = np.sqrt(u**2 + v**2)

    vf = hv.VectorField((x, y, angle, mag))

    return vf.opts(
        hv.opts.VectorField(
            magnitude="Magnitude",
            color="Magnitude",
            colorbar=True,
            tools=["hover"],
            **kwargs,
        )
    )


def save_plot(plot, filename, height=700):
    """Wrap a holoviews object in a responsive Panel layout and save to HTML."""
    pane = pn.Row(
        pn.pane.HoloViews(plot, sizing_mode="stretch_both"),
        sizing_mode="stretch_width",
        height=height,
    )
    out_path = DOCS_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pane.save(str(out_path))
    print(f"  saved: {out_path}")


# ===========================================================================
# 2D Tidal Flats
# ===========================================================================
def generate_2d_tidal_flats():
    print("Generating 2D tidal flats plots...")
    ds = xr.open_dataset(DATA_DIR / "r2d_tidal_flats.slf", engine="selafin")

    # Free surface (TriMesh)
    plot = plot_selafin(ds.isel(time=-1), "S", cmap="coolwarm", width=1000, height=200)
    save_plot(plot, "2d_free_surface.html", height=200)

    # Bathymetry (TriMesh)
    plot = plot_selafin(ds.isel(time=-1), "B", cmap="viridis", width=1000, height=200)
    save_plot(plot, "2d_bathymetry.html", height=200)

    # Time series at node 0
    plot_ts = ds.isel(node=0).hvplot(x="time", y="S", responsive=True)
    save_plot(plot_ts, "2d_timeseries.html", height=400)

    ds.close()


# ===========================================================================
# TOMAWAC (waves)
# ===========================================================================
def generate_tomawac():
    print("Generating TOMAWAC plots...")
    ds = xr.open_dataset(DATA_DIR / "tom_manche.slf", engine="selafin", lang="fr")

    # Wave height on geographic map
    plot = plot_selafin(ds.isel(time=-1), "HAUTEUR_HM0", geo=True, cmap="rainbow4", width=800, height=800)
    save_plot(plot, "tomawac_hm0.html", height=700)

    ds.close()


# ===========================================================================
# 3D Bump
# ===========================================================================
def generate_3d_bump():
    print("Generating 3D bump plots...")
    ds = xr.open_dataset(DATA_DIR / "r3d_bump.slf", engine="selafin")

    # Horizontal section at top layer (TriMesh)
    plot = plot_selafin(ds.isel(time=-1, plan=-1), "Z", cmap="coolwarm", width=1000, height=200)
    save_plot(plot, "3d_bump_z.html", height=300)

    # Vertical scatter section: x vs Z colored by U
    plot_scatter = ds.isel(time=-1).hvplot.scatter(x="x", y="Z", c="U", cmap="coolwarm", responsive=True)
    save_plot(plot_scatter, "3d_bump_scatter.html", height=500)

    ds.close()


# ===========================================================================
# Create from scratch
# ===========================================================================
def generate_scratch():
    print("Generating scratch mesh plot...")
    from scipy.spatial import Delaunay

    # Create a mesh
    xx = np.arange(10)
    yy = np.arange(10)
    x, y = np.meshgrid(xx, yy)
    x = x.ravel() + 0.3 * np.random.rand(100)
    y = y.ravel() + 0.3 * np.random.rand(100)
    ikle = Delaunay(np.vstack((x, y)).T).simplices  # 0-indexed from scipy

    # Create data
    ds = xr.Dataset(
        {
            "WINDX": (("time", "node"), np.matlib.repmat(np.arange(0, 10, 0.1), 5, 1)),
            "WINDY": (("time", "node"), np.matlib.repmat(np.arange(0, 20, 0.2), 5, 1)),
            "PATM": (("time", "node"), np.full((5, 100), 101325.0)),
        },
        coords={
            "x": ("node", x),
            "y": ("node", y),
            "time": pd.date_range("2024-01-01", periods=5, freq="6h"),
        },
    )

    # --- CRITICAL: set attributes for SELAFIN export ---
    ds.attrs["ikle2"] = ikle + 1  # convert to 1-based indexing

    ds.attrs["variables"] = {
        "WINDX": ("WINDX", "M/S"),
        "WINDY": ("WINDY", "M/S"),
        "PATM": ("PATM", "PASCAL"),
    }

    # Plot the mesh with data
    plot = plot_quiver(ds, time_idx=0, scale=0.1, cmap="rainbow4").opts(width=1000, height=600)

    save_plot(plot, "scratch_wind.html", height=600)


# ===========================================================================
# Main
# ===========================================================================
if __name__ == "__main__":
    generate_2d_tidal_flats()
    generate_tomawac()
    generate_3d_bump()
    generate_scratch()

    print("\nAll plots generated.")
