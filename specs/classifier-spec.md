# Classifier Spec — Pod Classifier

## build_few_shot_prompt(labeled_examples, description)

### What output format should you request from the LLM?

```text
Return ONLY a valid JSON object.

Do not include markdown.
Do not include code fences.
Do not include explanatory text before or after the JSON.

Required schema:

{
  "label": "interview|solo|panel|narrative",
  "reasoning": "brief explanation"
}

Rules:

- label must be exactly one of:
  interview
  solo
  panel
  narrative

- reasoning should be concise (1–3 sentences)

- if uncertain, choose the closest matching label and explain the uncertainty

Example:

{
  "label": "interview",
  "reasoning": "The description centers on a host speaking with a guest about their experiences."
}
```

### Edge cases to handle in the prompt

```text
If labeled_examples is empty:

- Perform zero-shot classification using the taxonomy definitions.
- Still return valid JSON.

If the description is extremely short:

- Use whatever evidence is available.
- Infer the most likely label.
- Mention uncertainty in the reasoning field.

If the description is empty:

- Return the closest possible classification based on available information.
- Explain that insufficient evidence was provided.

Always return valid JSON regardless of input quality.

Never invent labels outside the four valid categories.
```

---

## classify_episode(description, labeled_examples)

### Step 3 — Parse the response

```text
Primary strategy:

1. Extract:

   response_text = response.choices[0].message.content

2. Attempt direct parsing:

   parsed = json.loads(response_text)

3. If parsing fails:

   Use regex extraction:

   match = re.search(r"\{.*\}", response_text, re.DOTALL)

4. If a JSON object is found:

   parsed = json.loads(match.group(0))

5. Extract:

   label = parsed.get("label", "")
   reasoning = parsed.get("reasoning", "")

6. Normalize:

   label = label.strip().lower()

7. If reasoning is missing:

   reasoning = ""

8. If parsing completely fails:

   return {
       "label": "unknown",
       "reasoning": "Unable to parse LLM response."
   }
```

### Step 4 — Validate the label

```text
Normalize:

label = label.strip().lower()

If label is not in VALID_LABELS:

    label = "unknown"

VALID_LABELS contains:

{
    "interview",
    "solo",
    "panel",
    "narrative"
}

Reasoning should still be preserved whenever possible.

Never raise an exception for invalid labels.
```

### Step 5 — Handle errors gracefully

```text
Potential failures include:

- Groq API unavailable
- Authentication failure
- Network timeout
- Rate limiting
- Empty response
- Missing response fields
- Malformed JSON
- Unexpected response structure
- Regex extraction failure

The classifier should never crash the evaluation loop.

Wrap the entire classification process inside try/except.

If any exception occurs:

return {
    "label": "unknown",
    "reasoning": f"Classification error: {str(error)}"
}

This allows batch evaluation to continue even when individual calls fail.
```

---

## Return value structure

```python
{
    "label": str,
    "reasoning": str,
}
```

Where:

* label is one of:

  * interview
  * solo
  * panel
  * narrative
  * unknown

* reasoning is a short explanation from the model or parser.

---

## Implementation Notes

### Test: what does the raw LLM response look like for one episode?

```text
Episode tested: Example Episode

Raw response text:

{
  "label": "interview",
  "reasoning": "The episode description clearly indicates a host speaking with a guest."
}
```

### How did you parse the label out of the response?

```text
1. Read the raw response text.
2. Attempt json.loads().
3. If that fails, use regex extraction:
   re.search(r"\{.*\}", response_text, re.DOTALL)
4. Parse extracted JSON.
5. Retrieve:
   parsed["label"]
   parsed["reasoning"]
6. Normalize label using:
   strip()
   lower()
7. Validate against VALID_LABELS.
```

### Did any episodes return "unknown"? If so, why?

```text
Expected: Rarely.

Possible reasons:

- Model returned malformed JSON.
- API response was empty.
- Network error occurred.
- Model generated a label outside VALID_LABELS.

In those situations the parser safely falls back to:

{
    "label": "unknown",
    "reasoning": "Description of failure"
}
```


