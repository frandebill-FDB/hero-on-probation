"""CLI for snapshot-based journeys; all numbered decisions commit atomically."""

import copy
import sqlite3

from hero_on_probation import journey_store
from hero_on_probation.journey import Journey


def run(state: Journey) -> bool:
    """Return to the main menu on True; False exits the application."""
    print(
        "\nHERO ON PROBATION | Every decision autosaves, including wagers and battles."
    )
    print("load restores the latest autosave, not a pre-battle checkpoint.")
    while True:
        print("\n" + state.status())
        title, _ = state.view()
        options = state.available_options()
        print(title)
        for number, option in options:
            print(f"  {number}. {option}")
        print(
            "Commands: status | bag | quests | journal | achievements | hall | "
            "hints | save | load | back | menu | quit"
        )
        if "express" in state.flags and state.stage not in ("battle", "ending"):
            print("travel: return to route choices (no progress reset).")
        try:
            command = input("> ").strip().lower()
            if command == "quit":
                print("Goodbye! All completed decisions are already saved.")
                return False
            if command == "menu" or (state.stage == "ending" and command == "3"):
                return True
            if command in ("", "back", "status"):
                continue
            if command == "bag":
                print(
                    "\n".join(f"{k} x{v}" for k, v in state.inventory.items())
                    or "Empty bag."
                )
                print(
                    f"Task parcel: {state.job[2]} ({state.parcel})"
                    if state.quests.get("Delivery") == "Active"
                    else "No active delivery parcel."
                )
            elif command == "quests":
                print(state.quests or "No tasks yet.")
            elif command == "journal":
                print("\n".join(state.journal) or "Your journey has just begun.")
            elif command == "achievements":
                print(
                    "\n".join(
                        f"{title}: {r['description']} (x{r['count']})"
                        for title, r in state.achievements.items()
                    )
                    or "No achievements yet."
                )
            elif command == "hall":
                journey_store.show_honours()
            elif command == "hints":
                journey_store.show_honours(show_hints=True)
            elif command == "travel":
                candidate = copy.deepcopy(state)
                candidate.travel()
                state = journey_store.commit(candidate)
            elif command == "help":
                print(
                    "Numbers act. Information commands and back do not take a turn. "
                    "Every action saves automatically. "
                    "load cannot undo a wager or reward. "
                    "Use hints for optional ending clues; "
                    "travel returns to express-route choices outside combat."
                )
            elif command == "save":
                # No stale in-memory copy may overwrite a newer committed action.
                state = journey_store.load(state.save_id)
                print("Latest progress is already saved. Reloaded that snapshot.")
            elif command == "load":
                state = journey_store.load(state.save_id)
                print("Latest autosave loaded. No rewards repeated.")
            elif command in [str(number) for number, _ in options]:
                candidate = copy.deepcopy(state)
                candidate.act(int(command))
                state = journey_store.commit(candidate)
            else:
                print("Choose a displayed number, or use help / back / menu / quit.")
        except (OSError, ValueError, sqlite3.Error) as error:
            print(
                f"Could not complete action: {error}. "
                "No new transition was accepted; use load to check saved progress."
            )
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Completed decisions remain saved.")
            return False
