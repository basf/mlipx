import pathlib

import ase
import ase.io as aio
import zntrack

from mlipx.abc import NodeWithCalculator, ComparisonResults
import ase.optimize as opt

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
    symbol: str = zntrack.params()
    size: tuple = zntrack.params()
    a: float = zntrack.params(None)
    c: float = zntrack.params(False)
    vacuum: float = zntrack.params(10)
    orthogonal: bool = zntrack.params(True)
    periodic: bool  = zntrack.params(True)

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.traj")

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

        aio.write(self.frames_path, slab)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "rb") as f:
            return list(aio.iread(f, format="traj"))


class RelaxAdsorptionConfigs(zntrack.Node):
# class AddAdsorbate(zntrack.Node):

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
    slabs: list[ase.Atoms] = zntrack.deps()
    adsorbates: list[ase.Atoms] = zntrack.deps()
    height: float = zntrack.params(2.1)
    position: str = zntrack.params('all')
    mol_index: int = zntrack.params(0)
    slab_id: int = zntrack.params(-1)
    adsorbate_id: int = zntrack.params(-1)
    optimizer: str = zntrack.params('LBFGS')
    model: NodeWithCalculator = zntrack.deps()
    steps: int = zntrack.params(300)
    fmax: float = zntrack.params(0.05)

    frames_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "frames.traj")
    relax_path: pathlib.Path = zntrack.outs_path(zntrack.nwd / "relax")

    def relax_atoms(self, atoms):
        count = len(list(self.relax_path.glob('*')))
        optimizer = getattr(opt, self.optimizer)
        calc = self.model.get_calculator()

        self.relax_path.mkdir(exist_ok=True)

        # energies = []
        # fmax = []

        # def metrics_callback():
        #     energies.append(atoms.get_potential_energy())
        #     fmax.append(np.linalg.norm(atoms.get_forces(), axis=-1).max())

        atoms.calc = calc
        dyn = optimizer(
            atoms,
            trajectory = (self.relax_path / f"{count}.traj").as_posix(),
        )
        # dyn.attach(metrics_callback)
        dyn.run(fmax=self.fmax, steps=self.steps)
        return atoms

    def run(self):

        from ase.build import add_adsorbate
        
        slab = self.slabs[self.slab_id]
        slab.info['type'] = 'slab'
        slab = self.relax_atoms(slab)
        adsorbate = self.adsorbates[self.adsorbate_id]
        adsorbate.info['type'] = 'adsorbate'
        adsorbate = self.relax_atoms(adsorbate)
        
        # slab.info['_id'] = 'parent'
        # parent.info['parent_id'] = None

        ads_trj = []
        if self.position.lower() == 'all':
            # for k, v in self.slabs[self.slab_id].info['adsorbate_info']['sites'].items():
            for k in self.slabs[self.slab_id].info['adsorbate_info']['sites'].keys():

                print(k)
                ads_slab = slab.copy()
                ads_slab.info['type'] = 'slab+adsorbate'
                add_adsorbate(ads_slab, adsorbate=self.adsorbates[self.adsorbate_id], height=self.height, position = k, mol_index=self.mol_index)
                ads_trj.append(self.relax_atoms(ads_slab))
        else:
            raise ValueError('not yet, sry :)')
            # ads_slab = self.slabs[self.slab_id].copy()
            # add_adsorbate(ads_slab, adsorbate=self.adsorbates, height=self.height, position = self.position, mol_index=self.mol_index)

        aio.write(self.frames_path, ads_trj)

    @property
    def frames(self) -> list[ase.Atoms]:
        with self.state.fs.open(self.frames_path, "rb") as f:
            return list(aio.iread(f, format="traj"))
        
    @property
    def relaxations(self) -> dict[str, list[ase.Atoms]]:
        relax_dict = {}
        for path in self.relax_path.glob('*'):
            with self.state.fs.open(path, "rb") as f:
                relax_dict[path.as_posix()] = list(aio.iread(f, format="traj"))
        return relax_dict        


    # @staticmethod
    # def get_ref_ens(*nodes: "RelaxAdsorptionConfigs"):

    #     for key in nodes[0].relaxations:
    #         for node in nodes:
    #             traj = node.relaxations[key]

    #             if traj[0].info['type'].lower() == 'slab':
    #                 E_slab = traj[-1].get_potential_energy()
                
    #             if traj[0].info['type'].lower() == 'adsorbate':
    #                 E_adsorbate = traj[-1].get_potential_energy()
    #     return E_slab, E_adsorbate

    @staticmethod
    def compare(*nodes: "RelaxAdsorptionConfigs") -> ComparisonResults:

        full_traj = []
        for key in nodes[0].relaxations:
            for node in nodes:
                traj = node.relaxations[key]

                config_type = traj[0].info['type'].lower()

                if config_type == 'slab':
                    E_slab = traj[-1].get_potential_energy()
                    E_ref = E_slab
                
                elif config_type == 'adsorbate':
                    E_adsorbate = traj[-1].get_potential_energy()
                    E_ref = E_adsorbate

                elif config_type == 'slab+adsorbate':
                    E_ref = E_adsorbate + E_slab
                    #this will only work if the slab and adsorbate come in the traj before slab+ads
                    # - will always be the case
                
                else:
                    raise ValueError(f"type {config_type} not supported...")

                for a in traj:
                    a.info['E_ads'] = a.get_potential_energy() - E_ref
                    # a.info['E_ads'] = a.get_potential_energy() - E_ref

                full_traj += traj

        # for results in zip(x.relaxations.values() for x in nodes):
        #     traj = results[0]
        #     print(type(traj))
        return {
            'frames': full_traj,
            'figures': {}
        }
        
        # frames = sum([node.frames for node in nodes], [])
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

