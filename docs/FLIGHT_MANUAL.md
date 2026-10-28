# Flight exercises

## 1. Sounding flight

Choose Earth / Helios Two Stage and New surface flight. Set throttle to
100%, pitch 90°, resume. Watch altitude, mass and dynamic pressure. Cut
throttle after 30 seconds and watch the coast. Periapsis remains below
ground: the vehicle will return. Pause at any time to export CSV data.

## 2. Staging and gravity turn

Start a fresh rocket flight. Enable gravity-turn assist and full throttle.
The assist holds vertical until 1 km, then decreases pitch by one degree
per 750 m until horizontal. Separate when fuel-depleted appears in the
event log. Compare mass and acceleration immediately before/after staging.
The stage counter changes only on manual separation. The 220 km apoapsis
cutoff is an ascent aid, not an orbit guarantee. Disable the assist to make
manual circularization burns near apoapsis at pitch 0°. A positive periapsis
above the appreciable atmosphere indicates a useful orbit.

## 3. Orbital conservation

Choose Moon / Orbital Probe / New circular orbit. Select Orbit map. Increase
time warp and watch the trajectory close. Apoapsis and periapsis should
remain close to 200 km. Numerical errors accumulate because this is a
finite-step integrator. The included test bounds drift over 600 seconds.

## 4. Prograde burn and reentry

Choose Earth / Helios Two Stage / New circular orbit. Pitch 0°, throttle
20%, resume briefly, then cut throttle. See the orbit elongate. For a
retrograde burn use pitch 180°. Reduce periapsis into the atmosphere and
coast: drag will reduce energy. Heat is not connected to damage, so this
exercise demonstrates orbital decay rather than survivable reentry design.

## 5. Powered wing flight

Choose Earth / Aster Spaceplane / New surface flight. Launch at 90° and
full throttle. Gradually lower pitch as horizontal speed builds. Wing lift
depends on angle of attack relative to the velocity vector. Small changes
can produce large forces at high dynamic pressure. There is no attitude
inertia, trim, runway, or automatic stabilization. Use 1× time and pause
to inspect the response.

## Persistence

Save mission writes the selected world, complete vehicle definition, fuel,
stage, velocity, position, commands and simulation time. Load restores that
state paused. Telemetry and prior event logs do not persist. CSV export
writes only sampled data from the current session and includes units in
column headers. Files are written only to locations chosen in the dialog.

## Troubleshooting

- No liftoff: use sufficient throttle and outward pitch; local gravity and
  initial mass determine thrust-to-weight. An unpowered object cannot launch.
- Vehicle falls after staging: verify next-stage fuel and thrust in the lab.
- Black executable window or missing logos: extract the whole artifact and
  retain `_internal`; do not move the EXE alone.
- No Actions run: verify the workflow is at the repository root's `.github`
  path, Actions is enabled, and use Run workflow on the default branch.
- `No module named tkinter`: install your platform's Tk support for Python.
- Keyboard controls inactive: click the canvas to leave text entry focus.
