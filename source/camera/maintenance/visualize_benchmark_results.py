"""
Visualize the CSV results produced by the ZividBenchmark sample.

This script analyzes and visualizes Zivid benchmark CSV results with different categories.
Pass one CSV file to get an overview of a single system, or several to compare systems.

Usage: python visualize_benchmark_results.py [csv_file ...]

For more information about benchmarking your system, check out this tutorial:
https://support.zivid.com/en/latest/camera/api-reference/benchmarks/benchmarking-your-system.html

"""

# pandas-stubs cannot follow the dynamic frame reshaping done here, so the annotations
# below describe the intended types rather than what pyright is able to infer.
# pyright: reportArgumentType=false, reportAttributeAccessIssue=false, reportCallIssue=false
# pyright: reportIndexIssue=false, reportOperatorIssue=false, reportReturnType=false

# A sample is a single file someone downloads and reads, so the charts live together
# here rather than being split across modules.
# pylint: disable=too-many-lines

import argparse
import os
import platform
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

# Zivid color palette
ZIVID_COLORS = {
    "primary_blue": "#03b9eb",  # Main logo and title color
    "primary_pink": "#ed3472",  # Links, CTA buttons, subtitles, highlighted text
    "primary_dark": "#34323d",  # Main text color
    "secondary_teal": "#91D2C8",  # Secondary color 1
    "secondary_blue": "#4A8FA4",  # Secondary color 2
}

# Set up Zivid styling
plt.style.use("default")  # Start with clean default style
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": ZIVID_COLORS["primary_dark"],
        "axes.labelcolor": ZIVID_COLORS["primary_dark"],
        "text.color": ZIVID_COLORS["primary_dark"],
        "xtick.color": ZIVID_COLORS["primary_dark"],
        "ytick.color": ZIVID_COLORS["primary_dark"],
        "grid.color": ZIVID_COLORS["secondary_teal"],
        "grid.alpha": 0.3,
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "figure.titlesize": 16,
    }
)

ZIVID_PALETTE = [
    ZIVID_COLORS["secondary_teal"],
    ZIVID_COLORS["secondary_blue"],
    ZIVID_COLORS["primary_blue"],
    ZIVID_COLORS["primary_pink"],
]
sns.set_palette(ZIVID_PALETTE)

KEYS_IDENTIFYING_A_RUN_RATHER_THAN_A_SYSTEM = {"Process_Id", "Log_File"}


def _draw_no_data_placeholder(ax: Axes, message: str, title: str) -> None:
    """Fill an otherwise empty plot with a message explaining what is missing.

    Args:
        ax: Matplotlib axes to draw on.
        message: Text to centre in the plot area.
        title: Title to set on the plot.
    """
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        transform=ax.transAxes,
        color=ZIVID_COLORS["primary_dark"],
        fontsize=12,
    )
    ax.set_title(title, color=ZIVID_COLORS["primary_blue"], fontweight="bold")


def _style_legend(ax: Axes, bbox_to_anchor: Optional[Tuple[float, float]] = None, loc: str = "best") -> None:
    """Add a legend styled with the Zivid colors.

    Args:
        ax: Matplotlib axes to add the legend to.
        bbox_to_anchor: Anchor point for placing the legend outside the axes.
        loc: Legend location, as accepted by Axes.legend.
    """
    legend = ax.legend(loc=loc) if bbox_to_anchor is None else ax.legend(bbox_to_anchor=bbox_to_anchor, loc=loc)
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor(ZIVID_COLORS["primary_dark"])


def _maybe_log_scale(ax: Axes, values: Sequence[float], axis: str, base_label: str) -> None:
    """Switch an axis to a logarithmic scale when the values span a wide range.

    Args:
        ax: Matplotlib axes to adjust.
        values: The values plotted along the axis.
        axis: Either "x" or "y".
        base_label: Axis label to extend with a log-scale marker.
    """
    non_zero_values = [value for value in values if value > 0]
    if not non_zero_values or max(non_zero_values) / min(non_zero_values) <= 100:
        return

    log_label = f"{base_label} - Log Scale"
    if axis == "y":
        ax.set_yscale("log")
        ax.set_ylabel(log_label, color=ZIVID_COLORS["primary_dark"])
    else:
        ax.set_xscale("log")
        ax.set_xlabel(log_label, color=ZIVID_COLORS["primary_dark"])


