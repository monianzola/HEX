"""Write tournament results as JSON and as a static HTML leaderboard."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from hexarena.tournament.runner import WIN, TournamentResult

REPO_URL = "https://github.com/monianzola/HEX"

REASON_LABELS = {
    WIN: "conexión",
    "exception": "excepción",
    "timeout": "tiempo agotado",
    "illegal": "jugada ilegal",
    "crash": "proceso caído",
}

_CSS = """
:root {
  --bg: #f5f3ee; --card: #ffffff; --text: #1d1d1f; --muted: #6b6b70;
  --line: #e2dfd8; --red: #d62839; --blue: #1f6fd1; --gold: #c99700;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #16161a; --card: #1f1f24; --text: #ececf1; --muted: #a0a0aa; --line: #33333b; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 32px 16px 48px; }
h1 { margin: 0 0 4px; font-size: 28px; }
h1 span { color: var(--red); }
h2 { margin: 32px 0 12px; font-size: 19px; }
.meta { color: var(--muted); margin: 0 0 24px; }
.meta a { color: inherit; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--line); white-space: nowrap; }
tr:last-child td { border-bottom: none; }
th { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.rank { font-weight: 700; }
.first .rank { color: var(--gold); }
.bot small { display: block; color: var(--muted); }
.bar { display: inline-block; height: 6px; border-radius: 3px; background: var(--blue); vertical-align: middle; margin-left: 8px; }
.matrix td.self { color: var(--muted); text-align: center; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { background: var(--card); border: 1px solid var(--line); border-radius: 999px; padding: 4px 12px; font-size: 13px; }
.empty { padding: 16px; color: var(--muted); }
footer { margin-top: 40px; color: var(--muted); font-size: 13px; }
footer a { color: inherit; }
"""


def to_json(result: TournamentResult) -> str:
    """Serialise ``result`` as pretty-printed JSON."""
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


def to_html(result: TournamentResult) -> str:
    """Render a self-contained HTML page with the leaderboard."""
    config = result.config
    names = {e.bot: e.name for e in result.entrants}
    commit = result.commit
    commit_html = (
        f'<a href="{REPO_URL}/commit/{escape(commit)}">{escape(commit[:7])}</a>'
        if commit != "unknown"
        else "desconocido"
    )

    rows = []
    for rank, s in enumerate(result.standings, start=1):
        cls = ' class="first"' if rank == 1 else ""
        author = f"<small>{escape(s.author)}</small>" if s.author else ""
        rows.append(
            f"<tr{cls}><td class=\"rank\">{rank}</td>"
            f'<td class="bot"><strong>{escape(s.name)}</strong>{author}</td>'
            f'<td class="num">{s.elo:.0f}</td>'
            f'<td class="num">{s.wins}</td><td class="num">{s.losses}</td>'
            f'<td class="num">{s.win_rate:.0%}<span class="bar" style="width:{s.win_rate * 60:.0f}px"></span></td>'
            f'<td class="num">{s.forfeits}</td></tr>'
        )

    order = [s.bot for s in result.standings]
    matrix_head = "".join(f'<th class="num">{escape(names[b])}</th>' for b in order)
    matrix_rows = []
    for a in order:
        cells = []
        for b in order:
            if a == b:
                cells.append('<td class="self">—</td>')
            else:
                won, lost = result.head_to_head[a][b], result.head_to_head[b][a]
                cells.append(f'<td class="num">{won}–{lost}</td>')
        matrix_rows.append(f"<tr><th>{escape(names[a])}</th>{''.join(cells)}</tr>")

    incidents = [g for g in result.games if g.reason != WIN]
    if incidents:
        incident_rows = "".join(
            f"<tr><td class=\"num\">{g.index + 1}</td><td>{escape(names[g.loser])}</td>"
            f"<td>{escape(REASON_LABELS.get(g.reason, g.reason))}</td>"
            f"<td>{escape(g.detail[:160])}</td></tr>"
            for g in incidents
        )
        incidents_html = (
            '<div class="card"><table><thead><tr><th class="num">Partida</th><th>Bot</th>'
            f"<th>Motivo</th><th>Detalle</th></tr></thead><tbody>{incident_rows}</tbody></table></div>"
        )
    else:
        incidents_html = '<div class="card"><p class="empty">Ningún bot ha fallado. 🎉</p></div>'

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clasificación hex-arena</title>
<style>{_CSS}</style>
</head>
<body>
<main>
  <h1><span>⬢</span> Clasificación hex-arena</h1>
  <p class="meta">Actualizada el {escape(result.generated_at)} · commit {commit_html} ·
    {len(result.games)} partidas en {result.duration_seconds:.0f} s</p>

  <div class="chips">
    <span class="chip">Round-robin</span>
    <span class="chip">Tablero {config.board_size}×{config.board_size}</span>
    <span class="chip">{config.games_per_pair} partidas por pareja (mitad con cada color)</span>
    <span class="chip">{config.time_limit:g} s por movimiento</span>
    <span class="chip">Elo inicial {config.initial_elo:g}, K = {config.k_factor:g}</span>
    <span class="chip">Semilla {config.seed}</span>
  </div>

  <h2>Clasificación</h2>
  <div class="card"><table>
    <thead><tr><th>#</th><th>Bot</th><th class="num">Elo</th><th class="num">Victorias</th>
      <th class="num">Derrotas</th><th class="num">% victorias</th><th class="num">Descalif.</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table></div>

  <h2>Enfrentamientos directos</h2>
  <p class="meta">Cada celda muestra victorias–derrotas del bot de la fila contra el de la columna.</p>
  <div class="card"><table class="matrix">
    <thead><tr><th></th>{matrix_head}</tr></thead>
    <tbody>{''.join(matrix_rows)}</tbody>
  </table></div>

  <h2>Incidencias</h2>
  <p class="meta">Un bot que lanza una excepción, se pasa de tiempo, juega ilegalmente o se cae
    pierde esa partida, y el torneo continúa.</p>
  {incidents_html}

  <footer>Generado automáticamente por <a href="{REPO_URL}">hex-arena</a> ·
    <a href="results.json">resultados en JSON</a></footer>
</main>
</body>
</html>
"""


def write_results(result: TournamentResult, output_dir: str | Path) -> tuple[Path, Path]:
    """Write ``results.json`` and ``index.html`` into ``output_dir``.

    Returns:
        The paths of the JSON file and the HTML page.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "results.json"
    html_path = out / "index.html"
    json_path.write_text(to_json(result), encoding="utf-8")
    html_path.write_text(to_html(result), encoding="utf-8")
    return json_path, html_path
