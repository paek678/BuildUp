# Project Overview

BuildUp uses Unity ML-Agents PPO to train boss movement policies for a 2-player cooperative boss fight. Training runs, matchup analysis, and ONNX outputs are kept separately from the multiplayer game runtime.

## Project Roles

| Project | Responsibility |
| --- | --- |
| BuildUp | Training environment, player bots, movement policy training, analysis, and ONNX export |
| ArenaCombat_server | Multiplayer authority, combat resolution, skill execution, and movement inference |

## Training Pipeline

Behavior Tree player bots provide opponents for the boss. `BossInferenceAgent` supports Touch, Engage, and Combat training modes, with 129 observation channels and one discrete movement branch containing 5 actions.

The learned policy controls movement. Skill execution is handled separately by the training environment's auto-cast helper. Exported ONNX assets can be assigned to the related ArenaCombat_server runtime.

## Implementation References

- [Observation and action specification](observation-action-spec.md)
- [Matchup analysis](training-analysis.md)
- [Training agent](../../Assets/Scripts/AI/BossAI/Agents/BossInferenceAgent.cs)
- [Observation collector](../../Assets/Scripts/AI/BossAI/Observation/BossObservationCollector.cs)
- [Combat training configuration](../../BossInference_config.yaml)
- [Training change history](../../Assets/CHANGES.md)
- [ArenaCombat_server](https://github.com/paek678/ArenaCombat_server)

## Runtime Alignment and Validation

Observation order, normalization, action indices, and movement behavior must agree between training and runtime. The [observation and action specification](observation-action-spec.md#runtime-alignment) records the current backward-speed difference that requires verification.

Training results and exported models are available in the repository. Final model selection, behavior in a 2-player network session, and combat balance require runtime validation.
