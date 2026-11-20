"""Fixed-size copies of notebook charts for presentation exports."""

import altair as alt

from airbnb_analytics.data import PROJECT_ROOT

FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures"


def presentation_chart(chart, *, width=1200, height=675):
    """Keep the interactive original intact; size the exported canvas explicitly.

    Single plots include axes/legends inside the requested canvas. For facets,
    width and height apply to each panel; the grid determines the total size.
    """
    exported = chart.copy(deep=True)
    if isinstance(exported, alt.FacetChart):
        exported.spec = exported.spec.properties(width=width, height=height)
        exported = exported.properties(autosize="pad")
    else:
        exported = exported.properties(
            width=width,
            height=height,
            autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        )
    return (
        exported.configure(background="white", font="Arial")
        .configure_axis(labelFontSize=15, titleFontSize=17, labelLimit=400, titlePadding=14)
        .configure_legend(labelFontSize=15, titleFontSize=16, labelLimit=350)
        .configure_title(
            fontSize=22, subtitleFontSize=15, subtitlePadding=8, anchor="start", offset=18
        )
        .configure_header(labelFontSize=17, titleFontSize=17)
        .configure_view(stroke=None)
    )


def save_presentation_chart(chart, name, *, width=1200, height=675, scale_factor=3):
    """Write a high-resolution PNG and a vector SVG under outputs/figures."""
    destination = FIGURE_DIR / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    exported = presentation_chart(chart, width=width, height=height)
    exported.save(destination.with_suffix(".png"), scale_factor=scale_factor)
    exported.save(destination.with_suffix(".svg"))
    return exported