def load_benchmark_data(csv_file: Path) -> pd.DataFrame:
    """Load and preprocess benchmark data from CSV file.

    Args:
        csv_file: Path to the CSV file containing benchmark results.

    Returns:
        A pandas DataFrame with the "timestamp" column parsed as datetimes.

    Raises:
        FileNotFoundError: If `csv_file` does not exist.
    """
    if not csv_file.is_file():
        raise FileNotFoundError(
            f"Benchmark CSV file not found: {csv_file}\n"
            f"Run ZividBenchmark to produce one, or pass the path to an existing zivid_benchmark_results*.csv."
        )
    df = pd.read_csv(csv_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def load_multiple_datasets(csv_files: List[Path]) -> List[Dict[str, Any]]:
    """Load multiple CSV files and return datasets with platform info.

    Args:
        csv_files: Paths to CSV files with benchmark results.

    Returns:
        A list of dicts, each with a "file" path, a "data" DataFrame, and a
        "platform" dict extracted from the file's "system_info" rows.
    """
    datasets = []

    for csv_file in csv_files:
        df = load_benchmark_data(csv_file)

        system_info = df[df["test_category"] == "system_info"]
        platform_info = {}

        if not system_info.empty:
            for _, row in system_info.iterrows():  # pylint: disable=unused-variable
                key = row["test_name"]
                value = row["settings"]
                platform_info[key] = value

        datasets.append({"file": csv_file, "data": df, "platform": platform_info})

    return datasets


def sdk_log_directory() -> Optional[Path]:
    """Find the directory the Zivid SDK writes its log files to.

    Returns:
        The platform's Zivid API log directory, or None if the environment
        variable it is derived from is not set.
    """
    if platform.system() == "Windows":
        cache_home = os.environ.get("LOCALAPPDATA")
    else:
        cache_home = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    if not cache_home:
        return None
    return Path(cache_home) / "Zivid" / "API" / "Log"


def find_sdk_log_files(process_id: str) -> List[Path]:
    """Find every Zivid SDK log file written by the benchmark process.

    The SDK renames the first log file of a process to "<name>.first.log"
    when it closes it, and rotated files get "<name>.<n>.log", so the name
    recorded while the benchmark was running is usually not what is left on
    disk. A run that logs enough is spread over several of these files.

    Args:
        process_id: The "Process_Id" recorded by ZividBenchmark in the CSV.

    Returns:
        Every log file belonging to that process, oldest first. Empty if the
        log directory or any matching file cannot be found.
    """
    directory = sdk_log_directory()
    if directory is None or not directory.is_dir():
        return []
    matches = set(directory.glob(f"Zivid-*-{process_id}.log"))
    matches |= set(directory.glob(f"Zivid-*-{process_id}.*.log"))
    return sorted(matches, key=lambda log: log.stat().st_mtime)


def print_sdk_log_files(platform_info: Dict[str, str]) -> None:
    """Print every Zivid SDK log file belonging to the benchmarked run.

    All of them are listed rather than just one, because a run that rotates
    its log is spread over several files and they are only useful together.

    Args:
        platform_info: The dataset's platform info mapping.
    """
    process_id = platform_info.get("Process_Id")
    recorded_path = platform_info.get("Log_File")
    log_files = find_sdk_log_files(process_id) if process_id else []
    if not log_files and recorded_path and Path(recorded_path).is_file():
        log_files = [Path(recorded_path)]

    if log_files:
        print(f"  SDK log files for this run ({len(log_files)}), send all of them:")
        for log_file in log_files:
            print(f"    {log_file}")
    elif recorded_path:
        print(f"  SDK log files: none left on disk, {recorded_path} was recorded")
    elif process_id:
        print(f"  SDK log files: none found for process {process_id} in {sdk_log_directory()}")
    else:
        print("  SDK log files: not recorded in this CSV")


def _shorten_platform_value(key: str, value: str) -> str:  # pylint: disable=too-many-return-statements
    """Helper function to shorten platform values for labels.

    Args:
        key: The platform info key (e.g. "OS", "Camera_Model", "API_Version",
            or "Compute_Device_Model").
        value: The raw platform info value associated with the key.

    Returns:
        A shortened string representation of the value, suitable for use in
        plot labels.
    """
    if key == "OS":
        if "windows" in value.lower():
            return f"Win{value.split()[-1] if len(value.split()) > 1 else ''}"
        if "linux" in value.lower():
            return "Linux"
        if "macos" in value.lower():
            return "macOS"
        return value[:8]

    if key == "Camera_Model":
        return value.replace("Zivid ", "").replace(" ", "")

    if key == "Compute_Device_Model":
        return value

    if key == "API_Version":
        return f"v{value}"

    return value[:8] if len(value) > 8 else value


def generate_comparison_labels(datasets: List[Dict[str, Any]]) -> List[str]:
    """Generate short comparison labels based on platform differences.

    Args:
        datasets: List of dataset dicts as produced by
            load_multiple_datasets, each containing a "file" path and a
            "platform" dict.

    Returns:
        A list of label strings, one per dataset. If only one dataset is
        given, the label is the dataset's filename stem instead.
    """
    if len(datasets) <= 1:
        return [Path(datasets[0]["file"]).stem if datasets else "Dataset"]

    # Find keys that differ between datasets
    all_keys = set()
    for dataset in datasets:
        all_keys.update(dataset["platform"].keys())
    all_keys -= KEYS_IDENTIFYING_A_RUN_RATHER_THAN_A_SYSTEM

    differing_keys = []
    for key in all_keys:
        values = set()
        for dataset in datasets:
            if key in dataset["platform"]:
                values.add(dataset["platform"][key])
        if len(values) > 1:  # Key has different values
            differing_keys.append(key)

    # Generate labels based on differences
    labels = []
    for i, dataset in enumerate(datasets):
        label_parts = []

        for key in differing_keys[:2]:  # Limit to 2 most important differences
            if key in dataset["platform"]:
                value = dataset["platform"][key]
                label_parts.append(_shorten_platform_value(key, value))

        # If no differences found or no differing keys, use filename
        if not label_parts:
            label_parts.append(f"Config{i + 1}")

        labels.append(" | ".join(label_parts))

    return labels


def _filter_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Select the tests that ran with a smoothing or reflection filter.

    Rows from settings files are excluded even though most of those settings
    enable filters. They are reported on their own, and there can be enough
    of them to bury the handful of rows that measure what a filter costs.

    Args:
        df: DataFrame with benchmark results.

    Returns:
        The subset of `df` whose settings name a filter.
    """
    return df[
        (df["test_category"] != "capture_preset")
        & df["settings"].str.contains("Filter|Gaussian|Reflection", case=False, na=False)
    ]


def categorize_tests(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Categorize tests into different analysis groups.

    Args:
        df: DataFrame with benchmark results, expected to contain
            "test_category", "test_name", and "settings" columns.

    Returns:
        A dict mapping category names to the subset of `df` belonging to
        that category. Categories with no matching rows are omitted.
    """
    categories = {
        "Connection time": df[df["test_category"] == "connect"],
        "2D or 3D Capture": df[df["test_category"].isin(["capture_2d", "capture_3d"])],
        "File System": df[df["test_category"].isin(["save_data", "copy_data"])],
        "Filters": _filter_tests(df),
        "Settings files": df[df["test_category"] == "capture_preset"],
        "2D and 3D Capture": df[df["test_category"].isin(["capture_2d3d", "capture_3d2d"])],
        "Advanced 2D+3D analysis": df[
            df["test_name"].str.contains("projector|including|followed|first.*then", case=False, na=False)
        ],
    }

    # Remove empty categories
    categories = {k: v for k, v in categories.items() if not v.empty}
    return categories


def plot_category_comparison(data: pd.DataFrame, title: str, ax: Axes) -> None:
    """Create a bar plot comparing median and mean times for a category.

    Args:
        data: DataFrame with the category's benchmark results, expected to
            contain "test_name", "median_ms", and "mean_ms" columns.
        title: Title to use for the plot.
        ax: Matplotlib axes to draw the plot on.
    """
    if data.empty:
        _draw_no_data_placeholder(ax, "No data available", title)
        return

    grouped = data.groupby("test_name").agg({"median_ms": ["mean", "std"], "mean_ms": ["mean", "std"]}).round(2)
    grouped.columns = ["_".join(col).strip() for col in grouped.columns]

    test_names = grouped.index
    x_pos = np.arange(len(test_names))

    median_means = grouped["median_ms_mean"]
    median_stds = grouped["median_ms_std"].fillna(0)
    mean_means = grouped["mean_ms_mean"]
    mean_stds = grouped["mean_ms_std"].fillna(0)

    width = 0.35
    ax.bar(
        x_pos - width / 2,
        median_means,
        width,
        yerr=median_stds,
        label="Median Time",
        alpha=0.8,
        capsize=5,
        color=ZIVID_COLORS["secondary_teal"],
    )
    ax.bar(
        x_pos + width / 2,
        mean_means,
        width,
        yerr=mean_stds,
        label="Mean Time",
        alpha=0.8,
        capsize=5,
        color=ZIVID_COLORS["secondary_blue"],
    )

    ax.set_title(title, fontsize=14, fontweight="bold", color=ZIVID_COLORS["primary_blue"])
    ax.set_ylabel("Time (ms)", color=ZIVID_COLORS["primary_dark"])
    ax.set_xticks(x_pos)
    ax.set_xticklabels([name.replace("  ", "") for name in test_names], rotation=45, ha="right")

    _maybe_log_scale(ax, list(pd.concat([median_means, mean_means])), "y", "Time (ms)")

    _style_legend(ax)
    ax.grid(True, alpha=0.3)


def plot_time_series(data: pd.DataFrame, title: str, ax: Axes) -> None:
    """Create a time series plot showing performance over time.

    Args:
        data: DataFrame with the category's benchmark results, expected to
            contain "test_name", "timestamp", and "median_ms" columns.
        title: Title to use for the plot.
        ax: Matplotlib axes to draw the plot on.
    """
    if data.empty:
        _draw_no_data_placeholder(ax, "No data available", title + " - Time Series")
        return

    for i, test_name in enumerate(data["test_name"].unique()):
        test_data = data[data["test_name"] == test_name].sort_values("timestamp")
        color = ZIVID_PALETTE[i % len(ZIVID_PALETTE)]
        ax.plot(
            test_data["timestamp"],
            test_data["median_ms"],
            marker="o",
            label=test_name.replace("  ", ""),
            alpha=0.8,
            color=color,
            linewidth=2,
        )

    ax.set_title(title + " - Performance Over Time", fontsize=14, fontweight="bold", color=ZIVID_COLORS["primary_blue"])
    ax.set_xlabel("Timestamp", color=ZIVID_COLORS["primary_dark"])
    ax.set_ylabel("Median Time (ms)", color=ZIVID_COLORS["primary_dark"])

    _style_legend(ax, bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)


def plot_settings_analysis(data: pd.DataFrame, title: str, ax: Axes) -> None:
    """Analyze performance by settings when available.

    Args:
        data: DataFrame with the category's benchmark results, expected to
            contain "test_category", "settings", and "median_ms" columns.
        title: Title to use for the plot.
        ax: Matplotlib axes to draw the plot on.
    """
    has_settings_column = not data.empty and "settings" in data.columns
    settings_data = (
        data[(data["test_category"] != "system_info") & (data["settings"].notna()) & (data["settings"] != "")]
        if has_settings_column
        else data.iloc[0:0]
    )

    if settings_data.empty:
        _draw_no_data_placeholder(ax, "No settings data available", title + " - Settings Analysis")
        return

    settings_grouped = settings_data.groupby("settings")["median_ms"].mean().sort_values()

    if len(settings_grouped) > 10:  # Limit to top 10 for readability
        settings_grouped = settings_grouped.tail(10)

    y_pos = np.arange(len(settings_grouped))
    ax.barh(y_pos, settings_grouped.values, alpha=0.8, color=ZIVID_COLORS["secondary_teal"])
    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        [s[:50] + "..." if len(s) > 50 else s for s in settings_grouped.index], color=ZIVID_COLORS["primary_dark"]
    )
    ax.set_xlabel("Median Time (ms)", color=ZIVID_COLORS["primary_dark"])
    ax.set_title(
        title + " - Performance by Settings", fontsize=14, fontweight="bold", color=ZIVID_COLORS["primary_blue"]
    )

    _maybe_log_scale(ax, list(settings_grouped), "x", "Median Time (ms)")

    ax.grid(True, alpha=0.3)


