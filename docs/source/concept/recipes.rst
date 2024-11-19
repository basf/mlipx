Recipes
=======

Setup
-----
One of :code:`mlipx` core functionality is providing you with pre-designed recipes.
These define workflows for evaluating :term:`MLIP` on specific tasks.
You can get an overview of all available recipes using

.. code-block:: console

   (.venv) $ mlipx recipes --help

All recipes follow the same structure.
It is recommended, to create a new directory for each recipe.

.. code-block:: console

   (.venv) $ mkdir molecular_dynamics
   (.venv) $ cd molecular_dynamics
   (.venv) $ mlipx recipes md --initialize

This will create the following structure:

.. code-block:: console

   molecular_dynamics/
   ├── .git/
   ├── .dvc/
   ├── models.py
   └── main.py

After initialization, adapt the :code:`main.py` file to point towards the requested data files.
Define all models for testing in the :term:`models.py` file.

Finally, build the recipe using

.. code-block:: console

   (.venv) $ python main.py
   (.venv) $ dvc repro


Upload Results
--------------
Once the recipe is finished, you can persist the results and upload them to a remote storage.
Therefore, you want to make a GIT commit and push it to your repository.

.. code-block:: console

   (.venv) $ git add .
   (.venv) $ git commit -m "Finished molecular dynamics test"
   (.venv) $ git push
   (.venv) $ dvc push

.. note::
   You need to define a :term:`GIT` and :term:`DVC` remote to push the results.
   More information on how to setup a :term:`DVC` remote can be found at https://dvc.org/doc/user-guide/data-management/remote-storage.


In combination or as an alternative, you can upload the results to a parameter and metric tracking service, such as :term:`mlflow`.
Given a running :term:`mlflow` server, you can use the following command to upload the results:

.. code-block:: console

   (.venv) $ zntrack mlflow-sync --help

.. note::
   Depending on the installed packages, the :term:`mlflow` command might not be available.
   This functionality is provided by the :term:`zntrack` package, and other tracking services can be used as well.
   They will show up once the respective package is installed.
   See https://zntrack.readthedocs.io/ for more information.
