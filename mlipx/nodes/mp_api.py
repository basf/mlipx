import zntrack
from mp_api import client

# set MP_API_KEY environment variable


class MPRester(zntrack.Node):
    """Search the materials project database.

    Parameters
    ----------
    search_kwargs: dict
        The search parameters for the materials project database.

    Example
    -------
    >>> MPRester(search_kwargs={"material_ids": ["mp-1234"]})

    """

    search_kwargs: dict = zntrack.params()

    def run(self):
        with client.MPRester() as mpr:
            docs = mpr.materials.summary.search(**self.search_kwargs)
        print(docs)
