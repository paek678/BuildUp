# Portfolio Overview

BuildUp is the supporting ML training repository for ArenaCombat_server.

The public story should stay focused:

```text
BuildUp trains boss movement policies.
ArenaCombat_server owns the actual multiplayer runtime, combat rules, skill execution, and authority.
```

## Project Positioning

BuildUp uses Unity ML-Agents PPO to train boss movement decisions for a 2-player boss fight scenario. Its value is in the training setup, observation/action design, matchup analysis, and ONNX export path.

## What To Emphasize

- ML-Agents PPO training setup
- 129-channel observation design
- 5 discrete movement actions
- matchup-based performance analysis
- ONNX model outputs
- alignment target with ArenaCombat_server

## What Not To Emphasize

- BuildUp is not the multiplayer runtime.
- BuildUp should not be described as the full boss AI product.
- BuildUp should not claim complete production deployment without runtime validation.

