# Fehlerbericht — Agency-Plugin (Novel-Decomposition-Kampagne)

> Faktische Dokumentation der Reibungspunkte, die beim Dogfooding des
> Agency-Plugins während der Kohärenz-Protokoll-Decomposition auftraten
> (Session vom 2026-05-30/31). Arbeitssprache der Befunde: Deutsch auf Wunsch;
> alle zitierten Pfade/Verben sind englisch (Codebasis-Sprache).
>
> **Ziel dieses Berichts:** keine Schuldzuweisung, sondern eine reproduzierbare
> Liste echter Hürden, damit das Plugin (`netzkontrast/agency`) sie schließen
> kann. Jeder Befund nennt Beleg, Auswirkung und einen Vorschlag.

| Umgebung | Wert |
|---|---|
| Plugin | `netzkontrast/agency` (Marketplace-Plugin, MCP-Server) |
| Plugin-Quelle | `/root/.claude/plugins/marketplaces/agency/` |
| Graph-DB | `/root/.claude/plugins/data/agency-agency/agency.db` |
| venv | `/root/.claude/plugins/marketplaces/agency/.venv` (hat `fastmcp` + `graphqlite`) |
| Wire-Kontrakt | `search · get_schema · execute` (Code-Mode) |

---

## Befundübersicht

| # | Titel | Schweregrad | Status |
|---|---|---|---|
| F1 | Kein MCP-Verb zum Anlegen eines Intent (Bootstrap nur per Bash-CLI) | **Hoch** (Blocker) | offen |
| F2 | `JULES_API_KEY` wird vom laufenden Server nicht gelesen | **Hoch** | umgangen |
| F3 | Code-Mode-Sandbox-Timeout (30 s) killt Mehrfach-Dispatch → Duplikate | **Mittel** | umgangen |
| F4 | `reflect.batch_note`: `scope` ist ein undokumentiertes geschlossenes Enum | **Niedrig** | umgangen |
| F5 | System-`python3` ohne Deps → stiller Fehlschlag beim Intent-Anlegen | **Mittel** | umgangen |
| F6 | `intent_id`-Pflicht ohne Discovery-Pfad zum Bootstrap | **Mittel** (DX) | offen |

---

## F1 — Kein MCP-Verb mintet einen Intent (Bootstrap nur per Bash-CLI)

**Schweregrad:** Hoch (harter Blocker für jeden reinen MCP-Client)

**Symptom.** Jedes Capability-Verb verlangt eine gültige `intent_id`, die auf
einen existierenden `Intent`-Knoten auflöst. Der Registry-Guard lehnt sonst ab:

```
ValueError: intent_id 'x' is not an Intent node
```
(`agency/capability.py:172-174` — der `SERVES`-Guard, der vor jeder Nebenwirkung prüft.)

**Ursache.** Ein Intent wird ausschließlich von `engine.intent.capture()` erzeugt
(`agency/intent.py:16`, `memory.record("Intent", …)`). Diese Methode ist **nicht**
als MCP-Verb verdrahtet. Im Code-Mode-Sandbox (`execute`) ist `capability_intent_capture`
schlicht nicht vorhanden:

```
Exception: Unknown tool: capability_intent_capture
```

Der einzige Bootstrap-Pfad ist das Bash-CLI-Subkommando:
```bash
python -m agency.cli intent --purpose … --deliverable … --acceptance …
```
(`agency/cli.py:59-86` — Kommentar dort bestätigt: *„`intent` is the one verb
that bootstraps state without an existing intent“*.)

**Auswirkung.** Ein Client, der nur die drei Wire-Verben (`search/get_schema/execute`)
spricht — also der dokumentierte Normalfall — kann **keinen** Intent anlegen und
damit **kein einziges** Capability-Verb aufrufen. Man muss auf einen zweiten,
undokumentierten Kanal (Bash-CLI im Plugin-venv) ausweichen.

**Vorschlag.** Entweder (a) `intent.capture`/`intent.confirm` als reguläre Verben
verdrahten (mit der einzigen Ausnahme, dass sie keine vorab existierende
`intent_id` verlangen), oder (b) ein dediziertes Substrat-Tool `intent_bootstrap`
analog zu `lifecycle_gate`/`memory_graph_provenance` in `engine.build_mcp()`
registrieren.

---

## F2 — `JULES_API_KEY` wird vom laufenden Server nicht gelesen

**Schweregrad:** Hoch

