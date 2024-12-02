import pathlib

import ase
import ase.io as aio
import zntrack

import typing as t
ALLOWED_CRYSTAL = t.Literal['fcc111','fcc211','bcc110','bcc111','hcp0001','diamond111']
        
class BuildASEslab(zntrack.Node):
    """Create slab (ase.Atoms). As implemeneted in ase.build.
    Options are: fcc111, fcc211, bcc110, bcc111, hcp0001, diamond111

    Parameters
    ----------
    crystal : str
        A choice between a few options (fcc111, fcc211, bcc110, bcc111, hcp0001. diamond111)
    symbol : str
        Atoms symbol.
    size : tuple
        A tuple giving the system size in units of the minimal unit cell.
    a : float
        (optional) The lattice constant. If specified, it overrides the expermental lattice constant of the element. Must be specified if setting up a crystal structure different from the one found in nature.
    c : float
        (optional) Extra HCP lattice constant. If specified, it overrides the expermental lattice constant of the element.
    vacuum : float
        The thickness of the vacuum layer.
    orthogonal : bool
        If specified and true, forces the creation of a unit cell with orthogonal basis vectors.
    periodic : bool
         If true, sets boundary conditions and cell constantly with the corresponding bulk structure.
    """

    crystal: ALLOWED_CRYSTAL = zntrack.params()
    metal: str = zntrack.params()
    size: tuple = zntrack.params()
    a: float = zntrack.params()
    c: float = zntrack.params(False)
    vacuum: float = zntrack.params(10)
    orthogonal: bool = zntrack.params(True)
    periodic: bool  = zntrack.params(True)

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):
        # from ase.build import add_adsorbate
        from ase.constraints import FixAtoms
        import ase.build

        slb = getattr(ase.build, self.crystal)

        
        if not self.c:
            slab = slb(
                self.symbol, size=self.size, vacuum=self.vacuum, orthogonal=self.orthogonal, periodic=self.periodic, a=self.a
                )
        else:
            slab = slb(
                self.symbol, size=self.size, vacuum=self.vacuum, orthogonal=self.orthogonal, periodic=self.periodic, a=self.a, c=self.c
                )
        mask = [atom.tag > 1 for atom in slab]
        # print(mask)
        slab.set_constraint(FixAtoms(mask=mask))

        aio.write(self.frames_path, slabs)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(aio.iread(f, format="extxyz"))


class AddAdsorbate(zntrack.Node):
    """Add an adsorbate to a surface.

    Parameters
    ----------
    slab: ase.Atoms
        The surface onto which the adsorbate should be added.

    adsorbate: union(str, ase.Atoms)
        The adsorbate. Must be one of the following three types:
        A string containing the chemical symbol for a single atom.
        An atom object. An atoms object (for a molecular adsorbate).

    height: float
        Height above the surface.

    position: str
        The x-y position of the adsorbate, either as a tuple of
        two numbers or as a keyword (if the surface is produced by one
        of the functions in ase.build).

    mol_index: int
        (default: 0): If the adsorbate is a molecule, index of
        the atom to be positioned above the location specified by the
        position argument.

    """
    slab: ase.Atoms = zntrack.deps()
    adsorbate: ase.Atoms = zntrack.deps()
    height: float = zntrack.deps(1.5)
    position: str = zntrack.deps('all')
    mol_index: int = zntrack.deps(0)

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.xyz")

    def run(self):

        from ase.build import add_adsorbate
        
        parent = self.slab.copy()
        parent.info['_id'] = 'parent'
        parent.info['parent_id'] = None

        ads_trj = []
        if self.postions.lower() == 'all':
            for k, v in self.slab.info['adsorbate_info']['sites'].items():
                ads_slab = self.slab.copy()
                parent.info['_id'] = 'ads'
                parent.info['parent_id'] = 'parent'
                add_adsorbate(ads_slab, adsorbate=self.adsorbate, height=self.height, positon = v, mol_index=self.mol_index)
                ads_trj.append(ads_slab)
        else:
            ads_slab = self.slab.copy()
            parent.info['_id'] = 'ads'
            parent.info['parent_id'] = 'parent'
            add_adsorbate(ads_slab, adsorbate=self.adsorbate, height=self.height, positon = self.position, mol_index=self.mol_index)

        aio.write(self.frames_path, ads_trj)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "r") as f:
            return list(aio.iread(f, format="extxyz"))
        
    
    # @staticmethod
    # def compare(*nodes: "StructureOptimization") -> ComparisonResults:
    #     frames = sum([node.frames for node in nodes], [])
    #     offset = 0
    #     fig = go.Figure()
    #     for idx, node in enumerate(nodes):
    #         energies = [atoms.get_potential_energy() for atoms in node.frames]
    #         fig.add_trace(
    #             go.Scatter(
    #                 x=list(range(len(energies))),
    #                 y=energies,
    #                 mode="lines+markers",
    #                 name=node.name,
    #                 customdata=np.stack([np.arange(len(energies)) + offset], axis=1),
    #             )
    #         )
    #         offset += len(energies)
    #     return ComparisonResults(
    #         frames=frames,
    #         figures={"energy_vs_steps": fig},
    #     )