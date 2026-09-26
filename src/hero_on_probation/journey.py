"""Persistent, short repeatable adventures. Transitions perform no disk I/O."""

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

JOBS = (
    ("The Pan Returns", "Demon King", "frying pan", "Probation Square", "Bridge Slime"),
    (
        "Curtain Call",
        "Count Snooze",
        "blackout curtains",
        "Midnight Market",
        "Toll Bat",
    ),
    (
        "Notice Period",
        "The Lich Manager",
        "resignation form",
        "Overtime Plaza",
        "Union Skeleton",
    ),
)
GEAR = {"Wooden Sword", "Iron Sword", "Borrowed Coat", "Pot Lid", "Repair Kit"}
STAGES = {
    "guild",
    "parcel",
    "companion",
    "town",
    "shop",
    "rats",
    "ghost",
    "bridge",
    "certificate",
    "castle",
    "confirm",
    "battle",
    "ending",
}
ENDINGS = {
    "CLOCKED OUT": ("ANY% HERO", "Twelve seconds employed. A personal record.", 0),
    "DELIVERY COMPLETE": ("DELIVERY HERO", "You defeated the shipping estimate.", 80),
    "DISH DUTY": ("LORD OF THE RINSE", "You came for gold. You stayed for grease.", 40),
    "ACCIDENTAL CATERING": ("BREADWINNER", "Your parcel is now an approved snack.", 80),
    "TOLL TAKEN": (
        "SPOON-FED DEFEAT",
        "Defeated by an employee with a smaller salary.",
        10,
    ),
    "BOSS DEFEAT": ("ONE-HIT INTERN", "Your confidence was not valid armour.", 10),
    "TACTICAL RETREAT": ("CAREER PRESERVATION", "A short fight. A longer life.", 10),
    "THE FINAL LOAF": (
        "BREAD OF THE REALM",
        "The kingdom now has a crust problem.",
        80,
    ),
    "HONEST VICTORY": (
        "EARNED THE HARD WAY",
        "No bread. No bribe. Please frame this receipt.",
        80,
    ),
    "PAID PERFORMANCE": (
        "PAY-TO-WIN HERO",
        "The acting was terrible. The invoice was flawless.",
        0,
    ),
}