**Symptom.** Beim Aufruf eines Jules-Verbs über den laufenden MCP-Server:
```
Error calling tool 'capability_jules_quota': JULES_API_KEY is not set.
Export it in the shell that launched the engine, then retry.
```
Gleichzeitig **war** der Key in der Shell vorhanden (`len=53`).

**Ursache.** Der Server wird per `.mcp.json` mit
`"JULES_API_KEY": "${user_config.jules_api_key}"` gestartet
(`/root/.claude/plugins/marketplaces/agency/.mcp.json`). Er liest den Wert also
aus der Plugin-`user_config` zum Startzeitpunkt — nicht aus einer später
gesetzten Umgebungsvariable, und ein Neuladen ohne Server-Neustart greift nicht.

**Auswirkung.** Alle `jules.*`-Verben über die MCP-Schnittstelle waren nicht
nutzbar, obwohl der Key in der Umgebung lag. Der Hinweistext des Fehlers
(*„Export it in the shell that launched the engine“*) ist für einen
Marketplace-Plugin-Start zudem irreführend — die Shell startet den Server nicht
direkt, `bin/agency-mcp` tut es.

**Umgehung.** Dispatch über das Bash-CLI im Plugin-venv mit dem Key aus der
aktuellen Shell:
```bash
JULES_API_KEY="$JULES_API_KEY" .venv/bin/python -m agency.cli --db "$DB" execute --code '…'
```
(Funktioniert, weil MCP und Bash laut CORE isomorph sind.)

**Vorschlag.** Fehlermeldung präzisieren (auf `user_config.jules_api_key` und
Server-Neustart verweisen) und/oder den Key bei Bedarf lazy aus der Umgebung
nachladen, wenn `user_config` leer ist.

---

## F3 — Code-Mode-Sandbox-Timeout killt Mehrfach-Dispatch → Duplikate

**Schweregrad:** Mittel (führt zu inkonsistentem Zustand)

**Symptom.** Ein `execute`-Block, der 5 Jules-Sessions nacheinander dispatchte,
lief in den Sandbox-Timeout:
```
MontyRuntimeError: TimeoutError: time limit exceeded: 99.149387485s > 30s
```
(`AGENCY_SANDBOX_MAX_SECS`, Default 30 s, `agency/engine.py:35-40`.)

