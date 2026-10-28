# Physics and architecture

All quantities are SI. State is inertial Cartesian `(x,y,vx,vy)` in a single
central body's equatorial plane. The surface launch position is `(0,R)`;
the local east tangent initially points along +x. Bodies do not rotate.

## Force model

- Gravity: `a = -mu * r_vector / |r|^3`.
- Atmospheric density: `rho = rho0 * exp(-max(altitude,0)/H)`; no wind.
- Dynamic pressure: `q = rho * speed^2 / 2`.
- Body drag: `D = q * Cd * reference_area`, opposite inertial velocity.
- Thrust direction follows commanded pitch relative to local horizon.
- Mass flow: `mdot = thrust / (Isp * 9.80665)`; last step's thrust is reduced
  to match remaining fuel exactly. Dropped stages no longer contribute mass.
- Wing lift: `Cl = clamp(2*pi*sin(angle_of_attack), -1.2, 1.2)` and
  `L = q * wing_area * Cl`; induced drag adds `q * wing_area * .06 * Cl^2`.
  Lift is perpendicular to velocity. This saturation is a simplification,
  not a validated stall model. Plane thrust has a simple 30 km cutoff.
- Internal heat indicator: `1.83e-4 * sqrt(rho) * speed^3`. This is an
  approximate stagnation-heating proxy, not a thermal system simulation.

Earth: R=6,371,000 m, mu=3.986004418e14 m³/s², rho0=1.225 kg/m³,
H=8500 m. Moon: R=1,737,400 m, mu=4.9048695e12 m³/s², vacuum.
Mars: R=3,389,500 m, mu=4.282837e13 m³/s², rho0=.020 kg/m³, H=11100 m.
Atmosphere parameters are deliberately approximate constants.

## Integration and contact

Semi-implicit Euler updates velocity before position using a fixed .02 s
step. The UI accumulates wall-clock time multiplied by the warp factor;
rendering runs separately. Wall-clock stalls over .1 s are clipped so that
dragging windows cannot cause huge catch-up bursts. Simulation time can
therefore run slower than real time on slow systems. High warp is intended
for coasting; use 1× for manual maneuvers.

The launch pad holds the vehicle until net outward acceleration becomes
positive. Surface contact projects position back onto the spherical body.
Contact speed below 8 m/s produces `Landed`; other contact produces `Crashed`.
Both states terminate integration. No bounce, terrain, landing gear,
structural breakup, or attitude dynamics are modeled. The displayed g is
net coordinate acceleration divided by standard gravity, not pilot g-load.

## Orbits

Specific energy `E=v²/2-mu/r`, angular momentum `h=x*vy-y*vx`, eccentricity
`e=sqrt(max(0,1+2*E*h²/mu²))`, and semi-major axis `a=-mu/(2*E)` define
the osculating conic. Bound apoapsis/periapsis are `a*(1±e)-R`.
Unbound apoapsis displays ESCAPE. Negative periapsis means the ideal conic
intersects the body. Dashed paths ignore all future drag, thrust, and
collisions. Trail points show actual flight history, not a forecast.

## Architecture and extension

`physics.py` has no GUI or external dependencies and can run headlessly.
`app.py` owns the controls, data sampling and Tk canvas renderer. Save files
use schema version 1 and serialize state and vehicle definitions as JSON;
no code is executed from a mission. Save/load reconstructs flight state,
but history, past events and visualization buffers start fresh.

Telemetry samples at approximately .5 simulation-second intervals. At most
30,000 samples (roughly 4.2 hours) are kept; CSV exports this in-memory
window. The chart shows the latest 600 samples; the map retains 6,000
trajectory points. There is one active vessel and one central body.

Future work: velocity-Verlet or RK integrator, atmosphere tables, aircraft
stall/engine curves, angle-of-attack guidance, rotation, collision meshes,
multi-vessel propagation and three-dimensional rendering. Each should be
validated against reference trajectories before being called accurate.