def plot_settings_file_comparison(datasets: List[Dict[str, Any]], labels: List[str], ax: Axes) -> None:
    """Compare total 3D capture time per settings file across systems.

    One group per settings file, one bar per system, so a difference is
    read per setting rather than averaged into a single capture number.

    Args:
        datasets: List of dataset dicts as produced by load_multiple_datasets.
        labels: Label strings, one per dataset.
        ax: Matplotlib axes to draw on.
    """
    per_dataset = [settings_file_results(dataset["data"]) for dataset in datasets]

    names: List[str] = []
    for frame in per_dataset:
        for name in frame.index:
            if name not in names:
                names.append(str(name))
    if not names:
        _draw_no_data_placeholder(
            ax, "No runs used --presets, so there are no settings files to compare", "Settings files"
        )
        return

    slowest = max(
        (float(frame.loc[name, "total"]) for frame in per_dataset for name in names if name in frame.index),
        default=0.0,
    )
    ordered = sorted(
        names,
        key=lambda name: min(
            (float(frame.loc[name, "total"]) for frame in per_dataset if name in frame.index), default=slowest
        ),
    )

    positions = np.arange(len(ordered))
    height = 0.8 / len(datasets)
    for index, (frame, label) in enumerate(zip(per_dataset, labels)):  # noqa: B905
        totals = [float(frame.loc[name, "total"]) if name in frame.index else 0.0 for name in ordered]
        ax.barh(
            positions + (index - len(datasets) / 2 + 0.5) * height,
            totals,
            height,
            label=label,
            color=ZIVID_PALETTE[index % len(ZIVID_PALETTE)],
        )

    ax.set_yticks(positions)
    ax.set_yticklabels(_without_shared_prefix(ordered))
    ax.invert_yaxis()
    ax.set_xlabel("Total 3D capture time (ms)", color=ZIVID_COLORS["primary_dark"])
    ax.set_title(
        "Settings files, per system",
        color=ZIVID_COLORS["primary_blue"],
        fontweight="bold",
        fontsize=15,
    )
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    _style_legend(ax, loc="upper right")


