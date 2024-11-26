MLIPX Documentation
===================

:code:`mlipx` is a Python library for the evaluation of machine-learned interatomic potentials (:term:`MLIP`).
It provides you with an ever-growing set of evaluation methods accompanied by comprehensive visualization and comparison tools.
The goal of this project is to provide a common platform for the evaluation of MLIPs and to facilitate the exchange of evaluation results between researchers.
Ultimately, you should be able to determine the applicability of a given MLIP for your specific research question and to compare it to other MLIPs.

.. note::

   This project is under active development.


Example
-------

Create a ``mlipx`` :ref:`recipe <recipes>` to compute :ref:`ev` for the `mp-1143 <https://next-gen.materialsproject.org/materials/mp-1143>`_ structure using different :term:`MLIP` models

.. code-block:: console

   (.venv) $ mlipx recipes ev --models mace_mp,sevennet,orb_v2 --material-ids=mp-1143 --repro
   (.venv) $ mlipx compare --glob "*EnergyVolumeCurve"

and use the integration with :ref:`ZnDraw <zndraw>` to visualize the resulting trajectories and compare the energies interactively.

.. image:: https://github.com/user-attachments/assets/c2479d17-c443-4550-a641-c513ede3be02
   :width: 100%
   :alt: ZnDraw
   :class: only-light

.. image:: https://github.com/user-attachments/assets/2036e6d9-3342-4542-9ddb-bbc777d2b093
   :width: 100%
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
