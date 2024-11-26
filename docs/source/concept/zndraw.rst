.. _zndraw:

Visualisation
=============
:code:`mlipx` uses ZnDraw as primary tool for visualisation and comparison.
The following will give you an overview.

The ZnDraw package provides versatile visualisation package for atomisitc structures.
It is based on :term:`ASE` and runs as a web application.
You can install it via:

.. code:: bash

    pip install zndraw


It can be used to visualize data through a CLI:

.. code:: bash

    zndraw file.xyz # any ASE supported file format + H5MD
    zndraw --remote . Node.frames # any ZnTrack node that has an attribute `list[ase.Atoms]`

Once you have a running ZnDraw instance, you can connect to it from within Python.
You can find more information in the GUI by clicking on :code:`Python Access`.
The :code:`vis` object behaves like a list of :term:`ASE` atom objects.
Modifying them in place, will be reflected in real-time on the GUI.

.. code:: python

    from zndraw import ZnDraw

    vis = ZnDraw(url="http://localhost:1234", token="<some-token>")

    print(vis[0])
    >>> ase.Atoms(...)

    vis.append(ase.Atoms(...))


.. image:: ../_static/zndraw_render.png
    :width: 100%

**Figure 1** Graphical user interface of the :ref:`ZnDraw <zndraw>` package with GPU path tracing enabled.


For further information have a look at the ZnDraw repository https://github.com/zincware/zndraw - a full documentation will be provided soon.
