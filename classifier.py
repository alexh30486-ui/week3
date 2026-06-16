import json
import os
import re  # We need this to extract the JSON safely
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_LABELS, DATA_PATH, TRAIN_FILE, LABELS_FILE

_client = Groq(api_key=GROQ_API_KEY)


def load_labeled_examples() -> list[dict]:
    """
    Load the training episodes and merge them with the student's labels.
    """
    train_path = os.path.join(DATA_PATH, TRAIN_FILE)
    labels_path = os.path.join(DATA_PATH, LABELS_FILE)

    with open(train_path, encoding="utf-8") as f:
        episodes = {ep["id"]: ep for ep in json.load(f)}

    with open(labels_path, encoding="utf-8") as f:
        labels = {entry["id"]: entry["label"] for entry in json.load(f)}

    labeled = []
    for ep_id, ep in episodes.items():
        label = labels.get(ep_id)
        if label in VALID_LABELS:
            labeled.append({**ep, "label": label})

    return labeled


def build_few_shot_prompt(labeled_examples: list[dict], description: str) -> str:
    """
    Build a few-shot classification prompt using the student's labeled training examples.
    """
    # 1. System Instruction & JSON Output Format
    prompt = (
        "You are an expert podcast classifier. Your task is to categorize episodes "
        f"into one of the following formats: {', '.join(VALID_LABELS)}.\n\n"
        "You must respond ONLY with a valid JSON object in the exact following format:\n"
        '{"label": "your_label_here", "reasoning": "A brief 1-sentence explanation"}\n\n'
        "EXAMPLES:\n"
    )
    
    # 2. Few-Shot Examples (Dynamically loaded from your labeled data)
    # We use the first 5 so the prompt doesn't get too massive
    for ex in labeled_examples[:5]: 
        prompt += (
            f"Description: {ex['description']}\n"
            f'Output: {{"label": "{ex["label"]}", "reasoning": "This matches the {ex["label"]} format."}}\n\n'
        )
    
    # 3. The Target Episode
    prompt += (
        "Now, classify the following episode:\n"
        f"Description: {description}\n"
        "Output:"
    )
    
    return prompt


def classify_episode(description: str, labeled_examples: list[dict]) -> dict:
    """
    Classify a single podcast episode description using the few-shot LLM classifier.
    """
    # Step 1: Call build_few_shot_prompt() to construct the prompt
    prompt = build_few_shot_prompt(labeled_examples, description)
    
    try:
        # Step 2: Send it to the LLM
        response = _client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=LLM_MODEL,
            temperature=0.0  # Zero makes the model's output more deterministic and less creative
        )
        response_text = response.choices[0].message.content
        
        # Step 3: Parse the response to extract JSON safely
        # This regex looks for everything between the first { and last }
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response.")
            
        parsed_data = json.loads(json_match.group(0))
        
        # Step 4: Validate the label
        raw_label = parsed_data.get("label", "").strip().lower()
        reasoning = parsed_data.get("reasoning", "No reasoning provided.")
        
        if raw_label in VALID_LABELS:
            return {"label": raw_label, "reasoning": reasoning}
        else:
            return {"label": "unknown", "reasoning": f"LLM returned invalid label: {raw_label}"}
            
    except Exception as e:
        # Step 5: Handle crashes gracefully so the loop doesn't break
        return {
            "label": "unknown",
            "reasoning": f"Classification error: {str(e)}"
        }
