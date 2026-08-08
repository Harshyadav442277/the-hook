# THE HOOK — Devpost submission copy

## One-line pitch

THE HOOK turns a high-pressure MLB bullpen decision into an explainable, interactive Manager-vs-Model comparison.

## Inspiration

Bullpen decisions are made in seconds, but post-game analysis often reduces them to hindsight: the move worked or it did not. We wanted a fairer and more useful question—given the score, base/out state, upcoming hitters, workload, and information available at that moment, which plausible reliever projected best under the same assumptions?

## What it does

THE HOOK replays three verified MLB pitching changes. For each situation it shows the real managerial choice, ranks four plausible relievers, estimates win probability and expected runs over the next three hitters, and explains the model recommendation. A judge can switch relievers and see every dependent metric and reason update immediately.

Our flagship is the bases-loaded, two-out 12th inning of Game 3 of the 2025 World Series. The Dodgers chose Clayton Kershaw; THE HOOK recommends leaving Emmet Sheehan in and estimates a +3.6-percentage-point advantage under its shared assumptions.

## How we built it

We processed 1.27 million MLB Statcast pitches into 324,435 modelable plate appearances. Player profiles are prior-only and shrunk toward fixed league priors to control small samples. A regularized four-outcome multinomial logistic model projects out, walk/HBP, single, and extra-base-hit probabilities. A vectorized NumPy engine simulates up to the next three hitters 2,000 times per candidate, then a chronological logistic game-state model estimates win expectancy.

The matchup model is validated on a strictly later 2026 holdout. Its multiclass log loss is 0.9645 versus 0.9700 for the league-rate baseline. The state model's holdout log loss is 0.4743 versus 0.6927 for a constant baseline. Explanations are deterministic and traceable to stored profile values—no LLM is used.

## Challenges

The hardest work was not adding complexity; it was enforcing point-in-time correctness. We built restartable, checksummed Statcast chunks, normalized source-specific inning labels, caught and corrected a bottom-half team assignment bug through official-feed review, reconstructed base occupancy from simultaneous runner movements, and verified every selected scenario against MLB play-by-play.

## Accomplishments

- Three complete, source-reviewed historical scenarios.
- A responsive two-page Streamlit decision room with no runtime network calls.
- Deterministic rankings in under half a second for all 12 candidate simulations locally.
- Chronological validation, calibration, explicit limits, and 26 automated tests.
- A 25 KB scenario artifact and small deployable models instead of shipping raw data.

## What we learned

Sports decision support becomes more credible when every candidate shares the same assumptions and the product is honest about close calls. One scenario has a clear 3.6-point recommendation; another is an effective tie. THE HOOK presents both without manufacturing certainty.

## What's next

Future work could add official roster/availability context, richer baserunning, pitch-family interactions, and uncertainty from model specification—not just simulation noise. The prototype intentionally keeps those outside the hackathon scope.

## Actionable impact

Managers and analysts can use the interface to compare bullpen options consistently before or after a game. Broadcasters and fans get a transparent alternative to result-based hindsight, while every recommendation remains inspectable and appropriately qualified.
