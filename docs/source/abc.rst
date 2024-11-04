Abstract Base Classes
======================
We make use of abstract base classes, protocols and type hints to improve the workflow design experience.
Further, these can be used for cross-package interoperability with other :term:`ZnTrack` based packages like :term:`IPSuite`.

For most :term:`Node` classes operating on lists of :term:`ASE` objects, there are two scenarios:
- The node operates on a single :term:`ASE` object.
- The node operates on a list of :term:`ASE` objects.
For both scenarios, the node is given a list of :term:`ASE` objects via the `data` attribute.
For the first scenario, the `id` of the :term:`ASE` object is given via the `data_id` attribute which is omitted for the second scenario.

.. automodule:: mlipx.abc
    :members:
    :undoc-members:
