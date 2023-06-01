import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd


def _options() -> argparse.Namespace:
    """Function to read user arguments


    Returns:
        Argument from user

    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--csv-path",
        required=False,
        type=Path,
        default=Path(__file__).parent / "verification_data.csv",
        help="Path to the verification data",
    )

    return parser.parse_args()


def _main():
    user_input = _options()

    df = pd.read_csv(user_input.csv_path, parse_dates=["time"], comment="#")
    temperature_labels = [label for label in df.columns if label.startswith("temperature.")]

    fig, axes = plt.subplots(2, 2, figsize=(16, 8), sharex=True)
    temperature_axes = [axes[0,0], axes[0,1], axes[1,1]]
    axes[1,0].axis("off")
    ax_dim_trueness = axes[0,0].twinx()
    ax_position_drift = axes[0,1].twinx()

    # Plot temperature variables
    for column in temperature_labels:
        label = label=column.replace("temperature.","")
        axes[1,1].plot(df["time"], df[column], label=label, linestyle='dashed')
        if "DMD" in label:
            axes[0,0].plot(df["time"], df[column], label=label, linestyle='dashed')
            axes[0,1].plot(df["time"], df[column], label=label, linestyle='dashed')

    # Plot dimension_trueness
    ax_dim_trueness.plot(df["time"], df["dimension_trueness"] * 100, "+-r", label="dimension_trueness")
    ax_dim_trueness.set_ylim([0, max(df["dimension_trueness"].max() * 100, 0.1)])

    # Plot position drift
    for label in ['x', 'y', 'z']:
        ax_position_drift.plot(df["time"], df[f"position.{label}"] - df[f"position.{label}"][0], label=label)

    # Set labels and title
    for ax, title in zip(temperature_axes, ["Dimension Trueness", "Positional Drift", "All Temperatures"]):
        ax.set_xlabel("Time")
        ax.set_ylabel("\u00b0C", rotation=0)
        ax.set_title(title)
    formatter = ticker.FuncFormatter(lambda x, _: f"{x:.2f}%")
    ax_dim_trueness.yaxis.set_major_formatter(formatter)
    ax_dim_trueness.set_ylabel("Dimension Trueness")
    formatter = ticker.FuncFormatter(lambda x, _: f"{x:.2f}")
    ax_position_drift.yaxis.set_major_formatter(formatter)
    ax_position_drift.set_ylabel("mm", rotation=0)

    # Display legend
    for ax in temperature_axes:
        ax.legend(loc="center left")
    ax_position_drift.legend(loc="center right")

    # Display meta data
    meta_data = "\n".join([line for line in Path(user_input.csv_path).read_text(encoding="utf-8").splitlines() if line.startswith("#")])
    fig.text(0.05, 0.25, meta_data, ha='left', va='center', fontsize=12, transform=fig.transFigure)

    # Show the plot
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    _main()
