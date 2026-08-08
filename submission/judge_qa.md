# Judge Q&A

## Why only three scenarios?

The product is a curated decision simulator, not a universal game browser. Three verified cases let us guarantee correct state, candidates, profiles, and narrative while keeping the demo reliable.

## Is the +3.6-point result causal?

No. It is a comparative model estimate under shared assumptions. The app explicitly avoids “would have won” language and exposes the simplifications.

## How do you prevent leakage?

Training rows use cumulative player features before the target plate appearance. Scenario inference selects the latest monthly snapshot strictly before the game date. Validation is chronological: 2025 train, 2026 holdout.

## Why logistic regression?

It is stable, compact, inspectable, fast, and beats the pooled baseline on the untouched holdout. The hackathon problem rewards actionable, explainable analysis more than unnecessary model complexity.

## How are small samples handled?

Every player rate is pooled toward fixed league priors with a 200-PA prior. Cold starts fall back to those priors.

## Are the candidate relievers truly available?

Candidate pools come from each club's prior 30 days of relief usage, exclude pitchers already used in the game, and include the actual decision and current pitcher. This is a plausible-availability approximation, not an official bullpen-status feed.

## Why three hitters?

It matches the practical reliever decision horizon, keeps the simulation interpretable, and avoids making an under-supported full-game player-level forecast.

## Does the deployed app call MLB?

No. Acquisition, verification, training, and name resolution happen offline. The app loads only compact committed artifacts.
