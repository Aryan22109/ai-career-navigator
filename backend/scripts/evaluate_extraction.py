"""Measure skill-extraction quality against hand-labelled resumes.

Usage:  python scripts/evaluate_extraction.py [directory_with_txt_and_json_pairs]

Each rN.txt needs a matching rN.json containing the list of skills (canonical names
from app/skills_data.py) a human reader would extract from that resume.
Add your own anonymised resumes to get a number that reflects real data.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.parser import parse_resume  # noqa: E402


def main(folder: Path) -> None:
    tp = fp = fn = 0
    for txt in sorted(folder.glob("*.txt")):
        truth = set(json.loads(txt.with_suffix(".json").read_text()))
        pred = set(parse_resume(txt.read_text()).skills)
        tp += len(truth & pred); fp += len(pred - truth); fn += len(truth - pred)
        print(f"{txt.name}: missed={sorted(truth - pred)} spurious={sorted(pred - truth)}")
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    accuracy = tp / (tp + fp + fn) if tp + fp + fn else 0
    print(f"\nprecision={precision:.1%} recall={recall:.1%} f1={f1:.1%} accuracy(tp/(tp+fp+fn))={accuracy:.1%}")
    print(f"labelled resumes: {len(list(folder.glob('*.txt')))}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "tests/data/labeled")
