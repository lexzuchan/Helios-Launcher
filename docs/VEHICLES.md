# Vehicle lab

Open **Vehicle editor** to edit the current configuration. Applying a
configuration starts a new paused surface flight in the selected world.
Save a mission to preserve the custom configuration. To reuse the example
files, paste their JSON into the editor. No code editing is required.

| Field | Meaning |
| --- | --- |
| name | Display name |
| kind | `rocket`, `plane`, or `object` |
| payload | Persistent mass in kg; strictly positive |
| area | Reference drag area in m² |
| cd | Dimensionless body drag coefficient |
| wing | Wing area in m²; use 0 to disable lift |
| stages | Array ordered first-burning stage to last-burning stage |
| stages[].dry | Stage structure mass in kg |
| stages[].fuel | Propellant mass in kg |
| stages[].thrust | Maximum thrust in newtons |
| stages[].isp | Specific impulse in seconds |

Up to ten stages are allowed. Stage parameters must be finite positive
numbers. Use an empty stages array for unpowered objects. Payload is always
retained. Each stage's dry mass and remaining fuel are retained until
manual separation. Separating the final stage does nothing. Plane kind
enables the 30 km engine cutoff; wing area independently enables lift.

Changing kind does not select a different force model for gravity or drag.
The rocket gravity-turn assist only acts on `rocket` kind. The simulator
does not impose realistic structural or engine-design limits on editor
values; very extreme values can make a fixed-step simulation unstable.
