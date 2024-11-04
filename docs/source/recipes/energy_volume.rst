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


Dynamic Datasets
----------------
Often, one wants to investigate the performance of a model on a dynamic dataset. In the following we will show how to expand this recipe to data gathered dynamically from the mptraj dataset.
Here, we want to look at systems containing the elements :code:`B` and :code:`F`.
Therefore, we will make the following changes to the :term:`graph.py` file.
First, we replace the existing data generation with the loading of the mptraj dataset.
Then, we filter the data to only contain the elements :code:`B` and :code:`F`.

.. code-block:: diff

      - with project.group("initialize"):
      -     confs = mlipx.Smiles2Conformers(smiles="CCO", num_confs=10)
      -     data = mlipx.BuildBox(data=[confs.frames], counts=[10], density=789)
      + mptraj = zntrack.add(
      +     url="https://github.com/ACEsuit/mace-mp/releases/download/mace_mp_0b/mp_traj_combined.xyz",
      +     path="mptraj.xyz",
      + )
      + with project:
      +     data = mlipx.LoadDataFile(path=mptraj)
      +     filtered = mlipx.FilterAtoms(data=data.frames, elements=["B", "F"], filtering_type="exclusive")

Now, we could look at a single structure, but instead we iterate over multiple structures and evaluate each model on them.

.. note::
   You can not use :code:`for idx in range(len(filtered.frames))` as the number of frames is not known at this point.
   The :term:`graph.py` file only defines the workflow, and the number of frames is only known at runtime.


.. code-block:: diff

      +  for data_id in range(5):
            for model_name, model in MODELS.items():
      +        with project.group(f"frame_{data_id}", model_name):
                  ev = mlipx.EnergyVolumeCurve(
                     model=model,
                     data=filtered.frames,
      +              data_id=data_id,
                     n_points=50,
                     start=0.75,
                     stop=2.0,
                  )

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`Smiles2Conformers`
* :term:`BuildBox`
* :term:`EnergyVolumeCurve`

A working example can be found at `here <https://gitlab.roqs.basf.net/qm-inorganics/mlip-tracking/mlip-evaluation-templates/-/tree/energy-volume?ref_type=heads>`_.
