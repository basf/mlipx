MLIPX Documentation
===================

:code:`mlipx` is a Python library for the evaluation and benchmarking of machine-learned interatomic potentials (:term:`MLIP`). MLIPs are advanced computational models that use machine learning techniques to describe complex atomic interactions accurately and efficiently. They significantly accelerate traditional quantum mechanical modeling workflows, making them invaluable for simulating a wide range of physical phenomena, from chemical reactions to materials properties and phase transitions. MLIP testing requires more than static cross-validation protocols. While these protocols are essential, they are just the beginning. Evaluating energy and force prediction accuracies on a test set is only the first step. To determine the real-world usability of an ML model, more comprehensive testing is needed.

:code:`mlipx` addresses this need by providing systematically designed testing recipes to assess the strengths and weaknesses of rapidly developing growing flavours of MLIP models. These recipes help ensure that models are robust and applicable to a wide range of scenarios. :code:`mlipx` provides you with an ever-growing set of evaluation methods accompanied by comprehensive visualization and comparison tools.

The goal of this project is to provide a common platform for the evaluation of MLIPs and to facilitate the exchange of evaluation results between researchers.
Ultimately, you should be able to determine the applicability of a given MLIP for your specific research question and to compare it to other MLIPs.

By offering these capabilities, MLIPX helps researchers determine the applicability of MLIPs for specific research questions and compare them effectively while developing from scratch or finetuning universal models. This collaborative tool promotes transparency and reproducibility in MLIP evaluations.

Join us in using and improving MLIPX to advance the field of machine-learned interatomic potentials. Your contributions and feedback are invaluable.

.. note::

   This project is under active development.


Example
-------

Create a ``mlipx`` :ref:`recipe <recipes>` to compute :ref:`ev` for the `mp-1143 <https://next-gen.materialsproject.org/materials/mp-1143>`_ structure using different :term:`MLIP` models

.. code-block:: console

   (.venv) $ mlipx recipes ev --models mace-mpa-0,sevennet,orb-v2 --material-ids=mp-1143 --repro
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
   contributing
   hub
   nodes
   glossary
   abc
   authors
