"""CLI for snapshot-based journeys; all numbered decisions commit atomically."""

import copy
import sqlite3

from hero_on_probation import journey_store
from hero_on_probation.journey import Journey


def run(state: Journey) -> bool:
    """Return to the main menu on True; False exits the application."""
    print(
        "\nCONTINUING JOURNEY | Every decision autosaves, including wagers and battles."
    )
    print(
        "load restores the latest autosave, not a pre-battle checkpoint. Classic saves are unchanged."
    )
    while True:
        print("\n" + state.status())
        title, options = state.view()
        print(title)
        for number, option in enumerate(options, 1):
            print(f"  {number}. {option}")
        print(
            "Commands: status | bag | quests | journal | achievements | hall | save | load | back | menu | quit"
        )
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
            elif command == "help":
                print(
                    "Numbers act. Information commands and back do not take a turn. Every action saves automatically. load cannot undo a wager or reward."
                )
            elif command == "save":
                # No stale in-memory copy may overwrite a newer committed action.
                state = journey_store.load(state.save_id)
                print("Latest progress is already saved. Reloaded that snapshot.")
            elif command == "load":
                state = journey_store.load(state.save_id)
                print("Latest autosave loaded. No rewards repeated.")
            elif command in [str(i) for i in range(1, len(options) + 1)]:
                candidate = copy.deepcopy(state)
                candidate.act(int(command))
                state = journey_store.commit(candidate)
            else:
                print("Choose a displayed number, or use help / back / menu / quit.")
        except (OSError, ValueError, sqlite3.Error) as error:
            print(
                f"Could not complete action: {error}. No new transition was accepted; use load to check saved progress."
            )
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Completed decisions remain saved.")
            return False
