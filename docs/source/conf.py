# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib
import sys

sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "mlipx"
copyright = "2024, Fabian Zills, Sheena Agarwal, Sandip De"
author = "Fabian Zills, Sheena Agarwal, Sandip De"
release = "v0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinxcontrib.mermaid",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "hoverxref.extension",
    "sphinxcontrib.bibtex",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_logo = "_static/mlipx-logo.svg"
html_title = "Machine Learned Interatomic Potential eXploration"
html_short_title = "mlipx"

# -- Options for hoverxref extension -----------------------------------------
# https://sphinx-hoverxref.readthedocs.io/en/latest/

hoverxref_role_types = {
    "class": "tooltip",
}
hoverxref_roles = ["term"]

# -- Options for sphinxcontrib-bibtex ----------------------------------------
# https://sphinxcontrib-bibtex.readthedocs.io/en/latest/

bibtex_bibfiles = ["references.bib"]

# -- Options for sphinx_copybutton -------------------------------------------
# https://sphinx-copybutton.readthedocs.io/en/latest/

copybutton_prompt_text = r">>> |\.\.\. |\(.*\) \$ "
copybutton_prompt_is_regexp = True
