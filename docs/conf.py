from dotenv import load_dotenv


load_dotenv("../.env.test")

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "FLAME Hub Client"
copyright = "2025, Paul Brassel, Maximilian Jugl"
author = "Paul Brassel, Maximilian Jugl"
version = "0.2.2"
release = "0.2.2"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_default_options = {
    "show-inheritance": True,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "typing_extensions": ("https://typing-extensions.readthedocs.io/en/latest/", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "Documentation"
html_logo = "https://raw.githubusercontent.com/PrivateAIM/documentation/refs/heads/master/src/public/images/icon/icon_flame_light.png"
html_favicon = "https://github.com/PrivateAIM/documentation/raw/refs/heads/master/src/public/images/icon/favicon.ico"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