def plot_comparison_analysis(datasets: List[Dict[str, Any]], labels: List[str], title: str, ax: Axes) -> None:
    """Create a comparison plot across multiple datasets.

    Args:
        datasets: List of dataset dicts, each containing a "data" DataFrame
            with benchmark results for one dataset.
        labels: List of label strings, one per dataset, used for the legend.
        title: Title to use for the plot.
        ax: Matplotlib axes to draw the plot on.
    """
    if not datasets:
        _draw_no_data_placeholder(ax, "No data available", title)
        return

    per_dataset = [
        _median_by_test(dataset["data"][dataset["data"]["test_category"] != "system_info"]) for dataset in datasets
    ]

    all_test_names = []
    for medians in per_dataset:
        for name in medians.index:
            if name not in all_test_names:
                all_test_names.append(name)

    comparison_data = {}
    for test_name in all_test_names:
        comparison_data[test_name] = [float(medians.get(test_name, 0)) for medians in per_dataset]

    comparison_data = {k: v for k, v in comparison_data.items() if any(val > 0 for val in v)}

    if not comparison_data:
        _draw_no_data_placeholder(ax, "No comparable tests found", title)
        return

    test_names = list(comparison_data.keys())
    x_pos = np.arange(len(test_names))

    n_datasets = len(datasets)
    width = 0.8 / n_datasets

    for i, (dataset, label) in enumerate(zip(datasets, labels)):  # noqa: B905
        values = [comparison_data[test_name][i] for test_name in test_names]
        color = ZIVID_PALETTE[i % len(ZIVID_PALETTE)]

        ax.bar(
            x_pos + (i - n_datasets / 2 + 0.5) * width,
            values,
            width,
            label=label,
            alpha=0.8,
            color=color,
        )

    ax.set_title(title, fontsize=14, fontweight="bold", color=ZIVID_COLORS["primary_blue"])
    ax.set_ylabel("Median Time (ms)", color=ZIVID_COLORS["primary_dark"])
    ax.set_xticks(x_pos)
    ax.set_xticklabels([name.replace("  ", "") for name in test_names], rotation=45, ha="right")

    _maybe_log_scale(ax, [value for values in comparison_data.values() for value in values], "y", "Median Time (ms)")

    _style_legend(ax)
    ax.grid(True, alpha=0.3)


def _platform_table_value(key: str, platform_info: Dict[str, str]) -> str:
    """Format a single platform info value for the platform table.

    Args:
        key: The platform info key to look up.
        platform_info: The dataset's platform info mapping.

    Returns:
        The wrapped value for the table cell, or "-" if the key is missing.
    """
    if key not in platform_info:
        return "-"

    return textwrap.fill(platform_info[key], width=30)


