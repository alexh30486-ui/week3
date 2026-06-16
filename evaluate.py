import json
import os

from config import VALID_LABELS, DATA_PATH, TEST_FILE
from classifier import classify_episode, load_labeled_examples


def run_evaluation() -> dict:
    labeled_examples = load_labeled_examples()

    test_path = os.path.join(DATA_PATH, TEST_FILE)

    with open(test_path, encoding="utf-8") as f:
        test_episodes = json.load(f)

    results = []

    for episode in test_episodes:
        print(f"  Classifying: {episode['title'][:60]}...")

        prediction = classify_episode(
            episode["description"],
            labeled_examples
        )

        results.append({
            "id": episode["id"],
            "title": episode["title"],
            "description": episode["description"],
            "ground_truth": episode["label"],
            "predicted": prediction["label"],
            "reasoning": prediction["reasoning"],
            "correct": prediction["label"] == episode["label"],
        })

    predictions = [r["predicted"] for r in results]
    ground_truth = [r["ground_truth"] for r in results]

    return {
        "results": results,
        "predictions": predictions,
        "ground_truth": ground_truth,
        "total": len(results),
    }


def compute_accuracy(
    predictions: list[str],
    ground_truth: list[str]
) -> float:
    if not predictions:
        return 0.0

    correct = sum(
        1
        for prediction, truth in zip(predictions, ground_truth)
        if prediction == truth
    )

    return correct / len(predictions)


def compute_per_class_accuracy(
    predictions: list[str],
    ground_truth: list[str]
) -> dict[str, dict]:
    stats = {
        label: {
            "correct": 0,
            "total": 0,
            "accuracy": 0.0,
        }
        for label in VALID_LABELS
    }

    for prediction, truth in zip(predictions, ground_truth):
        if truth not in stats:
            continue

        stats[truth]["total"] += 1
        if prediction == truth:
            stats[truth]["correct"] += 1

    for label in stats:
        total = stats[label]["total"]
        correct = stats[label]["correct"]

        stats[label]["accuracy"] = (
            correct / total
            if total > 0
            else 0.0
        )

    return stats


def format_evaluation_report(eval_results: dict) -> str:
    predictions = eval_results["predictions"]
    ground_truth = eval_results["ground_truth"]
    results = eval_results["results"]

    accuracy = compute_accuracy(
        predictions,
        ground_truth
    )

    per_class = compute_per_class_accuracy(
        predictions,
        ground_truth
    )

    lines = [
        "## Evaluation Results\n",
        f"**Overall accuracy:** {accuracy:.1%} "
        f"({sum(r['correct'] for r in results)}/{eval_results['total']})\n",
        "\n**Per-class accuracy:**",
    ]

    for label, stats in per_class.items():
        bar = (
            "█" * int(stats["accuracy"] * 10)
            + "░" * (10 - int(stats["accuracy"] * 10))
        )

        lines.append(
            f"  {label:<12} "
            f"{bar}  "
            f"{stats['accuracy']:.0%}  "
            f"({stats['correct']}/{stats['total']})"
        )

    misclassified = [
        r for r in results
        if not r["correct"]
    ]

    if misclassified:
        lines.append(
            f"\n**Misclassified ({len(misclassified)}):**"
        )

        for r in misclassified:
            lines.append(
                f"  [{r['ground_truth']} → {r['predicted']}] "
                f"{r['title']}"
            )
    else:
        lines.append(
            "\n**No misclassifications — perfect score!**"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print("\nRunning evaluation...\n")

    evaluation_results = run_evaluation()

    report = format_evaluation_report(
        evaluation_results
    )

    print(report)

