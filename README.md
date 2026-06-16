# Podcast Episode Classifier

A robust, LLM-powered classification pipeline that sorts podcast episodes into four distinct categories: **interview**, **solo**, **panel**, and **narrative**.

## Taxonomy Definitions
- **interview:** Host speaks with a single guest.
- **solo:** Host speaks alone.
- **panel:** Host facilitates a roundtable with multiple guests.
- **narrative:** Story-driven, produced content.

## Implementation Details
- **Base Model:** Groq API (using Llama models).
- **Strategy:** Few-shot prompting with deterministic temperature (0.0).
- **Error Handling:** Implemented a regex-based JSON parser and batch-continuity guards to ensure the evaluation loop never crashes on API failures.

## Evaluation Results
The system achieved **100% accuracy** on the test set of 20 episodes.

| Label | Accuracy |
| :--- | :--- |
| interview | 100% (5/5) |
| solo | 100% (5/5) |
| panel | 100% (5/5) |
| narrative | 100% (5/5) |

## Setup Instructions
1. Install dependencies: `pip install -r requirements.txt`
2. Configure your API key: `cp .env.example .env` (and add your key).
3. Run evaluation: `python3 evaluate.py`

## AI Usage Disclosure
- **Constraint Enforcement:** I directed the AI to follow a strict JSON schema and used regex to sanitize outputs.
- **Annotation Assistance:** I utilized the model to validate label consistency and relied on few-shot examples to "teach" the taxonomy boundaries.
