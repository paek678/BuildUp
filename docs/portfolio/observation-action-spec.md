# Observation & Action Spec

## Observation

The portfolio-facing observation spec is 129 channels.

| Section | Channels |
| --- | ---: |
| Position relations | 11 |
| Boss/player state | 4 |
| Boss skill slots | 35 |
| Touch flags | 2 |
| Player skill slots | 70 |
| Extra battle context | 7 |
| Total | 129 |

## Why This Matters

The observation design includes more than raw positions. It includes combat context such as player skill slots, boss skill slots, cast state, movement state, unlocked slots, and recent battle context.

This makes the movement policy closer to the actual combat problem and helps align the training environment with the ArenaCombat_server runtime.

## Action Space

| Index | Action |
| ---: | --- |
| 0 | idle |
| 1 | forward |
| 2 | turn left |
| 3 | turn right |
| 4 | backward |

## Design Decision

The model is intentionally scoped to movement.

Skill selection is excluded from the ML action space and remains in the rule/runtime layer. This reduces action-space complexity and keeps combat authority in ArenaCombat_server.

