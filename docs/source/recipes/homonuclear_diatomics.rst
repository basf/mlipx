Homonuclear Diatomics
===========================
TBA

.. code-block:: console

   (.venv) $ mlipx recipes homonuclear-diatomics


.. jupyter-execute::
    :hide-code:

    import numpy as np
    from matplotlib import pyplot
    %matplotlib inline

    x = np.linspace(1E-3, 2 * np.pi)

    pyplot.plot(x, np.sin(x) / x)
    pyplot.plot(x, np.cos(x))
    pyplot.grid()


This test uses the following Nodes together with your provided model in the :term:`models.py` file:

* :term:`HomonuclearDiatomics`
