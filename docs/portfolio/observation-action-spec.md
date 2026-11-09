# Observation & Action Spec

## Observation

`BossObservationCollector.CollectFull129` collects 129 observation channels for the movement policy.

| Section | Channels |
| --- | ---: |
| Position relations | 11 |
| Boss/player state | 4 |
| Boss skill slots | 35 |
| Touch flags | 2 |
| Player skill slots | 70 |
| Extra battle context | 7 |
| Total | 129 |

## Combat Context

The observations include positions and combat context: player and boss skill slots, casting state, player movement speed, unlocked slots, and recent damage. Channel order and normalization must remain consistent with the ArenaCombat_server observation collector.

## Action Space

| Index | Action |
| ---: | --- |
| 0 | idle |
| 1 | forward |
| 2 | turn left |
| 3 | turn right |
| 4 | backward |

## Design Decision

The model selects movement actions. Skill selection and execution remain in the auto-cast and combat systems, which keeps the movement policy separate from skill rules and multiplayer authority.

## Runtime Alignment

Action index meanings match the runtime's `BossInferenceAgent`, but the current movement implementations differ: the training agent applies `BackwardSpeedScale = 0.7f`, while the runtime's backward action uses the full configured movement speed. This difference requires verification before treating a model as directly interchangeable between the two environments.

The channel count and action mapping describe the interface. They do not establish that all movement parameters or serialized scene settings are identical.

## Implementation References

- [Training agent](../../Assets/Scripts/AI/BossAI/Agents/BossInferenceAgent.cs)
- [Observation collector](../../Assets/Scripts/AI/BossAI/Observation/BossObservationCollector.cs)
- [ArenaCombat_server runtime](https://github.com/paek678/ArenaCombat_server)
