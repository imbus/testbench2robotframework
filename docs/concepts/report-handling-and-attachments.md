# Konzept: Report-Handling und Attachment-Export

Status: umgesetzt (Teil A, B, C); Doku in `docs/configuration/overview.md` und `docs/usage/`. Betrifft `generate-tests` und `fetch-results`.

## Ausgangslage

Heute (2.0.0):

- `generate-tests` entpackt ein Report-Zip in ein `TemporaryDirectory` im CWD und
  liest daraus. Attachments werden nicht angefasst; nach dem Lauf sind sie weg.
  Generierter Code, der Attachments braucht (Repräsentanten von
  Reference-Datentypen, XML-Templates), verweist über `${ITB_ATTACHMENTS_DIR}`
  auf einen Ordner, den der Aufrufer selbst bereitstellen muss. Das ist eine
  Konvention des Plattform-Executors, keine dokumentierte Eigenschaft der Library.
- `fetch-results` entpackt ein Report-Zip dauerhaft neben das Zip (`report.zip`
  → `report/`) und lässt es liegen. Zusätzlich wird ein `TemporaryDirectory`
  angelegt, in dem das Ergebnis aufgebaut wird – auch dann, wenn es nicht
  gebraucht wird (In-place-Modus). Ohne `-d` wird der Eingabe-Report
  überschrieben (siehe `output-directory` in der Referenz).
- Pfade im generierten Code werden mit `${/}` zusammengesetzt.

Ziele:

1. Keine Rückstände durch `fetch-results`; ein gemeinsames, steuerbares
   Verhalten beim Entpacken für beide Kommandos.
2. Attachments des Reports für den generierten Code verfügbar machen – als
   Feature der Library, nicht der Plattform.
3. Pfade im generierten Code mit `/`. Python und Robot Framework verarbeiten
   Forward Slashes auf allen Plattformen; `${/}` bläht den Code auf und bringt
   nichts. Kein Backslash-Escaping.

Nicht-Ziel: den In-place-Modus abschaffen. Er bleibt, wie er ist.

---

## Teil A – Report lesen (beide Kommandos)

Eine gemeinsame Funktion `open_report(path, config) -> ReportSource` ersetzt
`extract_to_working_directory` (generate) und `get_directory` (fetch):

- Verzeichnis → wird direkt und **nur lesend** benutzt.
- Zip → wird entpackt; wohin, entscheidet `keep-extracted-report` (unten).

`ReportSource` besitzt `close()`. Die Aufrufer räumen auf, sobald sie den
Report nicht mehr brauchen:

- `generate-tests`: nach `write_test_suites` (und dem Attachment-Export, Teil B).
- `fetch-results`: in `ResultWriter.end_result`. Der `ResultWriter` hält die
  `ReportSource` als Attribut, weil er im **Listener-Modus** (`listener_uid`)
  über den gesamten Robot-Lauf lebt und nach jeder Suite `project.json` aus
  der Quelle liest (`write_listener_mode_protocols`). Ein `with`-Block um den
  Konstruktor wäre dort falsch. Zusätzlich: `close()` läuft auch, wenn
  `end_result` wegen fehlendem `tt_tree` früh aussteigt (heute bleibt das
  Temp-Verzeichnis dann stehen).

`fetch-results` baut das Ergebnis weiterhin in einem zweiten Temp-Verzeichnis
auf (Quelle und Ziel müssen getrennt sein: pro Testfall wird das Original
gelesen und die geänderte Fassung geschrieben). Am Ende genau eine
Schreiboperation: Zip oder Verzeichnis an den Zielpfad. Ohne `-d` ist der
Zielpfad der Quellpfad – In-place bleibt damit exakt erhalten. Das Temp-Ziel
wird nur noch angelegt, wenn es gebraucht wird.

### Option `keep-extracted-report` (nur Config-Datei)

| | |
|---|---|
| Kommando | `generate-tests` **und** `fetch-results`, gleiches Verhalten |
| Werte | `true` / `false` |
| Default | `false` – Zip wird in ein Temp-Verzeichnis entpackt und danach entfernt |
| `true` | Zip wird nach `<name>/` neben das Zip entpackt und bleibt liegen. Existiert das Verzeichnis, wird es überschrieben. |
| CLI | nein |

Bei einem Verzeichnis als Eingabe hat die Option keine Wirkung.

Verhaltensänderung gegenüber heute: `fetch-results` hinterlässt per Default kein
`report/` mehr. Wer es braucht, setzt `true`. Für `generate-tests` ist `true`
neu (bisher immer Temp).

---

## Teil B – Attachments exportieren (`generate-tests`)

### Option `attachments-directory`

| | |
|---|---|
| Werte | Pfad (absolut oder relativ), `{root}`-Platzhalter wie bei `output-directory`, oder leer |
| Default | leer – nichts wird kopiert, keine Variablen-Sektion |
| CLI | `--attachments-directory` |

Ist ein Pfad gesetzt, kopiert `generate-tests` den Ordner `attachments/` des
Reports vollständig dorthin – Repräsentanten (`representatives/DT-…/`),
`advancedContent/` und Anhänge von Testfallsätzen/Testfällen gleichermaßen.
Es wird nicht gefiltert: die Library kennt nicht alle Konsumenten der
Unterordner (z. B. den XmlGenerator der Plattform). Der Zielordner wird vorher
geleert.

