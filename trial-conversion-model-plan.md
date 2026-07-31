# Model Plan: Early Trial Conversion Prediction

| **Driver**       | Data Science                                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Requested by** | Growth team                                                                                                                                                        |
| **Informed**     | Lifecycle, Growth Analytics, Finance                                                                                                                               |
| **Objective**    | Predict, from a trial's first 3 days of behavior, whether it will convert to a paid plan, early enough for the growth team to intervene on the ones that will not. |
| **Date**         | September 8, 2026                                                                                                                                                  |
| **Key outcomes** | A validated day-3 conversion signal, and if it proves out, a deployed and monitored scoring service that the lifecycle, analytics, and finance teams can rely on.  |
| **Status**       | `IN PROGRESS` (prototype)                                                                                                                                          |

## Background and request

Beam is a subscription media app where people browse, listen to, and read content. Users are either on the free tier, which is limited, or on a paid plan. On August 1, Beam launched something new: a 14-day free trial of the full paid product. A user who starts a trial gets complete access for two weeks. When the two weeks are up, the trial converts into a paid subscription automatically, unless the user cancels before the end.

The trial has been popular. Roughly 250 people start one every week. The problem is how the trials end. Only about half of them convert into a paid subscription; the other half cancel. When the company decided to build the trial, the business case assumed that closer to 6 out of 10 would convert, so we are running below what was promised.

Today, the growth team only learns how a trial went once it is over, and by then there is nothing left to do about it. Their request is simple to state: they want to know, while a trial is still running, whether it is likely to end in a cancellation, and they want to know early enough to still have time to act.

## The question the model answers

> For a trial that started three days ago, how likely is it to convert to a paid plan at the end of day 14?

**Why day 3?** By day 3 there is enough behavior to read, and there are still 11 days left in the trial, which is enough time for an intervention to matter.

**What do we expect to matter?** From an initial look at completed trials, the behavior that seems most informative is straightforward:

- How much the person actually used the app in those first days.
- Whether that usage was spread across several days, or packed into the first day and then abandoned.
- How much of the usage was listening, because audio is the main feature the paid product unlocks.

## Who needs it and what they will do

Three teams asked for this, and each would use it differently.

| Team | What they want | What they will do with it |
|---|---|---|
| Lifecycle (Growth) | A daily list of live trials, ranked by how likely each is to cancel. | Focus the trial nurture flow, meaning the onboarding emails, the prompts toward audio content, and, for some segments, a discount offer, on the trials that actually need help. |
| Analytics (Growth) | Current scores for live trials, available on demand. | Build fair test groups when running experiments on users who are mid-trial. |
| Finance | Predicted conversion summed up per weekly cohort. | Replace the fixed conversion assumption in the revenue forecast with a number grounded in actual behavior. |

One note on the lifecycle list: how far down it the team goes depends on how many users their tools can reach in a day, so the score cutoff is their decision to make, not ours.

## Value, order of magnitude

The numbers here are rough estimates meant to size the opportunity, not measured results.

- Every month, roughly 500 trials end in cancellation.
- Suppose the nurture flow, pointed at the right trials early enough, could rescue even 5 to 10 percent of them.
- That would mean 25 to 50 additional paying subscribers every month. Most converters choose the monthly plan, so each save keeps paying month after month, and the gains stack.

There is also a second, less obvious reason this matters. The case for having a trial at all was built on the assumption of a 58 percent conversion rate. Every point we fall below that number weakens the argument for keeping the trial, and every point we recover strengthens it.

## Roadmap

1. **Prototype:** We start by building the model offline, using the trials that have already completed, to confirm that the first three days of behavior carry enough signal to be worth acting on. Success here means clearly beating what the team does today, which is judging trials by their raw session counts. If the signal turns out to be too weak, we stop at this stage and report that.
2. **Deployment and monitoring:** Once the prototype proves out, the model has to become something the teams can rely on every day. That means deploying it so that live trials are scored daily and scores are available whenever the analytics team asks, and it means monitoring it in production so that we notice when its accuracy starts to slip, rather than discovering the problem months later in the conversion numbers. Monitoring matters more than usual here: the trial launched alongside a large marketing campaign, and people arriving through a campaign behave differently from the users who will arrive once acquisition settles back to normal. When the monitoring shows that the trial population has drifted away from what the model was trained on, that is our signal to retrain it on newer cohorts. We will scope the deployment work together with the engineering team.

## Out of scope for now

- **Churn among existing paid subscribers:** That is a different problem with a different timeline, and it belongs to a separate project.
- **Uplift modeling:** This asks a harder question: not "who is likely to cancel" but "who can actually be persuaded." It becomes worth asking once the nurture flow has run long enough to produce data about which interventions work.
- **Changes to the trial itself:** Its length, price, and eligibility rules all stay as they are.
