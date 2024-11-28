# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import typing as t

import mlipx

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "mlipx"
copyright = "2024, Fabian Zills, Sheena Agarwal, Sandip De"
author = "Fabian Zills, Sheena Agarwal, Sandip De"
release = mlipx.__version__

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
    "jupyter_sphinx",
    "sphinx_design",
    "nbsphinx",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_title = "Machine Learned Interatomic Potential eXploration"
html_short_title = "mlipx"
html_favicon = "_static/mlipx-favicon.svg"

html_theme_options: t.Dict[str, t.Any] = {
    "light_logo": "mlipx-light.svg",
    "dark_logo": "mlipx-dark.svg",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/basf/mlipx",
            "html": "",
            "class": "fa-brands fa-github fa-2x",
        },
    ],
    "source_repository": "https://github.com/basf/mlipx/",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "navigation_with_keys": True,
}

# font-awesome logos
html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

# -- Options for hoverxref extension -----------------------------------------
# https://sphinx-hoverxref.readthedocs.io/en/latest/

hoverxref_roles = ["term"]
hoverxref_role_types = {
    "class": "tooltip",
}


# -- Options for sphinxcontrib-bibtex ----------------------------------------
# https://sphinxcontrib-bibtex.readthedocs.io/en/latest/

bibtex_bibfiles = ["references.bib"]

# -- Options for sphinx_copybutton -------------------------------------------
# https://sphinx-copybutton.readthedocs.io/en/latest/

copybutton_prompt_text = r">>> |\.\.\. |\(.*\) \$ "
copybutton_prompt_is_regexp = True
