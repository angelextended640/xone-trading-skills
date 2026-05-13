#!/usr/bin/env python3
"""
Bubble-O-Meter: multi-factor bubble-risk score for the US equity market.

Eight indicators each scored 0-2; total (0-16) maps to a bubble phase:
- 0-4: Normal
- 5-8: Watch
- 9-12: Euphoria
- 13-16: Critical

Usage:
    python bubble_scorer.py --ticker SPY --period 1y
"""

import argparse
import json
from datetime import datetime


class BubbleScorer:
    """Bubble-risk scoring system."""

    def __init__(self):
        self.indicators = {
            "mass_penetration": {
                "name": "Mass Penetration",
                "weight": 2,
                "description": "Endorsements / mentions from outside the investor community",
            },
            "media_saturation": {
                "name": "Media Saturation",
                "weight": 2,
                "description": "Spike in search interest, social media, and press coverage",
            },
            "new_accounts": {
                "name": "New Accounts & Inflows",
                "weight": 2,
                "description": "Acceleration in new brokerage accounts and fund inflows",
            },
            "new_issuance": {
                "name": "New Issuance Flood",
                "weight": 2,
                "description": "IPO / SPAC / theme-product proliferation",
            },
            "leverage": {
                "name": "Leverage",
                "weight": 2,
                "description": "Imbalances in margin debt, lending balances, and funding rates",
            },
            "price_acceleration": {
                "name": "Price Acceleration",
                "weight": 2,
                "description": "Returns reaching the high end of the historical distribution",
            },
            "valuation_disconnect": {
                "name": "Valuation Disconnect",
                "weight": 2,
                "description": "Fundamentals replaced by pure narrative",
            },
            "breadth_expansion": {
                "name": "Breadth & Correlation",
                "weight": 2,
                "description": "Low-quality names also rally, broad participation",
            },
        }

    def calculate_score(self, scores: dict[str, int]) -> dict:
        """Compute the overall assessment from per-indicator scores.

        Args:
            scores: dict of indicator → score (0-2)

        Returns:
            dict with phase, risk_level, total_score, etc.
        """
        total_score = sum(scores.values())
        max_score = len(self.indicators) * 2

        # Determine bubble phase
        if total_score <= 4:
            phase = "Normal"
            risk_level = "Low"
            action = "Continue with normal investment strategy"
        elif total_score <= 8:
            phase = "Watch"
            risk_level = "Medium"
            action = "Begin partial profit-taking; reduce new position sizing"
        elif total_score <= 12:
            phase = "Euphoria"
            risk_level = "High"
            action = (
                "Accelerate staged profit-taking; tighten ATR trailing stops; "
                "cut total risk budget by 30-50%"
            )
        else:
            phase = "Critical"
            risk_level = "Very High"
            action = (
                "Take significant profits or fully hedge; halt new entries; "
                "consider short positions after a confirmed reversal"
            )

        # Estimate Minsky phase
        minsky_phase = self._estimate_minsky_phase(scores, total_score)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_score": total_score,
            "max_score": max_score,
            "percentage": round(total_score / max_score * 100, 1),
            "phase": phase,
            "risk_level": risk_level,
            "minsky_phase": minsky_phase,
            "recommended_action": action,
            "indicator_scores": scores,
            "detailed_indicators": self._format_indicator_details(scores),
        }

    def _estimate_minsky_phase(self, scores: dict[str, int], total: int) -> str:
        """Estimate the Minsky / Kindleberger phase."""
        mass_pen = scores.get("mass_penetration", 0)
        media = scores.get("media_saturation", 0)
        price_acc = scores.get("price_acceleration", 0)

        if total <= 4:
            return "Displacement / Early Boom"
        elif total <= 8:
            if media >= 1 and price_acc >= 1:
                return "Boom (expansion)"
            else:
                return "Displacement / Early Boom"
        elif total <= 12:
            if mass_pen >= 2 and media >= 2:
                return "Euphoria - FOMO is institutionalised"
            else:
                return "Late Boom / Early Euphoria"
        else:
            if mass_pen >= 2:
                return "Peak Euphoria / Profit Taking - reversal imminent"
            else:
                return "Euphoria"

    def _format_indicator_details(self, scores: dict[str, int]) -> list[dict]:
        """Format details for each indicator."""
        details = []
        for key, value in scores.items():
            indicator = self.indicators.get(key, {})
            status = "HIGH" if value == 2 else "MED" if value == 1 else "LOW"
            details.append(
                {
                    "indicator": indicator.get("name", key),
                    "score": value,
                    "status": status,
                    "description": indicator.get("description", ""),
                }
            )
        return details

    def get_scoring_guidelines(self) -> str:
        """Return the scoring guidelines for each indicator."""
        guidelines = """
## Bubble Scoring Guidelines

### 1. Mass Penetration
- 0: Discussion limited to experts and active investors
- 1: General audience aware but still limited as an investment target
- 2: Non-investors (taxi drivers, hairdressers, family) actively endorse / mention

### 2. Media Saturation
- 0: Normal levels of coverage / search interest
- 1: Search interest and social mentions 2-3x normal
- 2: TV specials, magazine covers, search interest spike (5x+ normal)

### 3. New Accounts & Inflows
- 0: Normal levels of account openings / inflows
- 1: Account openings +50-100% YoY
- 2: Account openings +200% YoY, large inflow from first-time investors

### 4. New Issuance Flood
- 0: Normal IPO / product issuance
- 1: IPOs / SPACs / themed ETFs +50% YoY
- 2: Low-quality IPO flood, surge in "[theme]-related" funds / ETFs

### 5. Leverage
- 0: Margin debt and lending balances within normal range
- 1: Margin debt 1.5x historical average, futures positioning skewed
- 2: Margin debt at all-time high, sustained high funding rates, extreme positioning

### 6. Price Acceleration
- 0: Annualised returns near the historical median
- 1: Annualised returns above the historical 90th percentile
- 2: Annualised returns in 95-99th percentile, or positive and rising acceleration (second derivative)

### 7. Valuation Disconnect
- 0: Fundamentals rationally explain the valuation
- 1: Elevated valuation but plausibly justified by growth expectations
- 2: Explanation depends entirely on "narrative", "revolution", "paradigm shift", "this time is different"

### 8. Breadth & Correlation
- 0: Only a handful of leaders rising
- 1: Whole sectors participate, mid-caps also rising
- 2: Low-quality / low-cap names also rallying, "zombie companies" rise (last buyers entering)
"""
        return guidelines

    def format_output(self, result: dict) -> str:
        """Format the result for human reading."""
        output = f"""
{"=" * 60}
US Equity Bubble Assessment - Bubble-O-Meter
{"=" * 60}

Assessment timestamp: {result["timestamp"]}

[Total Score]
{result["total_score"]}/{result["max_score"]} ({result["percentage"]}%)

[Market Phase]
Current: {result["phase"]} (Risk: {result["risk_level"]})
Minsky phase: {result["minsky_phase"]}

[Recommended Action]
{result["recommended_action"]}

{"=" * 60}
[Per-indicator Scores]
{"=" * 60}
"""
        for detail in result["detailed_indicators"]:
            output += f"\n[{detail['status']}] {detail['indicator']}: {detail['score']}/2\n"
            output += f"   - {detail['description']}\n"

        output += f"\n{'=' * 60}\n"

        return output


