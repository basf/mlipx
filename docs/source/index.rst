MLIPX Documentation
===================

:code:`mlipx` is a Python library for the evaluation of machine-learned interatomic potentials (:term:`MLIP`).
It provides you with an ever-growing set of evaluation methods accompanied by comprehensive visualization and comparison tools.
The goal of this project is to provide a common platform for the evaluation of MLIPs and to facilitate the exchange of evaluation results between researchers.
Ultimately, you should be able to determine the applicability of a given MLIP for your specific research question and to compare it to other MLIPs.

.. note::

   This project is under active development.


Create a ``mlipx`` :ref:`recipe <recipes>` to perform :ref:`relax` for a given system using different :term:`MLIP` models

.. code-block:: console

   (.venv) $ mlipx recipes relax --datapath DODH_adsorption.xyz --repro
   (.venv) $ mlipx compare --glob '*StructureOptimization'

and use the integration with :ref:`ZnDraw <zndraw>` to visualize the resulting trajectories and compare the energies interactively.

.. image:: https://github.com/user-attachments/assets/0d673ef4-0131-4b74-892c-0b848d0669f7
   :width: 80%
   :alt: ZnDraw
   :class: only-light

.. image:: https://github.com/user-attachments/assets/18159cf5-613c-4779-8d52-7c5e37e2a32f
   :width: 80%
   :alt: ZnDraw
   :class: only-dark

.. toctree::
   :hidden:
   :maxdepth: 2

   installation
   quickstart
   concept
   recipes
   build_graph
   nodes
   glossary
   abc
   authors