def _draw_platform_table(table_ax: Axes, datasets: List[Dict[str, Any]], labels: List[str]) -> None:
    """Draw the platform information table comparing the datasets' systems.

    Args:
        table_ax: Matplotlib axes to draw the table on.
        datasets: List of dataset dicts as produced by load_multiple_datasets.
        labels: List of label strings, one per dataset, used as column headers.
    """
    table_ax.axis("off")

    key_display_names = {
        "OS": "OS",
        "Camera_Model": "Camera Model",
        "API_Version": "API Version",
        "Compute_Device_Model": "GPU",
    }

    table_data = [
        [display_name] + [_platform_table_value(key, dataset["platform"]) for dataset in datasets]
        for key, display_name in key_display_names.items()
    ]

    param_col_width = 0.25
    data_col_width = (1.0 - param_col_width) / len(datasets)

    table = table_ax.table(
        cellText=table_data,
        colLabels=[""] + labels,
        cellLoc="left",
        colLoc="left",
        loc="center",
        colWidths=[param_col_width] + [data_col_width] * len(datasets),
    )
    table.set_fontsize(16)
    table.scale(1, 3)

    for (row_index, _), cell in table.get_celld().items():  # pylint: disable=unused-variable
        cell.set_edgecolor(ZIVID_COLORS["primary_blue"])
        cell.set_facecolor("white")
        cell.get_text().set_color(ZIVID_COLORS["primary_dark"])
        # Header row in matplotlib tables uses row index -1
        if row_index == -1:
            cell.get_text().set_fontweight("bold")
            cell.set_facecolor(ZIVID_COLORS["secondary_teal"])
            cell.set_alpha(0.12)


