Energy Volume Curves
===========================
TBA

.. note::
   This recipe uses the :term:`rdkit2ase` and :term:`packmol` packages to generate an initial box. Alternatively, you can provide a datafile using :term:`LoadDataFile` to evaluate your own structures.

.. code-block:: console

   (.venv) $ mlipx recipes ev

.. mermaid::
   :align: center

   graph TD

      subgraph Initialization
         Smiles2Conformers --> BuildBox
      end

      BuildBox --> mg1
      BuildBox --> mg2
      BuildBox --> mgn

      subgraph mg1["Model 1"]
         m1["EnergyVolumeCurve"]
      end
      subgraph mg2["Model 2"]
         m2["EnergyVolumeCurve"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["EnergyVolumeCurve"]
      end


In the following we show the results for a box of :code:`CCO`.


.. jupyter-execute::
   :hide-code:

   import plotly.io as pio
   pio.renderers.default = "sphinx_gallery"

   figure = pio.read_json("source/figures/energy-volume-curve.json")
   figure.show()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`Smiles2Conformers`
* :term:`BuildBox`
* :term:`EnergyVolumeCurve`

A working example can be found at `here <https://gitlab.roqs.basf.net/qm-inorganics/mlip-tracking/mlip-evaluation-templates/-/tree/energy-volume?ref_type=heads>`_.
