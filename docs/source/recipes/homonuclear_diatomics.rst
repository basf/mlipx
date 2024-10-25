Homonuclear Diatomics
===========================
TBA

.. code-block:: console

   (.venv) $ mlipx recipes homonuclear-diatomics


.. jupyter-execute::
   :hide-code:

   import plotly.io as pio
   pio.renderers.default = "sphinx_gallery"

   figure = pio.read_json("source/figures/fnorm_error.json")
   figure.show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`HomonuclearDiatomics`
