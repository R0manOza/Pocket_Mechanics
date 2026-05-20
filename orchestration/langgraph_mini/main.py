"""
Run the Lab 7 LangGraph mini-build locally (does not require Render/Vercel).

  cd orchestration/langgraph_mini
  pip install -r requirements.txt
  python main.py
"""

from __future__ import annotations

import argparse

from graph import run_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Pocket Mechanics LangGraph Lab 7 proof")
    parser.add_argument(
        "--request",
        default="What is a serpentine belt?",
        help="User question for the demo graph",
    )
    parser.add_argument("--vehicle", default="2014 Ford Focus", help="Optional vehicle context")
    parser.add_argument(
        "--high-stakes",
        action="store_true",
        help="Use a repair-procedure question that routes to human_review",
    )
    parser.add_argument(
        "--approved",
        action="store_true",
        help="Pretend the user already approved high-stakes guidance",
    )
    args = parser.parse_args()

    request = (
        "How do I replace the serpentine belt step by step?"
        if args.high_stakes
        else args.request
    )

    final = run_demo(request, vehicle_context=args.vehicle, approved=args.approved)
    print("\n--- final state ---")
    for key in (
        "current_step",
        "approval_required",
        "approved",
        "research_notes",
        "draft_answer",
    ):
        print(f"{key}: {final.get(key)!r}")


if __name__ == "__main__":
    main()