@dataclass
class Journey:
    """One character's complete resumable state, including an active battle."""

    save_id: str
    name: str
    revision: int = 0
    run: int = 1
    level: int = 1
    xp: int = 0
    gold: int = 3
    hp: int = 12
    inventory: dict[str, int] = field(
        default_factory=lambda: {"Wooden Sword": 1, "Borrowed Coat": 1}
    )
    equipment: dict[str, str] = field(
        default_factory=lambda: {"Weapon": "Wooden Sword", "Armour": "Borrowed Coat"}
    )
    companion: str = ""
    parcel: str = "intact"
    stage: str = "guild"
    ending: str = ""
    quests: dict[str, str] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    rewards: list[str] = field(default_factory=list)
    achievements: dict[str, dict] = field(default_factory=dict)
    journal: list[str] = field(default_factory=list)
    battle: dict | None = None

    @property
    def max_hp(self):
        return 12 + 8 * (self.level - 1)

    @property
    def attack(self):
        return {"Wooden Sword": 3, "Iron Sword": 5}.get(
            self.equipment.get("Weapon"), 1
        ) + 4 * (self.level - 1)

    @property
    def defence(self):
        return 2 * (self.level - 1) + (self.equipment.get("Shield") == "Pot Lid")

    @property
    def job(self):
        return JOBS[(self.run - 1) % len(JOBS)]

    @property
    def bribe(self):
        return 12 + 2 * ((self.run - 1) % len(JOBS))

    def reward(self, key: str, amount: int):
        """Award each run event once; XP is progress towards the next level."""
        if not isinstance(key, str) or type(amount) is not int or amount < 0:
            raise ValueError(
                "Rewards require a string key and non-negative integer XP."
            )
        if key in self.rewards:
            return
        self.rewards.append(key)
        self.xp += amount
        old_level = self.level
        while self.xp >= 100 * self.level:
            self.xp -= 100 * self.level
            self.level += 1
        if amount:
            print(f"+{amount} XP")
        if self.level > old_level:
            # Do not resurrect a defeated hero; survivors gain the extra HP capacity.
            if self.hp:
                self.hp += 8 * (self.level - old_level)
            print(
                f"LEVEL UP: {old_level} -> {self.level} | HP {self.max_hp} | Attack {self.attack} | Defence {self.defence}"
            )

    def unlock(self, title: str, description: str, bonus: int = 100):
        record = self.achievements.get(title)
        if record and record["last_run"] == self.run:
            return
        if record:
            record["count"] += 1
            record["last_run"] = self.run
            print(f"Achievement repeated: {title} (no first-unlock bonus).")
        else:
            self.achievements[title] = {
                "description": description,
                "first_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "first_run": self.run,
                "level": self.level,
                "last_run": self.run,
                "count": 1,
            }
            print(f"ACHIEVEMENT UNLOCKED: {title}\n{description}")
            self.reward("achievement:" + title, bonus)

    def finish(self, ending: str):
        if self.ending:
            return
        self.ending, self.stage, self.battle = ending, "ending", None
        title, joke, xp = ENDINGS[ending]
        print(f"\nENDING: {ending}\n{joke}")
        self.reward("ending", xp)
        self.unlock(
            title,
            joke,
            1000
            if ending == "THE FINAL LOAF"
            else 20
            if ending == "CLOCKED OUT"
            else 100,
        )
        self.quests["Delivery"] = (
            "Done"
            if ending in ("DELIVERY COMPLETE", "DISH DUTY", "ACCIDENTAL CATERING")
            else "Not delivered"
        )
        self.journal.append(f"Journey {self.run}: {ending}.")
        print(
            f"Settlement | Level {self.level} | XP {self.xp}/{100 * self.level} | Gold {self.gold} | HP {self.hp}/{self.max_hp}"
        )

    def next_run(self):
        if self.stage != "ending":
            raise ValueError("Finish the current journey first.")
        # Refusal is a replayable Easter egg, not a way to unlock later journeys.
        if self.ending != "CLOCKED OUT":
            self.run += 1
        self.inventory = {k: v for k, v in self.inventory.items() if k in GEAR}
        self.companion, self.parcel, self.ending = "", "intact", ""
        self.stage, self.battle = "guild", None
        self.quests, self.flags, self.rewards = {}, [], []
        self.hp = self.max_hp
        print(f"Journey {self.run}: {self.job[0]}. Same hero. Another invoice.")

    def begin_battle(self, kind: str, return_to: str = "bridge"):
        variant = (self.run - 1) % 3
        if kind == "boss":
            name, hp, attack, armour = self.job[1], 120 + variant * 10, 18 + variant, 8
        elif kind == "bridge":
            name, hp, attack, armour = self.job[4], 12 + variant * 3, 2 + variant, 0
        else:
            name = "Equipment Shopkeeper" if kind == "shop" else "Certificate Clerk"
            hp, attack, armour = 24 + variant * 4, 7 + variant, 1
        self.battle = {
            "kind": kind,
            "name": name,
            "hp": hp,
            "max_hp": hp,
            "attack": attack,
            "armour": armour,
            "turn": 1,
            "companion_used": False,
            "return_to": return_to,
        }
        self.stage = "battle"

    def wager(self, shop: str):
        if self.run < 2:
            print("Friendly wagers unlock on journey 2.")
            return
        key = "wager:" + shop
        if key in self.flags:
            print("One wager per merchant per journey. The accountant insists.")
            return
        if self.gold < 5:
            print("You need 5 gold. Credit is not a combat skill.")
            return
        self.gold -= 5
        self.flags.append(key)
        print("5 gold staked. Win: receive 10. Lose or retreat: lose the stake.")
        print("No bread magic. Last time, my accountant became a croissant.")
        self.begin_battle(shop, shop)

    def settle_battle(self, result: str):
        battle = self.battle
        kind, destination = battle["kind"], battle["return_to"]
        if kind in ("shop", "certificate"):
            if result == "victory":
                self.gold += 10
                self.reward("battle:" + kind, 30)
                self.unlock(
                    "HOSTILE NEGOTIATION",
                    "You negotiated with your sword. The receipt survived.",
                )
                print("You receive 10 gold (net profit: 5).")
            else:
                print("The merchant keeps your 5-gold stake. Shopping remains open.")
            self.hp = self.max_hp
            self.battle, self.stage = None, destination
            return
        if result in ("bread", "victory"):
            self.reward("battle:" + kind, 30 if kind == "bridge" else 150)
        if kind == "bridge":
            if result == "defeat":
                self.finish("TOLL TAKEN")
            else:
                if result == "bread":
                    self.unlock(
                        "BREAD OVER BRAWN",
                        "You solved a combat encounter with a bakery.",
                    )
                self.stage = "bridge" if result == "retreat" else "certificate"
                self.battle = None
            return
        endings = {
            "bread": "THE FINAL LOAF",
            "victory": "HONEST VICTORY",
            "retreat": "TACTICAL RETREAT",
            "defeat": "BOSS DEFEAT",
        }
        if result == "bread":
            print("The boss becomes a giant loaf. Your parcel joins the bakery.")
            print('Pip: "Dinner solved." You: "Who signs the payment receipt?"')
        elif result == "victory":
            self.gold += 8
            print(
                'Boss: "A real defeat? I did not budget for character development." Reward: 8 gold.'
            )
        self.finish(endings[result])

    def battle_turn(self, action: int):
        battle = self.battle
        wager = battle["kind"] in ("shop", "certificate")
        if action == 4:
            self.settle_battle("retreat")
            return
        guard, skip = 0, False
        if action == 3:
            if battle["companion_used"] or (wager and self.companion == "Pip"):
                print("That companion action is unavailable. No turn spent.")
                return
            battle["companion_used"] = True
            if self.companion == "Pip":
                self.parcel = "bread"
                self.settle_battle("bread")
                return
            damage, skip = max(0, self.attack + 2 - battle["armour"]), True
            print(f"Bea counters for {damage} and blocks this enemy turn.")
            battle["hp"] = max(0, battle["hp"] - damage)
        elif action == 2:
            guard = 4
            if (
                not wager
                and self.equipment.get("Shield") != "Pot Lid"
                and self.parcel == "intact"
            ):
                self.parcel = "damaged"
                print("Your parcel blocks the hit. Its resale value does not.")
        else:
            damage = max(0, self.attack - battle["armour"])
            battle["hp"] = max(0, battle["hp"] - damage)
            print(f"You deal {damage} damage.")
        if not battle["hp"]:
            self.settle_battle("victory")
            return
        if not skip:
            incoming = battle["attack"] + (
                3 if battle["turn"] % 2 == 0 and battle["kind"] == "bridge" else 0
            )
            damage = max(0, incoming - self.defence - guard)
            self.hp = max(0, self.hp - damage)
            print(f"{battle['name']} deals {damage}. HP: {self.hp}/{self.max_hp}.")
        if self.hp == 0:
            self.settle_battle("defeat")
        else:
            battle["turn"] += 1

    def view(self) -> tuple[str, list[str]]:
        """Return only presentation; rendering never executes a game event."""
        title, boss, parcel, town, enemy = self.job
        wager = (
            [
                "Challenge the merchant: stake 5 gold; win receives 10, lose/retreat forfeits 5. No bread magic."
            ]
            if self.run >= 2
            else []
        )
        menus = {
            "guild": (
                f"{title} | Guild desk",
                ["Read the contract.", "Check your pockets.", "Ring the service bell."],
            ),
            "parcel": (
                f"Deliver {boss}'s {parcel}. Five gold, if intact.",
                [
                    "What is in the parcel?",
                    "Who is it for?",
                    "What if it gets damaged?",
                    "Accept the job.",
                    "No thanks. I'm taking the day off.",
                ],
            ),
            "companion": (
                "Choose a volunteer. References remain unverified.",
                [
                    "Pip: turns things into bread. Reversal pending.",
                    "Bea: one counterattack and full block per battle.",
                ],
            ),
            "town": (
                town,
                [
                    "Equipment shop.",
                    "Rats' moving office.",
                    "Haunted warehouse.",
                    "Leave for the crossing.",
                ],
            ),
            "shop": (
                "Equipment Shopkeeper: No refunds for destiny.",
                [
                    "Iron Sword: 5 gold (+2 weapon damage).",
                    "Pot Lid: 3 gold (+1 defence; protect parcel).",
                    "Repair Kit: 2 gold (repairs damage, not bread).",
                    "Return to town.",
                ]
                + wager,
            ),
            "rats": (
                "The rats removed themselves. The guild refuses to pay.",
                [
                    "Read the contract to the guild. Slowly.",
                    "Help carry boxes.",
                    "Return to town.",
                ],
            ),
            "ghost": (
                "The ghost's resignation has been pending for thirty years.",
                [
                    "Witness the resignation.",
                    "Ask your companion to help.",
                    "Return to town.",
                ],
            ),
            "bridge": (
                f"{enemy}: Two gold. Complaints remain free.",
                [
                    "Pay 2 gold.",
                    "Help move the toll sign into the shade.",
                    "Challenge the guard.",
                    "Ask your companion for a safe route.",
                ],
            ),
            "certificate": (
                "Certificate Clerk: Fame needs a shiny border.",
                ["Buy a certificate: 3 gold.", "Go to the boss's door."] + wager,
            ),
            "castle": (
                f"{boss}: Finally. My {parcel}.",
                [
                    "Deliver the parcel and stay for dinner.",
                    "Ask for a proper boss fight.",
                ]
                + (
                    [
                        f"Offer {self.bribe} gold to stage a defeat (no delivery pay or boss XP)."
                    ]
                    if self.run >= 2
                    else []
                ),
            ),
            "confirm": (
                f"{boss}: {120 + (self.run - 1) % 3 * 10} HP. I also have plans for dinner.",
                [
                    "Dinner sounds better. Deliver the parcel.",
                    "I insist. Draw your weapon.",
                ],
            ),
            "ending": (
                f"ENDING: {self.ending} | Journey {self.run} settled and saved.",
                [
                    "Continue the journey (keep levels, gold and equipment).",
                    "Review this character.",
                    "Save and return to the main menu.",
                ],
            ),
        }
        if self.stage == "battle":
            b = self.battle
            incoming = b["attack"] + (
                3 if b["kind"] == "bridge" and b["turn"] % 2 == 0 else 0
            )
            unavailable = b["companion_used"] or (
                self.companion == "Pip" and b["kind"] in ("shop", "certificate")
            )
            return (
                f"ROUND {b['turn']} | {b['name']}: {b['hp']}/{b['max_hp']} HP | Defence {b['armour']} | Next attack {incoming}",
                [
                    f"Attack ({self.attack} before enemy defence).",
                    "Defend (+4 protection this turn).",
                    f"Ask {self.companion} for help."
                    + (" [Unavailable]" if unavailable else ""),
                    "Retreat (wager stake is forfeited)."
                    if b["kind"] in ("shop", "certificate")
                    else "Retreat.",
                ],
            )
        return menus[self.stage]

    def deliver(self):
        if self.parcel == "damaged" and self.inventory.get("Repair Kit", 0):
            self.inventory["Repair Kit"] -= 1
            if not self.inventory["Repair Kit"]:
                del self.inventory["Repair Kit"]
            self.parcel = "intact"
            print("Repair kit applied. The warranty department looks nervous.")
        if self.parcel != "damaged":
            self.gold += 5
            print("Delivery pay: 5 gold. Dinner: included.")
        self.finish(
            {
                "intact": "DELIVERY COMPLETE",
                "damaged": "DISH DUTY",
                "bread": "ACCIDENTAL CATERING",
            }[self.parcel]
        )

    def act(self, action: int):
        """Apply one numbered decision, including all associated rewards."""
        if type(action) is not int or not 1 <= action <= len(self.view()[1]):
            raise ValueError("Choose a displayed number.")
        stage = self.stage
        if stage == "battle":
            self.battle_turn(action)
        elif stage == "guild":
            if action == 3:
                self.stage = "parcel"
            else:
                print("Temporary hero. Permanent paperwork. Current gold:", self.gold)
        elif stage == "parcel":
            if action == 4:
                self.quests["Delivery"] = "Active"
                self.stage = "companion"
            elif action == 5:
                self.finish("CLOCKED OUT")
            else:
                print(
                    (
                        f"One {self.job[2]}. Do not test it on the receptionist.",
                        f"For {self.job[1]}. Fighting is not in the delivery contract.",
                        "Intact: five gold. Damaged: washing-up. Bread: catering.",
                    )[action - 1]
                )
        elif stage == "companion":
            self.companion = "Pip" if action == 1 else "Bea"
            self.stage = "town"
        elif stage == "town":
            self.stage = ("shop", "rats", "ghost", "bridge")[action - 1]
        elif stage == "shop":
            if action == 4:
                self.stage = "town"
            elif action == 5:
                self.wager("shop")
            else:
                item, price = (("Iron Sword", 5), ("Pot Lid", 3), ("Repair Kit", 2))[
                    action - 1
                ]
                if item != "Repair Kit" and item in self.inventory:
                    print("Already owned. Destiny does not need two.")
                elif self.gold < price:
                    print("Not enough gold.")
                else:
                    self.gold -= price
                    self.inventory[item] = self.inventory.get(item, 0) + 1
                    if item != "Repair Kit":
                        self.equipment[
                            "Weapon" if item == "Iron Sword" else "Shield"
                        ] = item
                    print(f"Bought {item}.")
        elif stage in ("rats", "ghost"):
            if action != 3:
                if stage in self.flags:
                    print("Already completed this journey. No duplicate paycheck.")
                else:
                    self.flags.append(stage)
                    self.quests[stage] = "Done"
                    self.gold += (4 if action == 1 else 2) if stage == "rats" else 3
                    if stage == "ghost":
                        print("The ghost clocks out. HR calls it an extended lunch.")
                        self.inventory["Ghost Reference"] = 1
                    else:
                        self.inventory["Rat Recommendation"] = 1
                        print("The rats give you a union reference. Toll waived.")
            self.stage = "town"
        elif stage == "bridge":
            if action == 1:
                price = 0 if "Rat Recommendation" in self.inventory else 2
                if self.gold < price:
                    print("Not enough gold. Helping is free.")
                    return
                self.gold -= price
                self.stage = "certificate"
            elif action == 2:
                print(
                    "You move the sign into the shade. Free crossing. Moisture matters."
                )
                self.stage = "certificate"
            elif action == 3:
                self.begin_battle("bridge")
            else:
                if self.companion == "Pip":
                    self.parcel = "bread"
                    print(
                        "Pip pays with the parcel's bread handle. No combat victory claimed."
                    )
                else:
                    print("Bea points out the ankle-deep water. You walk around.")
                self.stage = "certificate"
        elif stage == "certificate":
            if action == 3:
                self.wager("certificate")
            elif action == 1:
                if "certificate" in self.flags:
                    print("Already certified. Still temporary.")
                elif self.gold < 3:
                    print("Not enough gold.")
                else:
                    self.gold -= 3
                    self.flags.append("certificate")
                    self.inventory["Hero Certificate"] = 1
                    print("The certificate reads: PARTICIPATED.")
            else:
                if (
                    "Ghost Reference" in self.inventory
                    and "castle_bonus" not in self.flags
                ):
                    self.gold += 2
                    self.flags.append("castle_bonus")
                    print("Ghost reference: +2 gold.")
                self.stage = "castle"
        elif stage == "castle":
            if action == 1:
                self.deliver()
            elif action == 2:
                self.stage = "confirm"
            elif self.gold < self.bribe:
                print("Not enough gold. The boss does not accept exposure as payment.")
            else:
                self.gold -= self.bribe
                print(
                    'Boss: "Aaargh. Please leave a five-star review." No delivery pay. No combat XP.'
                )
                self.finish("PAID PERFORMANCE")
        elif stage == "confirm":
            if action == 1:
                self.deliver()
            else:
                self.begin_battle("boss", "castle")
        elif stage == "ending":
            if action == 1:
                self.next_run()
            elif action == 2:
                print(self.status())

    def status(self) -> str:
        return f"Hero: {self.name} | Journey {self.run} | Level {self.level} | XP {self.xp}/{100 * self.level}\nHP {self.hp}/{self.max_hp} | Attack {self.attack} | Defence {self.defence} | Gold {self.gold}\nCompanion: {self.companion or 'Solo'} | Parcel: {self.parcel} | Equipment: {self.equipment}"

    def data(self):
        return asdict(self)

    @classmethod
    def from_data(cls, data):
        """Reject malformed state rather than silently resetting progress."""
        if not isinstance(data, dict) or set(data) != set(cls.__dataclass_fields__):
            raise ValueError("Invalid journey state fields.")
        state = cls(**data)
        if not isinstance(state.save_id, str) or not re.fullmatch(
            r"[0-9a-f]{32}", state.save_id
        ):
            raise ValueError("Invalid journey save ID.")
        if (
            not isinstance(state.name, str)
            or not state.name.isprintable()
            or not 1 <= len(state.name.strip()) <= 24
        ):
            raise ValueError("Invalid character name.")
        for key in ("revision", "run", "level", "xp", "gold", "hp"):
            if type(data[key]) is not int or data[key] < (
                1 if key in ("run", "level") else 0
            ):
                raise ValueError("Invalid character statistics.")
        if (
            not isinstance(state.stage, str)
            or state.stage not in STAGES
            or state.parcel not in ("intact", "damaged", "bread")
            or state.hp > state.max_hp
            or state.xp >= 100 * state.level
        ):
            raise ValueError("Invalid journey progress.")
        if state.companion not in ("", "Pip", "Bea") or not isinstance(
            state.ending, str
        ):
            raise ValueError("Invalid character identity.")
        for key in ("flags", "rewards", "journal"):
            if not isinstance(data[key], list) or not all(
                isinstance(x, str) for x in data[key]
            ):
                raise ValueError("Invalid progress list.")
        for key in ("inventory", "equipment", "quests", "achievements"):
            if not isinstance(data[key], dict):
                raise ValueError("Invalid character records.")
        if not all(
            isinstance(k, str) and type(v) is int and v > 0
            for k, v in state.inventory.items()
        ):
            raise ValueError("Invalid inventory.")
        if not all(
            isinstance(k, str) and isinstance(v, str)
            for d in (state.equipment, state.quests)
            for k, v in d.items()
        ):
            raise ValueError("Invalid equipment or quests.")
        if (state.stage == "ending") != bool(state.ending) or (
            state.ending and state.ending not in ENDINGS
        ):
            raise ValueError("Invalid ending state.")
        if (state.stage == "battle") != (state.battle is not None):
            raise ValueError("Invalid battle state.")
        if state.hp == 0 and state.stage != "ending":
            raise ValueError("A defeated character must be at settlement.")
        if state.battle is not None:
            b = state.battle
            if not isinstance(b, dict) or set(b) != {
                "kind",
                "name",
                "hp",
                "max_hp",
                "attack",
                "armour",
                "turn",
                "companion_used",
                "return_to",
            }:
                raise ValueError("Invalid battle fields.")
            if (
                b["kind"] not in ("bridge", "boss", "shop", "certificate")
                or not isinstance(b["return_to"], str)
                or b["return_to"] not in STAGES
                or not isinstance(b["name"], str)
            ):
                raise ValueError("Invalid encounter.")
            if (
                any(
                    type(b[k]) is not int
                    or b[k] < (1 if k in ("hp", "max_hp", "turn") else 0)
                    for k in ("hp", "max_hp", "attack", "armour", "turn")
                )
                or b["hp"] > b["max_hp"]
                or type(b["companion_used"]) is not bool
            ):
                raise ValueError("Invalid enemy statistics.")
        for title, record in state.achievements.items():
            if (
                not isinstance(title, str)
                or not isinstance(record, dict)
                or set(record)
                != {
                    "description",
                    "first_at",
                    "first_run",
                    "level",
                    "last_run",
                    "count",
                }
            ):
                raise ValueError("Invalid achievement record.")
            if not isinstance(record["description"], str) or any(
                type(record[k]) is not int or record[k] < 1
                for k in ("first_run", "level", "last_run", "count")
            ):
                raise ValueError("Invalid achievement values.")
            if record["first_at"] is not None:
                try:
                    if datetime.fromisoformat(record["first_at"]).tzinfo is None:
                        raise ValueError("Achievement timestamp needs timezone.")
                except (TypeError, ValueError) as error:
                    raise ValueError("Invalid achievement timestamp.") from error
        return state
