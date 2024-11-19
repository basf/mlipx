import plotly.io as pio


def show(file: str) -> None:
    pio.renderers.default = "sphinx_gallery"

    figure = pio.read_json(f"source/figures/{file}")
    figure.update_layout(
        {
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
        }
    )
    figure.show()