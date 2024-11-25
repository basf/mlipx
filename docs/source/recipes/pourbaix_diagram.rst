Pourbaix Diagram
================

:code:`mlipx` provides a command line interface to generate Pourbaix diagrams.
You can run the following command to instantiate a test directory:

.. note::

   The Pourbaix diagram requires the installation of ``pip install mpcontribs-client``.

.. code-block:: console

   (.venv) $ mlipx recipes pourbaix-diagram

.. mermaid::
   :align: center

   graph TD
      subgraph setup
         setup1["LoadDataFile"]
      end
      subgraph mg1["Model 1"]
         m1["PourbaixDiagram"]
      end
      subgraph mg2["Model 2"]
         m2["PourbaixDiagram"]
      end
      subgraph mgn["Model <i>N</i>"]
         m3["PourbaixDiagram"]
      end
      setup --> mg1
      setup --> mg2
      setup --> mgn

This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`LoadDataFile`
* :term:`PourbaixDiagram`