**Auswirkung.** Der Block wurde **mittendrin** abgebrochen. Die ersten Dispatches
(externe Effekte!) waren bereits an die Jules-API abgesetzt und hatten reale
Sessions erzeugt — der `execute`-Aufruf gab aber nur einen Fehler zurück, **ohne
die erzeugten Session-IDs**. Das führte direkt zu Folgefehler-Risiko: Re-Dispatch
erzeugte **Duplikate** (Slice 02 lief doppelt → zwei Sessions, zwei PRs #138/#139).

Kernproblem: Ein `effect`-Verb, das N externe Aktionen in einer Sandbox-Transaktion
bündelt, ist **nicht atomar** und **nicht idempotent** — ein Timeout hinterlässt
teilweise ausgeführte Nebenwirkungen ohne Rückgabe.

**Umgehung.** (a) Pro Session ein eigener `execute`-Aufruf statt Batch;
(b) `AGENCY_SANDBOX_MAX_SECS=300` für die Batch-Variante; (c) danach die
Wahrheit aus `jules.list` rekonstruieren statt aus dem (verlorenen) Rückgabewert.

**Vorschlag.** Für `effect`-Verben mit externen Nebenwirkungen entweder einen
höheren/abschaltbaren Timeout dokumentieren, oder die Session-IDs inkrementell
(streamend) zurückgeben, oder einen Idempotenz-Schlüssel (z. B. `alias`)
serverseitig deduplizieren, sodass ein Re-Dispatch mit gleichem Alias keine
zweite Session erzeugt.

---

## F4 — `reflect.batch_note`: `scope` ist ein undokumentiertes geschlossenes Enum

**Schweregrad:** Niedrig (DX/Ergonomie)

**Symptom.**
```
Reflection record violates ontology:
["scope='kp-novel-decomposition' not in
  ['observation','project','reflection','technical','user','world']"]
```

**Ursache.** `scope` ist ontologisch ein geschlossenes Enum, aber die
Verb-Beschreibung (`reflect.batch_note` / `reflect.note`) nennt die erlaubten
Werte nicht. Sie beschreibt `scope` nur als „scope-tagged“ — der Aufrufer erfährt
die Enum-Domäne erst durch den Validierungsfehler.

**Auswirkung.** Ein erster, ansonsten korrekter Provenance-Schreibversuch schlug
fehl; erst der zweite Lauf mit `scope="project"` ging durch.

**Vorschlag.** Die erlaubten `scope`-Werte in die Verb-Beschreibung /
`get_schema`-Ausgabe aufnehmen (analog zu anderen Enum-Feldern), damit der
Aufrufer sie vor dem Call kennt.

---

## F5 — System-`python3` ohne Deps → stiller Fehlschlag beim Intent-Anlegen

**Schweregrad:** Mittel (stiller Datenverlust-Anschein)

**Symptom.** Der erste Versuch, Intents via direktem Import (`Memory`/`Intent`)
mit dem System-`python3` anzulegen, brach mit
`ModuleNotFoundError: No module named 'graphqlite'` (bzw. `fastmcp`) ab. Eine
spätere Prüfung zeigte `INTENT_COUNT 0` — es war also **nichts** geschrieben
worden, obwohl die Zwischenausgaben so aussahen, als sei etwas passiert.

**Ursache.** Nur das Plugin-venv
(`/root/.claude/plugins/marketplaces/agency/.venv`) hat `graphqlite`/`fastmcp`.
Das System-`python3` kann die Graph-DB gar nicht öffnen.

**Auswirkung.** Verlorene Zeit durch einen scheinbar erfolgreichen, real
fehlgeschlagenen Bootstrap. Erst die explizite `INTENT_COUNT`-Prüfung deckte es auf.

**Vorschlag.** (Eher Nutzungs-Lehre als Plugin-Bug.) Dokumentieren, dass jeglicher
direkter Zugriff auf die Engine das Plugin-venv verwenden muss; ggf. einen
`agency doctor`-Befehl anbieten, der Interpreter + Deps + DB-Erreichbarkeit prüft.

---

## F6 — `intent_id`-Pflicht ohne Discovery-Pfad zum Bootstrap

**Schweregrad:** Mittel (DX, eng verwandt mit F1)

**Symptom.** `search` liefert die Verben und ihre Parameter (inkl. „`intent_id`
(string, required)“), aber **kein** Treffer erklärt, *wie* man eine gültige
`intent_id` überhaupt erhält. Die Discovery-Oberfläche führt im Kreis: jedes Verb
verlangt einen Intent, kein auffindbares Verb erzeugt einen.

**Auswirkung.** Ohne Quellcode-Lektüre (`cli.py`, `intent.py`, `capability.py`)
ist der Einstieg nicht erschließbar. Genau das war hier nötig.

**Vorschlag.** Im `search`-Ergebnis (oder einem `help`-Verb) einen
Bootstrap-Hinweis ausgeben: „Beginne mit `intent` (CLI) bzw.
`intent_bootstrap` (MCP), um eine `intent_id` zu erhalten.“ Siehe F1.

---

## Was gut funktioniert hat (zur Fairness)

- **Cross-Prozess-DB-Sichtbarkeit:** Per CLI-venv angelegte Intents waren sofort
  für den laufenden MCP-Server sichtbar (gleiche `agency.db`). Der Intent-Guard
  wechselte korrekt von „is not an Intent node“ zu „JULES_API_KEY not set“ —
  Beweis, dass die Provenance-Verkettung griff.
- **MCP/Bash-Isomorphie:** Der Ausweich über `agency.cli execute` lieferte
  identische Ergebnisse wie der MCP-Pfad — wie in CORE versprochen.
- **`alias`-Mechanik:** Stabile Aliase + `JulesSession`-Knoten im Graphen
  funktionierten; die fünf Slices ließen sich sauber pro Child-Intent verorten.
- **Zero-Touch-Dispatch:** `require_plan_approval=False` + `automation_mode=AUTO_CREATE_PR`
  lieferte automatisch fünf fertige PRs (#137, #138, #140, #141, #142).

---

## Zusammenfassung für das Plugin-Team

Die zwei wirklich blockierenden Punkte sind **F1** (kein MCP-Bootstrap für
Intents) und **F2** (Key-Laden). Beide zwingen einen reinen MCP-Client auf den
Bash-CLI-Nebenpfad. **F3** (nicht-atomarer Batch-Effekt mit Duplikat-Risiko) ist
der gefährlichste Korrektheitspunkt, weil er stillen Doppel-Dispatch externer
Aktionen verursacht. **F4–F6** sind Ergonomie/Discovery und billig zu beheben.

*Erstellt im Rahmen der KP-Novel-Decomposition; Belege stammen aus den
Tool-Ausgaben derselben Session. Wurzel-Intent der Kampagne: `intent:52b23adc`.*
