import os

from dotenv import load_dotenv

from flame_hub import __version__


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
version = __version__
release = __version__
rst_prolog = f"""
.. |hub_version| replace:: {os.getenv("PYTEST_HUB_VERSION")}
.. role:: console(code)
    :language: console
.. role:: python(code)
    :language: python
"""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "numpydoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

numpydoc_show_class_members = False

autodoc_default_options = {
    "show-inheritance": True,
}
autodoc_member_order = "bysource"
autodoc_type_aliases = {
    "FilterParams": "flame_hub.types.FilterParams",
    "FieldParams": "flame_hub.types.FieldParams",
    "NodeType": "flame_hub.types.NodeType",
    "RegistryProjectType": "flame_hub.types.RegistryProjectType",
    "ProjectNodeApprovalStatus": "flame_hub.types.ProjectNodeApprovalStatus",
    "AnalysisBuildStatus": "flame_hub.types.AnalysisBuildStatus",
    "AnalysisRunStatus": "flame_hub.types.AnalysisRunStatus",
    "AnalysisCommand": "flame_hub.types.AnalysisCommand",
    "AnalysisNodeApprovalStatus": "flame_hub.types.AnalysisNodeApprovalStatus",
    "AnalysisNodeRunStatus": "flame_hub.types.AnalysisNodeRunStatus",
    "AnalysisBucketType": "flame_hub.types.AnalysisBucketType",
    "UNSET_T": "flame_hub.types.UNSET_T",
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "typing_extensions": ("https://typing-extensions.readthedocs.io/en/latest/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "Documentation"
html_logo = "https://raw.githubusercontent.com/PrivateAIM/documentation/refs/heads/master/src/public/images/icon/icon_flame_light.png"
html_favicon = "https://github.com/PrivateAIM/documentation/raw/refs/heads/master/src/public/images/icon/favicon.ico"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