def settings_file_results(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape the ``--presets`` rows into one row per settings file.

    The benchmark writes one row per settings file and measurement, named
    ``<file> acquisition``, ``<file> processing`` and ``<file> total``.
    Older CSVs, written before the split, hold only a total under the bare
    file name.

    Args:
        df: DataFrame with benchmark results.

    Returns:
        A DataFrame indexed by settings file name with an ``acquisition``,
        ``processing`` and ``total`` column, sorted fastest first. Columns
        the CSV does not carry hold NaN. Empty if the run used no settings
        files.
    """
    rows = df[df["test_category"] == "capture_preset"]
    if rows.empty:
        return pd.DataFrame()

    measurements: Dict[str, Dict[str, float]] = {}
    for row in rows.to_dict("records"):
        name = str(row["test_name"]).strip()
        measurement = "total"
        for candidate in ("acquisition", "processing", "total"):
            if name.endswith(f" {candidate}"):
                measurement = candidate
                name = name[: -len(candidate) - 1].strip()
                break
        measurements.setdefault(name, {})[measurement] = float(row["median_ms"])
        if measurement == "total" and "stddev_ms" in row and bool(pd.notna(row["stddev_ms"])):
            measurements[name]["stddev"] = float(row["stddev_ms"])

    frame = pd.DataFrame.from_dict(measurements, orient="index")
    for column in ("acquisition", "processing", "total", "stddev"):
        if column not in frame.columns:
            frame[column] = np.nan
    frame["total"] = frame["total"].fillna(frame["acquisition"] + frame["processing"])
    return frame.sort_values("total")


def _without_shared_prefix(names: List[str]) -> List[str]:
    """Drop the leading text every settings file name has in common.

    The presets installed with the sample data are all named after the
    camera model, so without this every row of the chart repeats it.

    Args:
        names: The settings file names, without extension.

    Returns:
        The names with the shared prefix removed, or unchanged when they
        share nothing or when removing it would empty one of them.
    """
    if len(names) < 2:
        return names
    shared = os.path.commonprefix(names)
    shared = shared[: shared.rfind("_") + 1]
    if not shared or any(len(name) == len(shared) for name in names):
        return names
    return [name[len(shared) :] for name in names]


def plot_settings_files(frame: pd.DataFrame, ax: Axes) -> None:
    """Plot total 3D capture time per settings file, split by where it is spent.

    Args:
        frame: DataFrame as returned by settings_file_results.
        ax: Matplotlib axes to draw on.
    """
    frame = frame.iloc[::-1]
    positions = np.arange(len(frame))
    has_split = bool(frame["acquisition"].notna().all() and frame["processing"].notna().all())

    if has_split:
        ax.barh(
            positions,
            frame["acquisition"],
            color=ZIVID_COLORS["secondary_blue"],
            label="Camera acquisition",
        )
        ax.barh(
            positions,
            frame["processing"],
            left=frame["acquisition"],
            color=ZIVID_COLORS["secondary_teal"],
            label="Processing on this PC",
        )
        _style_legend(ax, loc="upper right")
    else:
        ax.barh(positions, frame["total"], color=ZIVID_COLORS["secondary_blue"], label="Total 3D capture")

    spread = frame["stddev"]
    if bool(spread.notna().any()):
        ax.errorbar(
            frame["total"],
            positions,
            xerr=spread.fillna(0),
            fmt="none",
            ecolor=ZIVID_COLORS["primary_dark"],
            elinewidth=1.2,
            capsize=4,
            label="Standard deviation over repetitions",
        )
        _style_legend(ax, loc="upper right")

    limit = float((frame["total"] + spread.fillna(0)).max())
    for position, (total, deviation) in enumerate(zip(frame["total"], spread.fillna(0))):  # noqa: B905
        ax.text(total + deviation + limit * 0.012, position, f"{total:,.0f} ms", va="center", fontsize=10)

    ax.set_yticks(positions)
    ax.set_yticklabels(_without_shared_prefix([str(stem) for stem in frame.index]))
    ax.set_xlim(0, limit * 1.12)
    ax.set_xlabel("Total 3D capture time (ms)", color=ZIVID_COLORS["primary_dark"])
    ax.set_title(
        "Your settings, fastest first",
        color=ZIVID_COLORS["primary_blue"],
        fontweight="bold",
        fontsize=15,
    )
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)


def _median_by_test(data: pd.DataFrame) -> pd.Series:
    """Median time per measurement, slowest last.

    A test name on its own is not unique: the benchmark measures 3D capture
    several times over, once per acquisition count and filter combination.
    Grouping by name alone would average those separate configurations into
    one meaningless bar, so the settings are part of the key and only
    collapse when they are genuinely identical.

    Args:
        data: DataFrame with "test_name", "settings" and "median_ms" columns.

    Returns:
        A Series indexed by measurement label holding the median time in
        milliseconds.
    """
    summary = data.groupby(["test_name", "settings"], dropna=False)["median_ms"].median().reset_index()
    summary["configurations"] = summary.groupby("test_name")["settings"].transform("size")
    labels = []
    medians = []
    for row in summary.to_dict("records"):
        name = str(row["test_name"]).strip().rstrip(":")
        hint = _settings_hint(row["settings"])
        labels.append(name if row["configurations"] == 1 or not hint else f"{name} [{hint}]")
        medians.append(float(row["median_ms"]))
    return pd.Series(medians, index=pd.Index(labels)).sort_values()


def _settings_hint(settings: Union[str, float]) -> str:
    """Summarize a settings string as the acquisition count and filters.

    Args:
        settings: The "settings" value recorded alongside a measurement, a
            string, or NaN when the CSV cell is empty.

    Returns:
        A short label such as "3 acq, Gaussian and Reflection", or "" when
        the settings were not recorded.
    """
    if not isinstance(settings, str) or not settings:
        return ""
    acquisitions = settings.count(",") + 1 if "Exposure:" in settings else 0
    exposures = settings.split("Exposure:")[-1].split(";")[0] if "Exposure:" in settings else ""
    acquisitions = len([value for value in exposures.split(",") if value.strip()]) or acquisitions
    hint = f"{acquisitions} acq" if acquisitions else ""
    if "Filters:" in settings:
        filters = settings.split("Filters:")[-1].strip()
        hint = f"{hint}, {filters}" if hint else filters
    return hint


def _plot_horizontal_medians(data: pd.DataFrame, title: str, ax: Axes, log_scale: bool = False) -> None:
    """Draw one median bar per test name.

    Args:
        data: DataFrame with "test_name" and "median_ms" columns.
        title: Panel title.
        ax: Matplotlib axes to draw on.
        log_scale: Whether to use a logarithmic time axis, for panels
            whose values span orders of magnitude.
    """
    if data.empty:
        _draw_no_data_placeholder(ax, "Not measured in this run", title)
        return

    medians = _median_by_test(data)
    positions = np.arange(len(medians))
    ax.barh(positions, medians, color=ZIVID_COLORS["secondary_blue"])
    ax.set_yticks(positions)
    ax.set_yticklabels(list(medians.index), fontsize=9)
    if log_scale:
        ax.set_xscale("log")
        ax.set_xlabel("Median time (ms) - log scale", color=ZIVID_COLORS["primary_dark"])
    else:
        for position, value in enumerate(medians):
            ax.text(value + float(medians.max()) * 0.02, position, f"{value:,.1f}", va="center", fontsize=9)
        ax.set_xlim(0, float(medians.max()) * 1.18)
        ax.set_xlabel("Median time (ms)", color=ZIVID_COLORS["primary_dark"])
    ax.set_title(title, color=ZIVID_COLORS["primary_blue"], fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)


def plot_capture_breakdown(df: pd.DataFrame, ax: Axes) -> None:
    """Plot where the time goes for the benchmark's own capture settings.

    Args:
        df: DataFrame with benchmark results.
        ax: Matplotlib axes to draw on.
    """
    captures = df[df["test_category"].isin(["capture_2d", "capture_3d", "capture_2d3d", "capture_3d2d"])]
    _plot_horizontal_medians(captures, "Where a capture spends its time", ax)


def plot_connect_and_capture(df: pd.DataFrame, ax: Axes) -> None:
    """Plot the measurements the settings chart does not already cover.

    The settings chart shows 3D acquisition against processing for every
    settings file, so repeating the benchmark's own 3D numbers here would say
    the same thing twice. What is left is connecting, 2D capture, and the
    combined 2D+3D orderings.

    Args:
        df: DataFrame with benchmark results.
        ax: Matplotlib axes to draw on.
    """
    other = df[df["test_category"].isin(["connect", "capture_2d", "capture_2d3d", "capture_3d2d"])]
    _plot_horizontal_medians(other, "Connecting and 2D capture", ax, log_scale=True)


def plot_data_handling(df: pd.DataFrame, ax: Axes) -> None:
    """Plot the cost of copying point cloud data out and saving it to disk.

    Args:
        df: DataFrame with benchmark results.
        ax: Matplotlib axes to draw on.
    """
    handling = df[df["test_category"].isin(["copy_data", "save_data"])]
    _plot_horizontal_medians(handling, "Copying and saving data", ax, log_scale=True)


def _draw_system_summary(ax: Axes, datasets: List[Dict[str, Any]], labels: List[str]) -> None:
    """Draw the system configuration as one compact row of text.

    Args:
        ax: Matplotlib axes to draw on.
        datasets: List of dataset dicts as produced by load_multiple_datasets.
        labels: Label strings, one per dataset.
    """
    ax.axis("off")
    platform_info = datasets[0]["platform"]
    fields = [
        _platform_table_value(key, platform_info)
        for key in ("Camera_Model", "Compute_Device_Model", "API_Version", "OS")
        if _platform_table_value(key, platform_info) != "-"
    ]
    ax.text(
        0.5,
        0.55,
        "   ·   ".join(fields),
        ha="center",
        va="center",
        fontsize=13,
        color=ZIVID_COLORS["primary_dark"],
    )
    ax.text(
        0.5,
        0.05,
        labels[0],
        ha="center",
        va="center",
        fontsize=10,
        color=ZIVID_COLORS["secondary_blue"],
    )


def create_single_system_overview(dataset: Dict[str, Any], label: str) -> Figure:
    """Create the overview report for one benchmark run.

    Args:
        dataset: Dataset dict as produced by load_multiple_datasets.
        label: Label describing the run, shown under the system summary.

    Returns:
        The created matplotlib Figure.

    Raises:
        ValueError: If the dataset holds no benchmark measurements.
    """
    df = dataset["data"]
    if df[df["test_category"] != "system_info"].empty:
        raise ValueError(
            f"{dataset['file']} contains system information but no benchmark measurements. "
            f"This is what an interrupted ZividBenchmark run leaves behind - re-run the benchmark, "
            f"or use --summary-only to inspect the file without plotting."
        )

    settings_files = settings_file_results(df)
    measured_settings_files = not settings_files.empty
    supporting_panels = 2
    fig = plt.figure(figsize=(18, 15 if measured_settings_files else 11))
    grid = fig.add_gridspec(
        3,
        supporting_panels,
        height_ratios=[0.06, 1.05, 0.80],
        hspace=0.30,
        wspace=0.32,
        left=0.09,
        right=0.97,
        top=0.94,
        bottom=0.06,
    )

    _draw_system_summary(fig.add_subplot(grid[0, :]), [dataset], [label])

    hero = fig.add_subplot(grid[1, :])
    if measured_settings_files:
        plot_settings_files(settings_files, hero)
        plot_connect_and_capture(df, fig.add_subplot(grid[2, 0]))
        plot_data_handling(df, fig.add_subplot(grid[2, 1]))
    else:
        plot_capture_breakdown(df, hero)
        hero.set_title(
            "Where a capture spends its time",
            color=ZIVID_COLORS["primary_blue"],
            fontweight="bold",
            fontsize=15,
        )
        plot_connect_and_capture(df, fig.add_subplot(grid[2, 0]))
        plot_data_handling(df, fig.add_subplot(grid[2, 1]))

    fig.suptitle(
        "Zivid Benchmark - Capture Performance On This System",
        fontsize=17,
        fontweight="bold",
        color=ZIVID_COLORS["primary_blue"],
    )
    return fig


def create_platform_comparison_visualization(datasets: List[Dict[str, Any]], labels: List[str]) -> Optional[Figure]:
    """Create the comparison report for two or more benchmark runs.

    A single run is reported by create_single_system_overview instead.

    Args:
        datasets: List of dataset dicts as produced by
            load_multiple_datasets.
        labels: List of label strings, one per dataset, used for the
            platform info table columns and plot legends.

    Returns:
        The created matplotlib Figure, or None if `datasets` is empty.
    """
    if not datasets:
        print("No datasets available for visualization.")
        return None

    n_rows = 2
    n_cols = 3

    # Create figure with space for platform info table
    fig = plt.figure(figsize=(24, 14))

    # Create grid: platform table (left), plots (right)
    width_ratios = [1.4] + [1.3] * n_cols
    gs = fig.add_gridspec(n_rows, n_cols + 1, width_ratios=width_ratios, hspace=0.45, wspace=0.3, left=0.05, right=0.97)

    # Platform information table
    table_ax = fig.add_subplot(gs[:, 0])
    _draw_platform_table(table_ax, datasets, labels)

    settings_ax = fig.add_subplot(gs[0, 1:])
    plot_settings_file_comparison(datasets, labels, settings_ax)

    categories_to_compare = [
        ("capture_2d", "2D Capture Performance"),
        ("connect", "Connection Performance"),
        ("save_data", "Save Performance"),
    ]

    for i, (category, title) in enumerate(categories_to_compare):
        ax = fig.add_subplot(gs[1, i + 1])

        category_datasets = []
        for dataset in datasets:
            category_data = dataset["data"][dataset["data"]["test_category"] == category]
            if not category_data.empty:
                category_datasets.append({"data": category_data, "platform": dataset["platform"]})

        if category_datasets:
            plot_comparison_analysis(category_datasets, labels[: len(category_datasets)], title, ax)
        else:
            _draw_no_data_placeholder(ax, f"No {category} data available", title)

    fig.suptitle(
        "Zivid Benchmark Platform Comparison",
        fontsize=16,
        fontweight="bold",
        color=ZIVID_COLORS["primary_blue"],
        y=0.95,
    )

    return fig


def create_detailed_analysis(df: pd.DataFrame) -> int:
    """Create detailed analysis with multiple plot types for each category.

    Args:
        df: DataFrame with benchmark results to analyze.

    Returns:
        The number of categories for which detailed analysis plots were
        created (and saved to PNG files).
    """
    categories = categorize_tests(df)

    for category_name, category_data in categories.items():
        if category_data.empty:
            continue

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(
            f"Detailed Analysis: {category_name}", fontsize=16, fontweight="bold", color=ZIVID_COLORS["primary_blue"]
        )

        # Performance comparison
        plot_category_comparison(category_data, f"{category_name} - Performance", axes[0, 0])

        # Time series
        plot_time_series(category_data, category_name, axes[0, 1])

        # Settings analysis
        plot_settings_analysis(category_data, category_name, axes[1, 0])

        # Camera model comparison if available
        if "camera_model" in category_data.columns and len(category_data["camera_model"].unique()) > 1:
            camera_grouped = (
                category_data.groupby(["camera_model", "test_name"])["median_ms"].mean().unstack(fill_value=0)
            )
            sns.heatmap(
                camera_grouped,
                annot=True,
                fmt=".1f",
                ax=axes[1, 1],
                cmap="Blues",
                cbar_kws={"label": "Median Time (ms)"},
            )
            axes[1, 1].set_title(
                f"{category_name} - Camera Model Comparison", color=ZIVID_COLORS["primary_blue"], fontweight="bold"
            )
        else:
            # Distribution plot
            if not category_data.empty:
                boxplot_artists = category_data.boxplot(
                    column="median_ms", by="test_name", ax=axes[1, 1], patch_artist=True, return_type="dict"
                )
                for patch in boxplot_artists["median_ms"]["boxes"]:
                    patch.set_facecolor(ZIVID_COLORS["secondary_teal"])
                    patch.set_alpha(0.7)
                axes[1, 1].set_title(
                    f"{category_name} - Time Distribution", color=ZIVID_COLORS["primary_blue"], fontweight="bold"
                )
                axes[1, 1].set_ylabel("Median Time (ms)", color=ZIVID_COLORS["primary_dark"])
                axes[1, 1].set_xlabel("")
                # Tilt x tick labels for readability
                for label in axes[1, 1].get_xticklabels():
                    label.set_rotation(45)
                    label.set_ha("right")

                # Boxplot with 'by' parameter adds automatic suptitle, so we need to restore our custom one
                fig.suptitle(
                    f"Detailed Analysis: {category_name}",
                    fontsize=16,
                    fontweight="bold",
                    color=ZIVID_COLORS["primary_blue"],
                )

        plt.tight_layout()

        # Save individual category plots
        plt.savefig(
            f'benchmark_analysis_{category_name.lower().replace(" ", "_").replace("+", "plus")}.png',
            dpi=300,
            bbox_inches="tight",
        )

    return len(categories)


def print_category_analysis(df: pd.DataFrame) -> None:
    """Print the analysis categories and detected filters for one dataset.

    Args:
        df: DataFrame with benchmark results to summarize.
    """
    categories = categorize_tests(df)
    print("\n  Analysis Categories Found:")
    for category_name, category_data in categories.items():
        print(f"    {category_name}: {len(category_data)} tests")

    filter_tests = _filter_tests(df)
    if filter_tests.empty:
        return

    print("\n  Filter Analysis:")
    unique_filters = set()
    for settings in filter_tests["settings"]:
        if "Gaussian" in settings:
            unique_filters.add("Gaussian")
        if "Reflection" in settings:
            unique_filters.add("Reflection")
    print(f"    Filter types detected: {', '.join(unique_filters)}")
    print(f"    Tests with filters: {len(filter_tests)}")


def _main() -> None:
    parser = argparse.ArgumentParser(description="Visualize Zivid benchmark results")
    parser.add_argument("csv_files", nargs="*", type=Path, help="Path(s) to CSV file(s) with benchmark results")
    parser.add_argument("--summary-only", action="store_true", help="Only show summary statistics")
    parser.add_argument("--detailed", action="store_true", help="Create detailed analysis plots")

    args = parser.parse_args()

    csv_files = args.csv_files
    if not csv_files:
        discovered_files = list(Path(".").glob("zivid_benchmark_results*.csv"))
        if not discovered_files:
            print("No benchmark CSV files found. Please specify file(s) or run ZividBenchmark first.")
            return
        csv_files = [max(discovered_files, key=lambda f: f.stat().st_mtime)]
        print(f"Using most recent benchmark file: {csv_files[0]}")

    # Load datasets (works for both single and multiple files)
    print(f"Loading {len(csv_files)} dataset(s)...")
    datasets = load_multiple_datasets(csv_files)

    # Generate labels
    labels = generate_comparison_labels(datasets)

    # Print summary
    print("\n" + "=" * 60)
    if len(datasets) > 1:
        print("BENCHMARK COMPARISON SUMMARY")
    else:
        print("BENCHMARK RESULTS SUMMARY")
    print("=" * 60)

    for i, (dataset, label) in enumerate(zip(datasets, labels)):  # noqa: B905
        if len(datasets) > 1:
            print(f"\nDataset {i + 1}: {label}")
        print(f"  File: {Path(dataset['file']).name}")
        print_sdk_log_files(dataset["platform"])

        # Print detailed statistics
        df = dataset["data"]
        test_data = df[df["test_category"] != "system_info"]

        if not test_data.empty:
            print(f"  Total tests: {len(test_data)}")
            print(f"  Test categories: {', '.join(test_data['test_category'].unique())}")
            print(f"  Time range: {test_data['timestamp'].min()} to {test_data['timestamp'].max()}")
            print(f"  Avg time: {test_data['median_ms'].mean():.2f} ms")
            print(
                f"  Fastest test: {test_data.loc[test_data['median_ms'].idxmin(), 'test_name']} ({test_data['median_ms'].min():.2f} ms)"
            )
            print(
                f"  Slowest test: {test_data.loc[test_data['median_ms'].idxmax(), 'test_name']} ({test_data['median_ms'].max():.2f} ms)"
            )

        # Category analysis for first dataset only (to avoid repetition)
        if i == 0:
            print_category_analysis(df)

    if args.summary_only:
        return

    # Create visualizations
    print("\nCreating visualization...")
    if len(datasets) == 1:
        vis_fig = create_single_system_overview(datasets[0], labels[0])
    else:
        vis_fig = create_platform_comparison_visualization(datasets, labels)

    if vis_fig:
        # Save with appropriate filename
        if len(datasets) > 1:
            filename = "benchmark_comparison.png"
        else:
            filename = "benchmark_overview.png"
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        print(f"Saved: {filename}")

    # Detailed analysis if requested (only for single file)
    if args.detailed and len(datasets) == 1:
        n_categories = create_detailed_analysis(datasets[0]["data"])
        print(f"Created detailed analysis for {n_categories} categories.")

    # Show plots
    plt.show()


if __name__ == "__main__":
    _main()
