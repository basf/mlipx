Metrics Overview
================

``mlipx`` provides several tools and integrations for comparing and visualizing metrics across experiments and nodes.
This section outlines how to use these features to evaluate model performance and gain insights into various tasks.

Comparing Metrics Using ``mlipx compare``
-----------------------------------------

With the ``mlipx compare`` command, you can directly compare results from the same Node or experiment using the :ref:`ZnDraw <zndraw>` visualization tool. For example:

.. code-block:: bash

    mlipx compare mace_mp_0_StructureOptimization orb_v2_0_StructureOptimization

This allows you to study the performance of different models for a single task in great detail.
Every Node in ``mlipx`` defines its own comparison method for this.

Integrations with DVC and MLFlow
--------------------------------

To enable a broader overview of metrics and enhance experiment tracking, ``mlipx`` integrates with both :term:`DVC` and :term:`mlflow`. These tools allow for efficient tracking, visualization, and comparison of metrics across multiple experiments.

MLFlow Integration
-------------------

``mlipx`` supports logging metrics to :term:`mlflow`. To use this feature, ensure ``mlflow`` is installed:

.. code-block:: bash

    pip install mlflow


.. note::

    More information on how to setup MLFlow and run the server can be found in the `MLFlow documentation <https://mlflow.org/docs/latest/tracking.html#tracking-ui>`_.

Set the tracking URI to connect to your MLFlow server:

.. code-block:: bash

    export MLFLOW_TRACKING_URI=http://localhost:5000

Use the ``zntrack mlflow-sync`` command to upload metrics to MLFlow.
For this command, you need to specify the Nodes you want to sync.

.. note::
    You can get an overview of all available Nodes using the ``zntrack list`` command.
    The use of glob patterns makes it easy to sync the same node for different models.
    To structure the experiments in MLFlow, you can specify a parent experiment.

A typical structure for syncing multiple Nodes would look like this:

.. code-block:: bash

    zntrack mlflow-sync "*StructureOptimization" --experiment "mlipx" --parent "StructureOptimization"
    zntrack mlflow-sync "*EnergyVolumeCurve" --experiment "mlipx" --parent "EnergyVolumeCurve"
    zntrack mlflow-sync "*MolecularDynamics" --experiment "mlipx" --parent "MolecularDynamics"

With the MLFlow UI, you can visualize and compare metrics across experiments:

.. image:: https://github.com/user-attachments/assets/2536d5d5-f8ef-4403-ac4b-670d40ae64de
    :align: center
    :alt: MLFlow UI Metrics
    :width: 100%
    :class: only-dark

.. image:: https://github.com/user-attachments/assets/0d3d3187-b8ee-4b27-855e-7b245bd88346
    :align: center
    :alt: MLFlow UI Metrics
    :width: 100%
    :class: only-light

Additionally, ``mlipx`` logs plots to MLFlow, enabling comparisons of relaxation energies across models or direct visualizations of energy-volume curves:

.. image:: https://github.com/user-attachments/assets/19305012-6d92-40a3-bac6-68522bd55490
    :align: center
    :alt: MLFlow UI Plots
    :width: 100%
    :class: only-dark

.. image:: https://github.com/user-attachments/assets/3cffba32-7abf-4a36-ac44-b584126c2e57
    :align: center
    :alt: MLFlow UI Plots
    :width: 100%
    :class: only-light


Data Version Control (DVC)
---------------------------

Each Node in ``mlipx`` includes predefined metrics that can be accessed via the :term:`DVC` command-line interface. Use the following commands to view metrics and plots:

.. code-block:: bash

    dvc metrics show
    dvc plots show

For more details on working with DVC, refer to the `DVC documentation <https://dvc.org/doc/start/data-pipelines/metrics-parameters-plots#viewing-metrics-and-plots>`_.

DVC also integrates seamlessly with Visual Studio Code through the `DVC extension <https://marketplace.visualstudio.com/items?itemName=iterative.dvc>`_, providing a user-friendly interface to browse and compare metrics and plots:

.. image:: https://github.com/user-attachments/assets/79ede9d2-e11f-47da-b69c-523aa0361aaa
    :alt: DVC extension in Visual Studio Code
    :width: 100%
    :class: only-dark

.. image:: https://github.com/user-attachments/assets/562ab225-15a8-409a-8e4e-f585e33103fa
    :alt: DVC extension in Visual Studio Code
    :width: 100%
    :class: only-light
