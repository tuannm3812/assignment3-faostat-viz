# Assignment Requirements Summary

## Project Brief

The Data Narrative Studio asks each group to act as a specialist data consultancy. The final product must transform complex, multi-dimensional, real-world data into an interactive and persuasive data narrative. The goal is a human-centred story that convinces with evidence and supports a clear stakeholder action.

## Assessment Context

- Assignment 3 total weighting: 40%.
- Part 3 weighting: 20%.
- Format: group project.
- Tooling: Tableau or Streamlit, GitHub, and SharePoint/Teams.
- Part 3 deliverable: final portfolio with hosted dashboard, walkthrough video, and technical documentation.

## Subject Intended Learning Outcomes

The project assesses the ability to:

- **SILO 1:** Justify data selection and analysis for stakeholder-specific data narratives.
- **SILO 2:** Apply visualisation and narrative techniques across varied data types.
- **SILO 3:** Justify narrative tools and techniques that clarify critical aspects of a problem.
- **SILO 4:** Communicate data narratives to stakeholders using relevant evidence, analysis, and patterns.

## Data Requirements

The final portfolio must use real-world, recent data. Synthetic or overused datasets such as Titanic, Superstore, and Iris are not acceptable.

The data must:

- be collected from 2024 onwards, or include earlier data points from a source actively collected or updated in 2026;
- include temporal variables, spatial variables, or both;
- support at least four purposeful visuals;
- ideally combine multiple datasets to reveal stronger "So what?" insights.

## Human-Centred Design Requirements

The dashboard must be designed for a specific audience and supported by clear user stories. The design should include:

- a defined stakeholder persona;
- user needs and acceptance criteria;
- visual choices informed by Gestalt principles, pre-attentive attributes, and cognitive load reduction;
- accessible colour contrast, readable layout, and intuitive controls.

Selected stakeholder persona:

> UN Food Systems Summit Panel or a regional food-security policy board.

## Advanced Feature Requirement

The dashboard must include at least three advanced features or tool-specific equivalents. This project implements:

- **Context-aware filtering:** sidebar selections update charts, rankings, metrics, and narrative text.
- **Visual tooltips:** hover states reveal deeper country, commodity, and methodology details.
- **Guided narrative layout:** tabs lead viewers through the story from context to action.
- **What-if parameterisation:** sliders model alternative scenario assumptions.
- **Sensitivity analysis:** priority countries are tested across alternative exposure weights.

## Narrative Structure

The selected narrative structure is **Sparkline**:

- "What is": global food-price and producer-price shock evidence.
- "What could happen": scenario-based pressure rankings under alternative assumptions.
- "What should happen next": prioritised monitoring and preparedness for countries with high hunger-import exposure.

## Part 3 Portfolio Requirements

The final portfolio must include:

- hosted dashboard on Streamlit Cloud or Tableau Public;
- consistent design system, custom palette or Streamlit configuration, and responsive load times;
- 3-minute video walkthrough explaining code logic or Tableau organisation and highlighting advanced features;
- data dictionary, source provenance, methodology, limitations, and credits;
- clear code organisation and useful annotations where implementation choices are not self-evident.

## Dashboard Decision Question

For the selected food-security policy audience, the dashboard should answer:

- When have global food-price and Australia/New Zealand producer-price signals intensified?
- Which commodities show the strongest or most volatile signals?
- Which countries combine hunger vulnerability with food-import dependency?
- Under alternative producer-price shock assumptions, which countries should be prioritised for monitoring, preparedness, or policy support?

Recommended action:

> Use hunger-import exposure as an early-warning layer when producer-price and global food-price signals rise together.
