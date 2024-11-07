.. _Distributed evaluation:

Distributed evaluation
======================

For the evaluation of different :term:`MLIP` models, it is often necessary to
run the evaluation in different environments due to package incompatibility.
Another reason can be the computational cost of the evaluation.

Writing the evaluation in a workflow-like manner allows for the separation of tasks
onto different hardware or software environments.
For this purpose, the :term:`paraffin` package was developed.

You can use :code:`paraffin submit` to queue the evaluation of the selected stages.
With :code:`paraffin worker --concurrency 5` you can start 5 workers to evaluate the stages.

Further, you can select which stage should be picked up by which worker by defining a :code:`paraffin.yaml` file which supports wildcards.

.. code-block:: yaml

    queue:
        "B_X*": BQueue
        "A_X_AddNodeNumbers": AQueue

The above configuration will queue all stages starting with :code:`B_X` to the :code:`BQueue` and the stage :code:`A_X_AddNodeNumbers` to the :code:`AQueue`.
You can then use :code:`paraffin worker --queue BQueue` to only pick up the stages from the :code:`BQueue` and vice versa.

The paraffin package is available on PyPI and can be installed via:

.. code-block:: bash

    pip install paraffin
