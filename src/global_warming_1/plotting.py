from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.lines import Line2D

WORLD_URL = (
    "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
)


def plot_coastal_distance_vs_trend(
    df: pd.DataFrame,
    type_col: str = "type",
    x_col: str = "dist_coast_km",
    y_col: str = "trend_per_decade",
    type_order: list | None = None,
    show_trend_line: bool = True,
    show_ci_band: bool = True,
    ci_level: float = 0.95,
    figsize: tuple = (9, 6),
    title: str = "Warming Trend vs. Distance to Coast",
    save_path: Path | None = None,
) -> None:
    """
    Scatter plot of distance to coast vs. temperature trend, coloured by type,
    with an OLS linear fit (slope reported per 1000 km with confidence interval).
    """
    data = df.dropna(subset=[x_col, y_col, type_col])

    types = type_order if type_order is not None else sorted(data[type_col].unique())
    if len(types) <= 10:
        colors = plt.get_cmap("tab10")(np.arange(len(types)))
    else:
        colors = plt.get_cmap("hsv")(np.linspace(0, 1, len(types), endpoint=False))

    fig, ax = plt.subplots(figsize=figsize)

    # Scatter, one colour per type
    for t, c in zip(types, colors):
        subset = data[data[type_col] == t]
        ax.scatter(
            subset[x_col],
            subset[y_col],
            s=70,
            color=c,
            edgecolor="white",
            linewidth=0.8,
            alpha=0.9,
            label=f"{t} (n={len(subset)})",
            zorder=3,
        )

    # Linear fit with CI
    if show_trend_line and len(data) >= 3:
        X = sm.add_constant(data[x_col])
        res = sm.OLS(data[y_col], X).fit()

        slope_1000 = res.params[x_col] * 1000
        lo, hi = res.conf_int(alpha=1 - ci_level).loc[x_col] * 1000

        xs = np.linspace(data[x_col].min(), data[x_col].max(), 100)
        Xp = np.column_stack([np.ones_like(xs), xs])
        pred = res.get_prediction(Xp).summary_frame(alpha=1 - ci_level)

        ax.plot(
            xs,
            pred["mean"],
            color="black",
            linestyle="--",
            linewidth=1.5,
            zorder=2,
            label=(
                f"Linear fit: {slope_1000:.2f} °C/decade per 1000 km\n"
                f"({ci_level:.0%} CI: [{lo:.2f}, {hi:.2f}], $R^2$ = {res.rsquared:.2f})"
            ),
        )
        if show_ci_band:
            ax.fill_between(
                xs,
                pred["mean_ci_lower"],
                pred["mean_ci_upper"],
                color="black",
                alpha=0.10,
                linewidth=0,
                zorder=1,
            )

    # Labels, title, grid
    ax.set_xlabel("Distance to coast (km)", fontsize=12)
    ax.set_ylabel("Temperature trend (°C per decade)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.grid(True, linestyle=":", alpha=0.5, zorder=0)
    ax.tick_params(labelsize=10)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    ax.legend(
        title="Location type",
        frameon=True,
        framealpha=0.95,
        fontsize=10,
        title_fontsize=11,
    )

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()


def plot_stations(
    df,
    lat_col="lat",
    lon_col="lon",
    value_col="trend_per_decade",
    type_col="type",
    label=True,
    zoom=True,
    pad=3,
    cmap="viridis",
    figsize=(16, 9),
    markersize=25,
    fontsize=6,
    save_path: Path | None = None,
):
    """Plot station locations on a map, colored by value_col, marker by type_col."""
    gdf = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
        crs="EPSG:4326",
    )
    world = gpd.read_file(WORLD_URL)

    fig, ax = plt.subplots(figsize=figsize)
    world.plot(ax=ax, color="#eeeeee", edgecolor="#999999", linewidth=0.4)

    markers = {"inland": "o", "near-coastal": "s", "coastal": "^"}
    vmin, vmax = gdf[value_col].min(), gdf[value_col].max()

    for t, sub in gdf.groupby(type_col):
        sub.plot(
            ax=ax,
            column=value_col,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            marker=markers.get(t, "o"),
            markersize=markersize,
            edgecolor="black",
            linewidth=0.3,
            zorder=3,
        )

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin, vmax))
    fig.colorbar(sm, ax=ax, shrink=0.6, label=value_col)

    handles = [
        Line2D(
            [],
            [],
            marker=markers.get(t, "o"),
            linestyle="",
            color="grey",
            markeredgecolor="black",
            markersize=6,
            label=t,
        )
        for t in gdf[type_col].unique()
    ]
    ax.legend(handles=handles, title=type_col, loc="lower left", fontsize=8)

    if label:
        for name, row in gdf.iterrows():
            ax.annotate(
                str(name),
                (row.geometry.x, row.geometry.y),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=fontsize,
                alpha=0.8,
                zorder=4,
            )

    if zoom:
        minx, miny, maxx, maxy = gdf.total_bounds
        ax.set_xlim(minx - pad, maxx + pad)
        ax.set_ylim(miny - pad, maxy + pad)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Station locations")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()