Die Form des Pfads bestimmt, wie die Variable in den Suites definiert wird:

| `attachments-directory` | Kopiert nach | Wert der Variablen in jeder Suite |
|---|---|---|
| absolut, z. B. `/data/run1/attachments` | genau dorthin | `/data/run1/attachments` (absolut, unverändert) |
| relativ, z. B. `attachments` | `<output-directory>/attachments` | `${CURDIR}/../attachments` – relativ zur Suite, `..` je nach Tiefe der Suite im Ausgabebaum |

Der relative Fall macht den Ausgabeordner als Ganzes verschiebbar; der absolute
Fall ist für Umgebungen, in denen die Attachments an einem festen Ort liegen.
Ein `{root}`-Platzhalter wird vor der Entscheidung aufgelöst und ergibt damit
immer einen absoluten Pfad.

Bei einem `.zip` als `output-directory` landet ein relativer Attachments-Ordner
mit im Zip.

### Option `attachments-variable`

| | |
|---|---|
| Werte | Name einer Robot-Variablen ohne `${}`, oder leer |
| Default | `ITB_ATTACHMENTS_DIR` |
| CLI | nein |

Der Name, unter dem generierter Code Attachments referenziert:

```robotframework
${message}    Envelope.Load Message    ${ITB_ATTACHMENTS_DIR}/representatives/DT-6917529030000126275/Vorlage_pain.001.001.09.xml
```

Ist `attachments-directory` gesetzt, schreibt der Generator in jede Suite,
deren Keyword-Aufrufe die Variable verwenden (Attachment-Repräsentanten oder
bereits injizierte `${ITB_ATTACHMENTS_DIR}/…`-Werte des XmlGenerators), eine
Variablen-Sektion – nicht in Suiten ohne Attachments, nicht in `__init__.robot`:

```robotframework
*** Variables ***
${ITB_ATTACHMENTS_DIR}    ${CURDIR}/../attachments
```

Ein `--variable ITB_ATTACHMENTS_DIR:…` auf der Robot-Kommandozeile
überschreibt Suite-Variablen – die Plattform kann die Variable also weiter
selbst setzen, während ein lokal generierter Ordner ohne Angaben lauffähig ist.

Leerer Wert: Attachment-Parameter werden ohne Variable geschrieben, also als
`representatives/DT-…/<datei>` relativ zum CWD des Robot-Laufs, und es wird
keine Variablen-Sektion erzeugt. Das ist die Form für Nutzer, die Robot aus dem
Report-Verzeichnis heraus starten.

Die frühere Option `attachments-variable-in-suites` entfällt: ob die Sektion
geschrieben wird, folgt aus `attachments-directory` (gesetzt oder nicht), der
Name aus `attachments-variable`.

### Verhalten in `fetch-results`

Keine Änderung. `fetch-results` liest Attachments aus dem Report (für
`references.json`) und kopiert `itb-reference`-Dateien aus dem
Robot-Ausgabeverzeichnis hinein; `attachments-directory` spielt dort keine
Rolle.

---

## Teil C – Pfade im generierten Code

Alle von der Library zusammengesetzten Pfade verwenden `/`:

- Attachment-Werte (`${ITB_ATTACHMENTS_DIR}/representatives/…`), bereits im
  aktuellen Fix enthalten und dort von `${/}` auf `/` umzustellen.
- Der Wert der Variablen-Sektion (`${CURDIR}/../attachments`).
- Resource-Imports – prüfen, ob dort heute `${/}` oder `os.sep` verwendet wird,
  und angleichen.

Kein Escaping von Backslashes; absolute Windows-Pfade werden mit `/` geschrieben
(`C:/data/attachments`), was Python, Robot und die Java-Libraries akzeptieren.

---

## Zusammenfassung der Optionen

| Option | Kommando | CLI | Default | Verhalten heute |
|---|---|---|---|---|
| `keep-extracted-report` | beide | nein | `false` | fetch: `true`-Verhalten, generate: `false`-Verhalten |
| `attachments-directory` | generate-tests | ja | leer | leer |
| `attachments-variable` | generate-tests | nein | `ITB_ATTACHMENTS_DIR` | hart codiert |

Die Plattform (tb-rf-convertor) bräuchte keine der Optionen: der Executor
lädt den Report komplett und setzt die Variable per `--variable`. Sie
profitiert nur vom neuen Default für `keep-extracted-report`.

## Reihenfolge der Umsetzung

1. Teil C für den bestehenden Fix (`${/}` → `/`), Tests anpassen.
2. Teil A: `open_report`, `keep-extracted-report`, Tests für die sechs
   Ein-/Ausgabe-Kombinationen von `fetch-results` plus Listener-Modus.
3. Teil B: Kopieren, Variablen-Sektion, Tests für absolut/relativ/leer und
   für die `..`-Tiefe bei verschachtelten Suiten.
4. Doku: Referenz (`overview.md`), `generate_tests.md`, `fetch_results.md`.
