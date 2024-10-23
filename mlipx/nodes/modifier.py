import dataclasses
import typing as t

from ase import units

from mlipx.abc import DynamicsModifier


@dataclasses.dataclass
class TemperatureRampModifier(DynamicsModifier):
    """Ramp the temperature from start_temperature to temperature.

    Attributes
    ----------
    start_temperature: float, optional
        temperature to start from, if None, the temperature of the thermostat is used.
    end_temperature: float
        temperature to ramp to.
    interval: int, default 1
        interval in which the temperature is changed.
    total_steps: int
        total number of steps in the simulation.

    References
    ----------
    Code taken from ipsuite/calculators/ase_md.py
    """

    end_temperature: float
    total_steps: int
    start_temperature: t.Optional[float] = None
    interval: int = 1

    def modify(self, thermostat, step):
        # we use the thermostat, so we can also modify e.g. temperature
        if self.start_temperature is None:
            # different thermostats call the temperature attribute differently
            if temp := getattr(thermostat, "temp", None):
                self.start_temperature = temp / units.kB
            elif temp := getattr(thermostat, "temperature", None):
                self.start_temperature = temp / units.kB
            else:
                raise AttributeError("No temperature attribute found in thermostat.")

        percentage = step / (self.total_steps - 1)
        new_temperature = (
            1 - percentage
        ) * self.start_temperature + percentage * self.end_temperature
        if step % self.interval == 0:
            thermostat.set_temperature(temperature_K=new_temperature)
