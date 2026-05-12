# Part 2 Deck Feedback and Dashboard Improvements

## Quick Review of Team Draft Deck

The draft deck has a strong narrative direction: it opens with global food price shocks, narrows to Australia/New Zealand producer prices, then moves to country vulnerability and action. This fits the assignment brief well because it is not just a status dashboard; it is a persuasive story for the UN Food Systems Summit Panel.

Main strengths:

- Clear stakeholder framing: UN Food Systems Summit Panel.
- Strong human-centred question: who pays when food prices spike?
- Good narrative arc: context -> AUS/NZ signal -> vulnerable countries -> recommendations.
- Good visual focus on FFPI, wheat, vulnerability, and what-if impact.
- Honest limitations slide reduces Q&A risk.

Main fixes before presenting:

- Slides 2 and 3 are almost duplicates. Keep one stronger context slide.
- Slide numbering says 08 slides, but the deck has 9 slides.
- Some claims are too strong: say "structural exposure to global food-price pressure" rather than "AUS/NZ shocks cause these countries' import costs."
- The fixed transmission assumptions need careful wording. The dashboard uses a safer pass-through slider because producer prices are not import prices.
- Add one live-dashboard moment so Part 2 proves the prototype is interactive, not only static screenshots.

## Dashboard Improvements Added

I added a new Streamlit page: `Part 2 Pitch Brief`.

This page is designed for the presentation flow and contains four live visuals:

1. **FFPI Shock Context**
   - Reason: opens the story with the global shock pattern.
   - Assignment fit: temporal data, narrative framing, crisis annotation.

2. **Wheat Producer Price Signal**
   - Reason: wheat is an intuitive indicator commodity and links AUS/NZ producer prices to the global food-price story.
   - Assignment fit: persuasive evidence object, not just an overview metric.

3. **Undernourishment x Food Import Exposure**
   - Reason: improves Chaitya's vulnerability method by using undernourishment where available, which is more directly food-price sensitive than broad GHI.
   - Assignment fit: human-centred design and enriched data join.

4. **Scenario Priority Ranking**
   - Reason: turns the analysis into action by showing which countries should be monitored first under a selected shock and pass-through assumption.
   - Assignment fit: what-if parameterisation and call to action.

## Suggested Part 2 Slide Content

### Slide: Prototype Improvement

**Claim title:** We turned the analysis into a live decision tool.

**Body copy:**

The dashboard now follows the same persuasive arc as the pitch: global shock context, AUS/NZ wheat signal, human exposure, and scenario-based prioritisation. This lets the UN panel move from "what happened" to "who needs monitoring first".

**Proof to show live:**

Open `Part 2 Pitch Brief` in the Streamlit sidebar.

**Speaker note:**

"We added this page because the assignment asks for an interactive persuasive narrative, not a static status dashboard. Each visual supports one decision: understand the shock, identify the supply-side signal, locate exposed populations, and prioritise action."

### Slide: Why We Added the Wheat Signal

**Claim title:** Wheat makes the global shock visible.

**Body copy:**

Wheat is a globally important staple and a clear indicator commodity for food-price stress. Showing AUS/NZ wheat producer prices beside the FFPI helps the audience see why local producer-price movements matter in the wider food-security story.

**Speaker note:**

"We are not claiming every vulnerable country imports wheat from Australia or New Zealand. We use wheat as a signal commodity because it is understandable, globally relevant, and visibly aligned with major food-price shocks."

### Slide: Why We Changed the Vulnerability Lens

**Claim title:** Hunger severity needs a food-access measure.

**Body copy:**

The refined dashboard uses undernourishment where available, combined with food import dependency. This is stronger than raw `GHI x import %` because undernourishment is closer to the lived food-access problem, while import dependency describes the exposure channel.

**Speaker note:**

"This keeps the model transparent: 60% hunger/access pressure and 40% import exposure. It is a prioritisation index, not a causal forecast."

### Slide: What-If Scenario

**Claim title:** The scenario converts insight into action.

**Body copy:**

The what-if sliders let the panel test a producer-price shock and pass-through assumption. The ranking does not predict exact import bills; it identifies which countries should be monitored first when global food-price pressure rises.

**Speaker note:**

"We deliberately avoid one-to-one shock claims. Producer prices are filtered through exchange rates, shipping, substitution, margins, and policy. That is why pass-through is adjustable."

## Recommended Live Demo Script

1. Start on `Part 2 Pitch Brief`.
2. Show FFPI shock context and say: "The world has seen repeated food-price storms."
3. Scroll to wheat and say: "Here is the AUS/NZ signal commodity we use to connect local producer prices to the global story."
4. Scroll to exposure and say: "The human issue is not price alone; it is price pressure landing on countries with hunger and import exposure."
5. Move the scenario sliders and say: "This is the action layer: not a forecast, but an early-warning prioritisation tool."

## Final Recommendation

Use the team deck for the emotional narrative, but use the live dashboard as proof of technical implementation. Keep the language careful: our dashboard identifies structural exposure to global food-price pressure; it does not prove direct bilateral trade dependence on Australia or New Zealand.
