# Architecture 2.0

```text
                     ┌─────────────────────────────┐
TI IWR6843 UART ───> │ reconnecting radar worker  │ ──┐
                     └─────────────────────────────┘   │
                                                       v
                                                bounded FrameBus
                                                       ^
                     ┌─────────────────────────────┐   │
RealSense D435i ───> │ reconnecting vision worker │ ──┘
                     └─────────────────────────────┘
                                                       |
                                             timestamp matcher
                                                       |
                                             trust-aware fusion
                                                       |
                                      covariance-bearing measurements
                                                       |
                                          Kalman/Hungarian tracker
                                                       |
                      ┌────────────────────────────────┼─────────────────────┐
                      v                                v                     v
                scene memory                    active-scan advice      async recorder
                      |                                |                     |
                      └────────────────────────────────┴──────────────┬──────┘
                                                                      v
                                                          API / metrics / dashboard
```

## Design principle
The real-time path is bounded at every queue. When overloaded, it sacrifices old data rather than increasing latency without limit.
