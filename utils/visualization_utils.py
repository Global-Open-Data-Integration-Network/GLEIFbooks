import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import math


class Visualizations:
    """
    Creates visulizations for LEI data

    - Creates a stacked bar chart using matplotlib for better control over stacking.
    """

    def create_matplotlib_stacked_chart(by_mapping, level_1_subset, top_n=5):
        """
        Create a stacked bar chart using matplotlib for better control over stacking.
        """

        # Find the jurisdiction column name
        jurisdiction_col = None
        for col in level_1_subset.columns:
            if "LegalJurisdiction" in col:
                jurisdiction_col = col
                break

        if jurisdiction_col is None:
            raise ValueError("No LegalJurisdiction column found in level_1_subset")

        # Get top N jurisdictions by total mapping pairs
        jurisdiction_counts = {}

        # Merge each mapping with level_1 data and count by jurisdiction
        for mapping_name, mapping_df in by_mapping.items():
            merged = pd.merge(level_1_subset, mapping_df, on="LEI", how="inner")
            jurisdiction_counts[mapping_name] = merged[jurisdiction_col].value_counts()

        # Get top N jurisdictions
        all_jurisdictions = set()
        for counts in jurisdiction_counts.values():
            all_jurisdictions.update(counts.index)

        total_counts = {}
        for jurisdiction in all_jurisdictions:
            total = sum(
                counts.get(jurisdiction, 0) for counts in jurisdiction_counts.values()
            )
            total_counts[jurisdiction] = total

        top_jurisdictions = sorted(
            total_counts.items(), key=lambda x: x[1], reverse=True
        )[:top_n]
        top_jurisdiction_names = [j[0] for j in top_jurisdictions]

        # Prepare data for stacking
        mapping_types = list(by_mapping.keys())
        mapping_labels = [
            mapping.replace("-lei", "").upper() for mapping in mapping_types
        ]

        # Create data matrix for stacking
        data_matrix = []
        for jurisdiction in top_jurisdiction_names:
            row = []
            for mapping_name in mapping_types:
                count = jurisdiction_counts[mapping_name].get(jurisdiction, 0)
                row.append(count)
            data_matrix.append(row)

        data_matrix = np.array(data_matrix)

        # Create the plot with wider figure to accommodate wider bars
        fig, ax = plt.subplots(figsize=(14, 8))

        # Use turquoise color scheme consistent with existing visualizations
        colors = ["#123235", "#79D7C5", "#403E74", "#4D979B", "#4DA2F8"]

        # Create stacked bars
        bottom = np.zeros(len(top_jurisdiction_names))
        bar_width = 0.7

        for i, (mapping_type, label) in enumerate(zip(mapping_types, mapping_labels)):
            values = data_matrix[:, i]
            ax.bar(
                top_jurisdiction_names,
                values,
                bottom=bottom,
                label=label,
                color=colors[i % len(colors)],
                alpha=1.0,
                width=bar_width,
            )

            # Add value labels on significant segments
            for j, (jurisdiction, value) in enumerate(
                zip(top_jurisdiction_names, values)
            ):
                if (
                    value > 0 and value > max(data_matrix.flatten()) * 0.03
                ):  # Only show significant values
                    label_y = bottom[j] + value / 2
                    ax.text(
                        j,
                        label_y,
                        f"{value:,}",
                        ha="center",
                        va="center",
                        fontsize=9,
                        fontweight="bold",
                        color="white"
                        if value > max(data_matrix.flatten()) * 0.08
                        else "black",
                    )

            bottom += values

        # Customize the plot
        ax.set_title(
            "Distribution of Mapping Pairs by Jurisdiction and Mapping Type",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )
        ax.set_xlabel("Legal Jurisdiction", fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of Mapping Pairs", fontsize=12, fontweight="bold")

        # Rotate x-axis labels
        plt.xticks(rotation=45, ha="right")

        # Add some padding to prevent labels from touching borders
        ax.margins(x=0.05, y=0.05)

        # Format y-axis with commas
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))

        # Add legend with controlled order (reverse order to match stacking from bottom to top)
        handles, labels = ax.get_legend_handles_labels()
        # Reverse the order so legend matches stacking order (bottom to top)
        ax.legend(
            handles[::-1],
            labels[::-1],
            title="Mapping Type",
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )

        # Add grid for better readability
        ax.grid(True, alpha=0.3, axis="y")

        # Use tight_layout with padding to ensure proper spacing
        plt.tight_layout(pad=2.0)
        plt.show()

        # Print detailed breakdown
        print("\nDetailed Breakdown by Jurisdiction:")
        print("=" * 60)
        for i, jurisdiction in enumerate(top_jurisdiction_names):
            print(f"\n{jurisdiction}:")
            total_for_jurisdiction = 0
            for j, (mapping_type, label) in enumerate(
                zip(mapping_types, mapping_labels)
            ):
                count = data_matrix[i, j]
                if count > 0:
                    percentage = (count / sum(data_matrix[i, :])) * 100
                    print(f"  {label}: {count:,} ({percentage:.1f}%)")
                    total_for_jurisdiction += count
            print(f"  Total: {total_for_jurisdiction:,}")

        return data_matrix, top_jurisdiction_names, mapping_labels

    def draw_bar_chart_jurisdictions(top20: list[tuple[str, int]], mapping_pairs: str):
        # Plot bar chart
        plt.figure(figsize=(6, 4))
        ax = top20.plot(kind="bar", color="Turquoise")
        plt.title(f"Top 20 Legal Jurisdictions for {mapping_pairs}")
        plt.xlabel("Legal Jurisdiction")
        plt.ylabel("Number of mapping pairs")
        plt.xticks(rotation=45)

        # Format y-axis labels with thousand separators
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f}"))

        plt.tight_layout()
        plt.show()

    def draw_star_map(
        center_label: str, center_value: int, data: list[tuple[str, int]]
    ):
        """
        Draw a simple hub-and-spoke map

        Args:
            center_label: Text label inside the center circle.
            center_value: Number inside the center circle.
            data: - a list of (label, value) tuples.
        """
        leaves = data

        n = len(leaves)
        if n == 0:
            raise ValueError("No leaves provided")

        # Plot setup
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.set_aspect("equal")
        ax.axis("off")

        # Style defaults
        center_circle_color = "#509C9E"
        center_line_color = "#85D4D8"
        leaf_circle_color = "#79D7C5"
        line_color = "dimgray"
        halo_color = "cyan"
        center_radius = 1.5
        leaf_radius = 0.75
        halo_expand = 0.1
        ring_radius = 3.0

        # --- Center node ---
        # Halo (bigger, transparent)
        ax.add_patch(
            Circle(
                (0, 0),
                center_radius + halo_expand,
                facecolor=halo_color,
                alpha=0.2,
                edgecolor="none",
            )
        )
        ax.add_patch(
            Circle(
                (0, 0),
                center_radius,
                facecolor=center_circle_color,
                edgecolor=center_line_color,
                linewidth=2,
            )
        )
        ax.text(
            0,
            0,
            f"{center_label}\n{center_value:,}",
            ha="center",
            va="center",
            fontsize=12,
        )

        # --- Outer nodes ---
        angles = [2 * math.pi * i / n for i in range(n)]
        for (label, value), theta in zip(leaves, angles):
            x, y = ring_radius * math.cos(theta), ring_radius * math.sin(theta)

            # Direction vector
            dx, dy = x, y
            dist = math.hypot(dx, dy)
            dxn, dyn = dx / dist, dy / dist

            # Edge-to-edge line
            x_start, y_start = dxn * center_radius, dyn * center_radius
            x_end, y_end = x - dxn * leaf_radius, y - dyn * leaf_radius
            ax.plot(
                [x_start, x_end],
                [y_start, y_end],
                color=line_color,
                linewidth=1,
                linestyle="--",
            )

            # Halo
            ax.add_patch(
                Circle(
                    (x, y),
                    leaf_radius + halo_expand,
                    facecolor=halo_color,
                    alpha=0.2,
                    edgecolor="none",
                )
            )
            # Leaf circle
            ax.add_patch(
                Circle(
                    (x, y), leaf_radius, facecolor=leaf_circle_color, edgecolor="none"
                )
            )
            ax.text(x, y, f"{label}\n{value:,}", ha="center", va="center", fontsize=10)

        # Adjust limits
        pad = ring_radius + leaf_radius + 0.7
        ax.set_xlim(-pad, pad)
        ax.set_ylim(-pad, pad)

        ax.set_title(
            "Existing Mappings to LEI data", fontsize=12, fontweight="bold", pad=20
        )

        plt.show()
