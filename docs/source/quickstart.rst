Quickstart
==========

There are two ways to use the library: as a :ref:`command-line tool <cli-quickstart>` or as a :ref:`Python library <python-quickstart>`.
The CLI provides the most convenient way to get started, while the Python library offers more flexibility for advanced workflows.

.. image:: https://github.com/user-attachments/assets/ab38546b-6f5f-4c7c-9274-f7d2e9e1ae73
   :width: 100%
   :class: only-light

.. image:: https://github.com/user-attachments/assets/c34f64f7-958a-47cc-88ab-d2689e82deaf
   :width: 100%
   :class: only-dark

Use the :ref:`command-line tool <cli-quickstart>` to evaluate different :term:`MLIP` models on the ``DODH_adsorption_dft.xyz`` file and
visualize the trajectory together with the maximum force error in :ref:`ZnDraw <zndraw>`.

.. code:: console

   (.venv) $ mlipx recipes metrics --models mace_mp,sevennet,orb_v2 --datapath ../data DODH_adsorption_dft.xyz --repro
   (.venv) $ mlipx compare --glob "*CompareCalculatorResults"

.. toctree::
   :maxdepth: 2
   :hidden:

   quickstart/cli
   quickstart/python