def manual_assessment() -> dict[str, int]:
    """Interactive manual assessment."""
    scorer = BubbleScorer()
    print("\n" + "=" * 60)
    print("US Equity Bubble Assessment - Manual Assessment")
    print("=" * 60)
    print("\nScore each indicator from 0 to 2:")
    print(scorer.get_scoring_guidelines())

    scores = {}
    for key, indicator in scorer.indicators.items():
        while True:
            try:
                score = int(input(f"\n{indicator['name']} (0-2): "))
                if 0 <= score <= 2:
                    scores[key] = score
                    break
                else:
                    print("Enter 0, 1, or 2.")
            except ValueError:
                print("Please enter a number.")

    return scores


def main():
    parser = argparse.ArgumentParser(description="Score US equity bubble risk (Bubble-O-Meter)")
    parser.add_argument("--manual", action="store_true", help="Interactive manual assessment mode")
    parser.add_argument(
        "--scores",
        type=str,
        help='JSON-encoded scores (e.g. \'{"mass_penetration":2,"media_saturation":1,...}\')',
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args()
    scorer = BubbleScorer()

    # Obtain the scores
    if args.manual:
        scores = manual_assessment()
    elif args.scores:
        try:
            scores = json.loads(args.scores)
        except json.JSONDecodeError:
            print("Error: invalid JSON for --scores", flush=True)
            return 1
    else:
        print("Error: pass --manual or --scores")
        print("\nGuidelines:")
        print(scorer.get_scoring_guidelines())
        return 1

    # Run the assessment
    result = scorer.calculate_score(scores)

    # Output
    if args.output == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(scorer.format_output(result))

    return 0


if __name__ == "__main__":
    exit(main())
