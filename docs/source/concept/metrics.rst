Metrics
=======

You can use different ways to compare metrics from ``mlipx``.
With the ``mlipc compare`` command you can compare results from the same Node and experiment using :ref:`ZnDraw <zndraw>`.

.. code-block:: bash

    mlipx compare mace_mp_0_StructureOptimization orb_v2_0_StructureOptimization

Often one might want to get an overview of different metrics from various experiments to evaluate the performance of different models on different tasks.
Therefore, ``mlipx`` integrates with :term:`DVC` and :term:`mlflow`.

Data Version Control
--------------------

Each Node comes with predefined metrics.
You can use the :term:`DVC` command line interface to see them.

.. code-block:: bash

    dvc metrics show
    dvc plots show

More information on how to use DVC can be found in the `DVC documentation <https://dvc.org/doc/start/data-pipelines/metrics-parameters-plots#viewing-metrics-and-plots>`_.

In addition, DVC integrates well with Visual Studio Code through the `DVC extension <https://marketplace.visualstudio.com/items?itemName=iterative.dvc>`_.

.. image:: https://github.com/user-attachments/assets/79ede9d2-e11f-47da-b69c-523aa0361aaa
    :alt: DVC extension in Visual Studio Code
    :width: 80%
    :class: only-dark

.. image:: https://github.com/user-attachments/assets/562ab225-15a8-409a-8e4e-f585e33103fa
    :alt: DVC extension in Visual Studio Code
    :width: 80%
    :class: only-light

MLFlow
------

``mlipx`` also logs metrics to :term:`mlflow`.
For this you need to have mlflow installed.

.. code-block:: bash

    pip install mlflow

If you have ``mlflow`` installed and running you can set the tracking URI to the mlflow server.

.. code-block:: bash

    export MLFLOW_TRACKING_URI=http://localhost:5000

Then you can use the ``zntrack mlflow-sync`` command to log metrics to mlflow.

.. code-block:: bash

    zntrack mlflow-sync "*StructureOptimization" --experiment "mlipx" --parent "StructureOptimization"
    zntrack mlflow-sync "*EnergyVolumeCurve" --experiment "mlipx" --parent "EnergyVolumeCurve"
    zntrack mlflow-sync "*MolecularDynamics" --experiment "mlipx" --parent "MolecularDynamics"


Using the mlflow UI you can get an overview of all evaluations, can look at the metrics and compare them.

.. image:: https://github.com/user-attachments/assets/2536d5d5-f8ef-4403-ac4b-670d40ae64de
    :align: center
    :alt: MLFlow UI Metrics
    :width: 80%
    :class: only-dark

.. image:: https://github.com/user-attachments/assets/0d3d3187-b8ee-4b27-855e-7b245bd88346
    :align: center
    :alt: MLFlow UI Metrics
    :width: 80%
    :class: only-light


Further, ``mlipx`` logs plots to mlflow as well, allowing you to compare the energy across different models or directly compare the energy-volume curves.


.. image:: https://github.com/user-attachments/assets/19305012-6d92-40a3-bac6-68522bd55490
    :align: center
    :alt: MLFlow UI Plots
    :width: 80%
    :class: only-dark


.. image:: https://github.com/user-attachments/assets/3cffba32-7abf-4a36-ac44-b584126c2e57
    :align: center
    :alt: MLFlow UI Plots
    :width: 80%
    :class: only-light


More information on visualizing metrics and plots in mlflow can be found in the `mlflow documentation <https://mlflow.org/docs/latest/tracking.html#tracking-ui>`_.
