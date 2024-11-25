Pourbaix Diagram
================

:code:`mlipx` provides a command line interface to generate Pourbaix diagrams.
You can run the following command to instantiate a test directory:

.. note::

   The Pourbaix diagram requires the installation of ``pip install mpcontribs-client``.

.. code-block:: console

   (.venv) $ mlipx recipes pourbaix-diagram

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`PourbaixDiagram`
