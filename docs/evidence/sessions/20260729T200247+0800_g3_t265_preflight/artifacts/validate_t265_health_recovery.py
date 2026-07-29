#!/usr/bin/env python3
import json
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_t265_health_recovery.py RESULT.json")
    with open(sys.argv[1], encoding="utf-8") as stream:
        raw = json.load(stream)

    minimum_quality = 50
    qualities = [event["value"] for event in raw["quality_events"]]
    epochs = [event["value"] for event in raw["source_epoch_events"]]
    healthy_before_loss = False
    recovered_after_loss = False
    saw_loss = False
    for quality in qualities:
        if quality == 0:
            saw_loss = True
        elif quality >= minimum_quality:
            if not saw_loss:
                healthy_before_loss = True
            else:
                recovered_after_loss = True

    report = {
        "source_result": sys.argv[1],
        "production_minimum_quality": minimum_quality,
        "observed_quality_sequence": qualities,
        "observed_source_epoch_sequence": epochs,
        "note": (
            "The adapter's integer expression maps confidence 2 to 66. "
            "Its source comment says 67; production minimum_quality is 50."
        ),
        "status": (
            "PASS"
            if healthy_before_loss
            and saw_loss
            and recovered_after_loss
            and len(set(epochs)) >= 2
            and epochs == sorted(epochs)
            and all(
                count == 0
                for count in raw["maximum_input_publisher_counts_at_end"].values()
            )
            else "FAIL"
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
