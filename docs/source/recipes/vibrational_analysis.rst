Vibrational Analysis
====================

:code:`mlipx` provides a command line interface to vibrational analysis.
You can run the following command to instantiate a test directory:

.. code-block:: console

   (.venv) $ mlipx recipes vibrational-analysis --models mace_mp,sevennet,orb_v2 --smiles=CO,CCO,CCCO,CCCCO

The vibrational analysis method needs additional information to run.
Please edit the ``main.py`` file and set the ``system`` parameter on the ``VibrationalAnalysis`` node.
For the given list of SMILES, you should set it to ``"molecule"``.
Then run the following commands to reproduce and inspect the results:

.. code-block:: console

   (.venv) $ python main.py
   (.venv) $ dvc repro
   (.venv) $ mlipx compare --glob "*VibrationalAnalysis"


.. jupyter-execute::
   :hide-code:

   from mlipx.doc_utils import get_plots

   plots = get_plots("*VibrationalAnalysis", "../../examples/vibrational_analysis/")
   plots["Gibbs-Comparison"].show()

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`VibrationalAnalysis`

.. dropdown:: Content of :code:`main.py`

   .. literalinclude:: ../../../examples/vibrational_analysis/main.py
      :language: Python


.. dropdown:: Content of :code:`models.py`

   .. literalinclude:: ../../../examples/vibrational_analysis/models.py
      :language: Python
