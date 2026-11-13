# Dark Magic Rules Analysis

Source reviewed: `TS_Save_37.json` / **Dark Magic v1.34s**. The observations below compare the Rules notebook with the latest Tabletop Simulator setup and challenge scripts.

## High-priority rule problems

1. **Action count is wrong.** The rules say a player may take â€œany of these five actions,â€ but list six playable actions: Tribute, Free Summon, Tap for Power, Engage, Free Draw, and Dig Deeper. End Turn is listed separately as a seventh numbered item. State whether each listed action is once per turn, and whether End Turn is an action or simply ends the turn.

2. **Passing the Edge conflicts.** The base turn rule says the next player is â€œto their right, ie. in counter-clockwise order.â€ The Multiplayer section says the Edge is passed to the player â€œto their left.â€ These cannot both be the default direction. Pick one direction and use it everywhere.

3. **First-turn Engage/Draw rules conflict.** Free Draw says the first player cannot Draw and Attack in the same turn, while Multiplayer says that first player can Draw and Engage in the same turn when engaging the next player. Also, the game now uses *Engage*, not *Attack*. Make the multiplayer sentence an explicit exception to the first-turn rule and use one term.

4. **Starting Wounds conflict with automation.** The notebook says seven Wounds for the base game, six for three players, and five for four players. The current start-game script always sets `INITIAL_WOUNDS = 7` for every available player; it does not reduce Wounds for additional players. The older Workshop save instead uses nine. Choose the intended two-player total and update both the rules and script.

5. **Challenge procedure is not implemented by the scripted bag.** The rules require drawing counters until two matching colors appear. The bag button script draws one object, then resets the bag; it cannot determine or resolve a two-match challenge. The script and notebook currently describe different systems.

6. **A challenge can become impossible.** The rules do not say what happens if the bag is empty, contains only one counter, or runs out before a duplicate color is drawn. They also do not say where drawn counters go or when they return to the bag. Add a failure/cleanup rule.

7. **Tap for Power is ambiguous.** â€œPut counters â€¦ equal to your Daemonâ€™s total Powerâ€ can mean one selected Daemon, all Daemons, or the playerâ€™s total Power. The rules must say whether each Daemon may be tapped once per turn, how a tapped card is restored at the start of its controllerâ€™s next turn, and whether summoning sickness exists beyond the stated exception.

## Missing mechanical definitions

- Define **Fate deck**, **Void**, **Wound**, **take a Wound**, **destroy**, **sacrifice**, **banish**, **summon**, **counter**, **tap**, **Edge**, and **Power**. Cards use several of these terms, but the notebook does not establish their destination/timing rules.
- State what happens to a Daemon when it is destroyed, and where a countered or otherwise invalid spell goes.
- Give a clear priority rule for responding to spells and activated effects: who receives priority next, how all players pass, and when the top item resolves. â€œBefore any stepâ€ conflicts with effects that may occur during a step.
- Define whether players may inspect their Wound piles and Fate/Void piles, and whether Wounds are discarded, revealed, or otherwise handled when taken.
- Greater Summon needs a clean definition. The current wording repeats â€œthis turn,â€ has an unmatched parenthesis, and does not state whether an Invocation that summons a Greater Daemon needs a prior Tribute.
- Judgements need a resolution rule: who decides whether the task was completed, what happens if it is impossible, and how this affects the challenge result.

## Tabletop Simulator implementation mismatches

- The notebook says the implementation supports White and Black two-player games by default. The deck script instead deals to every `Player.getAvailableColors()` result, so it does not enforce two players or the White/Black restriction.
- Card triggers and spell responses are intentionally manual. That is acceptable for a prototype, but the notebook should say which setup actions are automated (shuffle/deal Wounds) and which are not.
- The latest script creates seven Wounds per player. It does not implement the Multiplayer reduction rule or a reset/pass/last-Wound warning described in the TODO list.

## Text and consistency fixes

- Rename the second **Objective** heading to **Elimination and victory**.
- Change â€œif this on the first turnâ€ to â€œif this is the first turn.â€
- Use **Daemon** consistently; the spell example contains â€œDeamon.â€
- Correct **refounded** to **refunded**, **Similarily** to **Similarly**, **refereced** to **referenced**, **Rememeber** to **Remember**, and **ocurr** to **occur**.
- Change â€œits a drawâ€ to â€œitâ€™s a draw.â€
- Replace informal wording such as â€œdonâ€™t wannaâ€ with â€œchoose not to.â€
- Standardize capitalization: **Power**, **Wound**, **Void**, **Fate deck**, **Edge**, **Tribute**, **Summon**, **Engage**, and **Draw** when they name game terms.

## Recommended rules order

1. Components and glossary.
2. Setup, with player-count Wound totals.
3. Turn structure and action limits.
4. Summoning, tapping, and Power.
5. Spell timing and resolution.
6. Challenge procedure and counter cleanup.
7. Taking Wounds, elimination, and victory.
8. Multiplayer-only rules and Judgements.
9. Tabletop Simulator automation limitations.
