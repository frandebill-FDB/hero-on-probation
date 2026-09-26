"""Read-only ending collection; undiscovered names stay hidden by default."""

from hero_on_probation.journey import ENDINGS

HINTS = {
    "CLOCKED OUT": (
        "The guild's offer is not compulsory. Revisit the full introduction."
    ),
    "DELIVERY COMPLETE": "Sometimes doing exactly the job is enough.",
    "DISH DUTY": "An unshielded parcel can block a hit. Leave repair kits at the shop.",
    "ACCIDENTAL CATERING": "Pip can change what you deliver at the crossing.",
    "TOLL TAKEN": "The crossing guard accepts a concession, even from a strong hero.",
    "BOSS DEFEAT": "A boss fight can end with your concession, at any level.",
    "TACTICAL RETREAT": "Start a boss fight, then reconsider your career.",
    "THE FINAL LOAF": "Bring a baker to a boss fight. Ask for help.",
    "HONEST VICTORY": "Grow stronger, then win a boss fight without bread or bribery.",
    "PAID PERFORMANCE": "From journey 2, the boss also accepts financial arguments.",
}


def show_collection(titles, show_hints=False):
    """Count distinct endings, not duplicate records or bonus achievements."""
    earned = set(titles)
    count = sum(title in earned for title, _, _ in ENDINGS.values())
    print(f"Ending collection: {count}/{len(ENDINGS)} (across local characters)")
    for number, (ending, (title, joke, _)) in enumerate(ENDINGS.items(), 1):
        if title in earned:
            print(f"  {number:02d}. {ending} | {title}\n      {joke}")
        else:
            print(f"  {number:02d}. ???")
            if show_hints:
                print(f"      Hint: {HINTS[ending]}")
    if not show_hints:
        print("Optional: type hints for clues to undiscovered endings.")
