"""
Plotting Tool for Climate Data Visualization
Allows the model to generate matplotlib plots that are displayed in Streamlit
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Any
import json


def create_plot(
    plot_type: str,
    data: Dict[str, Any],
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    style: Optional[Dict[str, Any]] = None
) -> plt.Figure:
    """
    Create a matplotlib plot based on specifications from the model.

    Args:
        plot_type: Type of plot ("line", "bar", "scatter", "heatmap", "contour")
        data: Dictionary containing plot data:
            - For line/bar/scatter: {"x": [...], "y": [...], "labels": [...] (optional)}
            - For heatmap/contour: {"z": [[...]], "x": [...] (optional), "y": [...] (optional)}
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        style: Optional styling parameters (colors, markers, fonts, axis limits, etc.)

    Returns:
        matplotlib Figure object
    """
    # Create figure with optional custom size
    if style is None:
        style = {}
    figsize = style.get("figsize", [12, 6])
    fig, ax = plt.subplots(figsize=figsize)

    # Font settings from style (used for labels, title, ticks)
    title_fontsize = style.get("title_fontsize", style.get("fontsize", 14))
    title_fontweight = style.get("title_fontweight", style.get("fontweight", "bold"))
    label_fontsize = style.get("label_fontsize", style.get("fontsize", 12))
    label_fontweight = style.get("label_fontweight", style.get("fontweight", "normal"))
    tick_fontsize = style.get("tick_fontsize", style.get("fontsize", None))
    tick_rotation_x = style.get("tick_rotation_x", style.get("xtick_rotation", None))
    tick_rotation_y = style.get("tick_rotation_y", style.get("ytick_rotation", None))
    fontfamily = style.get("fontfamily", None)

    # Get data arrays
    if plot_type in ["line", "bar", "scatter"]:
        # Support multi-series via "series" key, or single series via "x"/"y"
        default_colors = ["steelblue", "orange", "green", "red", "purple",
                          "brown", "pink", "gray", "olive", "cyan"]
        series_list = data.get("series", None)
        if series_list is None:
            # Single-series backward compatibility: wrap into a one-element list
            x = data.get("x", [])
            y = data.get("y", [])
            label = data.get("labels", None)
            if label is None and style.get("legend"):
                metadata = style.get("metadata", {})
                label = metadata.get("variable") or metadata.get("location") or ylabel or "Data"
            series_list = [{"x": x, "y": y, "label": label}]

        num_series = len(series_list)
        for idx, s in enumerate(series_list):
            sx = s.get("x", [])
            sy = s.get("y", [])
            slabel = s.get("label", None)
            scolor = s.get("color", style.get("color", default_colors[idx % len(default_colors)]))

            if plot_type == "line":
                linewidth = s.get("linewidth", style.get("linewidth", 2))
                marker = s.get("marker", style.get("marker", "o"))
                markersize = s.get("markersize", style.get("markersize", 8))
                linestyle = s.get("linestyle", style.get("linestyle", "-"))
                ax.plot(sx, sy, color=scolor, linewidth=linewidth, marker=marker,
                       markersize=markersize, linestyle=linestyle, label=slabel)

            elif plot_type == "bar":
                alpha = s.get("alpha", style.get("alpha", 0.7))
                edgecolor = s.get("edgecolor", style.get("edgecolor", None))
                barwidth = style.get("barwidth", 0.8)
                # Offset bars when multiple series share the same x-axis
                if num_series > 1:
                    bar_w = barwidth / num_series
                    x_indices = np.arange(len(sx))
                    offset = (idx - (num_series - 1) / 2) * bar_w
                    bars = ax.bar(x_indices + offset, sy, color=scolor, alpha=alpha,
                                 label=slabel, edgecolor=edgecolor, width=bar_w)
                    if idx == 0:
                        ax.set_xticks(x_indices)
                        ax.set_xticklabels(sx)
                else:
                    bars = ax.bar(sx, sy, color=scolor, alpha=alpha, label=slabel,
                                 edgecolor=edgecolor, width=barwidth)

                # Add value labels on bars
                if style.get("show_values", num_series == 1):
                    value_fontsize = style.get("value_fontsize", 9)
                    for i, (xi, yi) in enumerate(zip(sx, sy)):
                        ax.text(i, yi + max(sy) * 0.01, f'{yi:.1f}',
                               ha='center', va='bottom', fontsize=value_fontsize)

            elif plot_type == "scatter":
                alpha = s.get("alpha", style.get("alpha", 0.6))
                size = s.get("size", style.get("size", 50))
                marker = s.get("marker", style.get("marker", "o"))
                ax.scatter(sx, sy, c=scolor, alpha=alpha, s=size, marker=marker, label=slabel)

        # Auto-enable legend when multiple series are present
        if num_series > 1 and not style.get("legend"):
            style["legend"] = True

    elif plot_type in ["heatmap", "contour"]:
        z = np.array(data.get("z", [[]]))
        x = data.get("x", None)
        y = data.get("y", None)

        if plot_type == "heatmap":
            cmap = style.get("cmap", "RdYlBu_r")
            im = ax.imshow(z, cmap=cmap, aspect='auto', origin='lower')
            plt.colorbar(im, ax=ax, label=style.get("colorbar_label", ""))

            # Set tick labels if x and y provided
            if x is not None:
                ax.set_xticks(range(len(x)))
                ax.set_xticklabels(x, rotation=45)
            if y is not None:
                ax.set_yticks(range(len(y)))
                ax.set_yticklabels(y)

        elif plot_type == "contour":
            cmap = style.get("cmap", "RdYlBu_r")
            levels = style.get("levels", 10)
            if x is not None and y is not None:
                contour = ax.contourf(x, y, z, levels=levels, cmap=cmap)
            else:
                contour = ax.contourf(z, levels=levels, cmap=cmap)
            plt.colorbar(contour, ax=ax, label=style.get("colorbar_label", ""))

    # Set labels and title with customizable fonts
    title_kwargs = {"fontsize": title_fontsize, "fontweight": title_fontweight}
    label_kwargs = {"fontsize": label_fontsize, "fontweight": label_fontweight}
    if fontfamily:
        title_kwargs["fontfamily"] = fontfamily
        label_kwargs["fontfamily"] = fontfamily

    ax.set_title(title, **title_kwargs)
    ax.set_xlabel(xlabel, **label_kwargs)
    ax.set_ylabel(ylabel, **label_kwargs)

    # Customize tick labels
    if tick_fontsize:
        ax.tick_params(axis='both', labelsize=tick_fontsize)
    if tick_rotation_x is not None:
        plt.setp(ax.get_xticklabels(), rotation=tick_rotation_x, ha='right')
    if tick_rotation_y is not None:
        plt.setp(ax.get_yticklabels(), rotation=tick_rotation_y)

    # Bold tick labels if requested
    if style.get("tick_fontweight") or (style.get("fontweight") == "bold" and tick_fontsize):
        weight = style.get("tick_fontweight", style.get("fontweight", "normal"))
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight(weight)

    # Set axis limits if provided
    if style.get("ylim"):
        ax.set_ylim(style["ylim"])
    if style.get("xlim"):
        ax.set_xlim(style["xlim"])

    # Add grid
    if style.get("grid", True):
        grid_alpha = style.get("grid_alpha", 0.3)
        grid_color = style.get("grid_color", None)
        grid_kwargs = {"alpha": grid_alpha}
        if grid_color:
            grid_kwargs["color"] = grid_color
        ax.grid(True, **grid_kwargs)

    # Background color
    if style.get("facecolor"):
        ax.set_facecolor(style["facecolor"])

    # Add legend if labels provided or multiple series
    if data.get("labels") is not None or data.get("series") is not None or style.get("legend"):
        legend_kwargs = {"loc": style.get("legend_loc", "best")}
        if style.get("legend_fontsize"):
            legend_kwargs["fontsize"] = style["legend_fontsize"]
        if style.get("legend_title"):
            legend_kwargs["title"] = style["legend_title"]
        if style.get("legend_title_fontsize"):
            legend_kwargs["title_fontsize"] = style["legend_title_fontsize"]
        if style.get("legend_frameon") is not None:
            legend_kwargs["frameon"] = style["legend_frameon"]
        if style.get("legend_framealpha") is not None:
            legend_kwargs["framealpha"] = style["legend_framealpha"]
        if style.get("legend_facecolor"):
            legend_kwargs["facecolor"] = style["legend_facecolor"]
        if style.get("legend_edgecolor"):
            legend_kwargs["edgecolor"] = style["legend_edgecolor"]
        if style.get("legend_shadow") is not None:
            legend_kwargs["shadow"] = style["legend_shadow"]
        if style.get("legend_ncol"):
            legend_kwargs["ncol"] = style["legend_ncol"]
        if style.get("legend_markerscale"):
            legend_kwargs["markerscale"] = style["legend_markerscale"]
        if style.get("legend_borderpad") is not None:
            legend_kwargs["borderpad"] = style["legend_borderpad"]

        leg = ax.legend(**legend_kwargs)

        # Post-creation text styling (not available via legend kwargs)
        if style.get("legend_fontweight"):
            for text in leg.get_texts():
                text.set_fontweight(style["legend_fontweight"])
        if style.get("legend_fontstyle"):
            for text in leg.get_texts():
                text.set_fontstyle(style["legend_fontstyle"])
        if style.get("legend_fontcolor"):
            for text in leg.get_texts():
                text.set_color(style["legend_fontcolor"])
        if style.get("legend_fontfamily"):
            for text in leg.get_texts():
                text.set_fontfamily(style["legend_fontfamily"])
        if style.get("legend_title_fontweight") and leg.get_title():
            leg.get_title().set_fontweight(style["legend_title_fontweight"])

    # Add metadata annotation if provided
    metadata = style.get("metadata", {})
    if metadata:
        metadata_text = ""

        # Build metadata text
        if "location" in metadata:
            metadata_text += f"Location: {metadata['location']}\n"
        if "coordinates" in metadata:
            metadata_text += f"Coordinates: {metadata['coordinates']}\n"
        if "scenario" in metadata:
            metadata_text += f"Scenario: {metadata['scenario']}\n"
        if "year" in metadata or "time_range" in metadata:
            time_info = metadata.get('year') or metadata.get('time_range')
            metadata_text += f"Time: {time_info}\n"
        if "ensemble" in metadata:
            metadata_text += f"Ensemble: {metadata['ensemble']}\n"
        if "variable" in metadata:
            metadata_text += f"Variable: {metadata['variable']}\n"
        if "source" in metadata:
            metadata_text += f"Source: {metadata['source']}\n"

        # Add any additional metadata
        for key, value in metadata.items():
            if key not in ["location", "coordinates", "scenario", "year", "time_range",
                          "ensemble", "variable", "source"]:
                metadata_text += f"{key}: {value}\n"

        # Add metadata box to plot
        metadata_fontsize = style.get("metadata_fontsize", 9)
        metadata_fontweight = style.get("metadata_fontweight", "normal")
        metadata_fontstyle = style.get("metadata_fontstyle", "normal")
        metadata_fontcolor = style.get("metadata_fontcolor", "black")
        metadata_fontfamily = style.get("metadata_fontfamily", "monospace")
        metadata_facecolor = style.get("metadata_facecolor", "wheat")
        metadata_edgecolor = style.get("metadata_edgecolor", "black")
        metadata_alpha = style.get("metadata_alpha", 0.8)
        metadata_position = style.get("metadata_position", "upper left")

        # Map position names to coordinates
        position_map = {
            "upper left": (0.02, 0.98, "top", "left"),
            "upper right": (0.98, 0.98, "top", "right"),
            "lower left": (0.02, 0.02, "bottom", "left"),
            "lower right": (0.98, 0.02, "bottom", "right"),
            "upper center": (0.50, 0.98, "top", "center"),
            "lower center": (0.50, 0.02, "bottom", "center"),
        }
        if isinstance(metadata_position, list) and len(metadata_position) == 2:
            mx, my = metadata_position
            mva, mha = "top", "left"
        else:
            mx, my, mva, mha = position_map.get(metadata_position, (0.02, 0.98, "top", "left"))

        if metadata_text:
            ax.text(mx, my, metadata_text.strip(),
                   transform=ax.transAxes,
                   fontsize=metadata_fontsize,
                   fontweight=metadata_fontweight,
                   fontstyle=metadata_fontstyle,
                   color=metadata_fontcolor,
                   verticalalignment=mva,
                   horizontalalignment=mha,
                   bbox=dict(boxstyle='round', facecolor=metadata_facecolor,
                             edgecolor=metadata_edgecolor, alpha=metadata_alpha),
                   family=metadata_fontfamily)

    plt.tight_layout()
    return fig


def plot_climate_data(
    plot_config: str | Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main function called by the model to create plots.

    Args:
        plot_config: JSON string or dict containing plot configuration

    Returns:
        Dictionary with status and figure object
    """
    try:
        # Parse configuration - handle both string and dict inputs
        if isinstance(plot_config, dict):
            config = plot_config
        else:
            config = json.loads(plot_config)

        # Create the plot
        fig = create_plot(
            plot_type=config.get("plot_type", "line"),
            data=config.get("data", {}),
            title=config.get("title", ""),
            xlabel=config.get("xlabel", ""),
            ylabel=config.get("ylabel", ""),
            style=config.get("style", {})
        )

        return {
            "status": "ok",
            "figure": fig,
            "message": "Plot created successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to create plot: {str(e)}"
        }
