const btn = document.getElementById("reload-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const metaBar = document.getElementById("meta-bar");
const changesList = document.getElementById("changes-list");
const cardTemplate = document.getElementById("card-template");
const changeTemplate = document.getElementById("change-template");

const fmtUSD = (v) =>
  v == null ? "—" : v.toLocaleString("es-ES", { style: "currency", currency: "USD" });

const fmtEUR = (v) =>
  v == null ? "" : `≈ ${v.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}`;

const fmtPct = (v, withSign = true) => {
  if (v == null) return "—";
  const sign = withSign && v > 0 ? "+" : "";
  return `${sign}${v.toFixed(1)}%`;
};

const CHANGE_LABELS = {
  entra_top10: "Entra en el Top 10",
  sale_top10: "Sale del Top 10",
  objetivo_subido: "Objetivo del modelo ↑",
  objetivo_bajado: "Objetivo del modelo ↓",
  upgrade_analista: "Analista sube rating",
  downgrade_analista: "Analista baja rating",
  objetivo_analista_subido: "Analista sube objetivo",
  objetivo_analista_bajado: "Analista baja objetivo",
  resultados_positivos: "Resultados: sorpresa positiva",
  resultados_negativos: "Resultados: sorpresa negativa",
};

const CHANGE_POLARITY = {
  entra_top10: "positive",
  objetivo_subido: "positive",
  upgrade_analista: "positive",
  objetivo_analista_subido: "positive",
  resultados_positivos: "positive",
  sale_top10: "negative",
  objetivo_bajado: "negative",
  downgrade_analista: "negative",
  objetivo_analista_bajado: "negative",
  resultados_negativos: "negative",
};

async function loadData() {
  btn.disabled = true;
  statusEl.classList.remove("hidden");
  statusEl.innerHTML = "<p>Cargando el ultimo analisis disponible…</p>";
  resultsEl.classList.add("hidden");
  metaBar.classList.add("hidden");

  try {
    const bust = Date.now();
    const [dataRes, changesRes] = await Promise.all([
      fetch(`data.json?t=${bust}`),
      fetch(`changes.json?t=${bust}`),
    ]);

    if (!dataRes.ok) {
      throw new Error("No se encontro data.json todavia. El primer analisis puede tardar unos minutos en generarse.");
    }
    const payload = await dataRes.json();
    const changes = changesRes.ok ? await changesRes.json() : [];

    renderMeta(payload);
    renderResults(payload.results);
    renderChanges(changes);
    statusEl.classList.add("hidden");
  } catch (err) {
    statusEl.innerHTML = `<div class="error-box">No se pudieron cargar los datos: ${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

function renderMeta(payload) {
  const date = new Date(payload.generated_at);
  metaBar.innerHTML = `
    <span>Ultima actualizacion: <b>${date.toLocaleString("es-ES")}</b></span>
    <span>Umbral minimo: <b>+${payload.min_upside_pct_3m}% en 3 meses</b> (~${payload.min_monthly_return_pct}%/mes)</span>
    <span>Candidatas analizadas: <b>${payload.candidates_analyzed}</b></span>
    <span>Por debajo del umbral: <b>${payload.candidates_below_threshold}</b></span>
    <span>Tipo de cambio: <b>1 € = ${payload.eur_usd_rate ? payload.eur_usd_rate.toFixed(4) : "—"} $</b></span>
    <span>Retorno S&amp;P 500 (3m): <b>${fmtPct(payload.benchmark_return_3m)}</b></span>
  `;
  metaBar.classList.remove("hidden");
}

function renderResults(results) {
  resultsEl.innerHTML = "";

  if (!results || results.length === 0) {
    resultsEl.innerHTML = `
      <div class="error-box" style="color: var(--text-secondary); border-color: var(--border);">
        Ahora mismo ninguna accion del universo analizado supera el umbral minimo de rentabilidad objetivo
        exigido (5%/mes a 3 meses). Es preferible no mostrar nada a mostrar oportunidades mediocres — vuelve a
        comprobarlo mas tarde, los datos se recalculan cada 6 horas.
      </div>`;
    resultsEl.classList.remove("hidden");
    return;
  }

  for (const r of results) {
    const node = cardTemplate.content.cloneNode(true);

    node.querySelector(".rank").textContent = `#${r.rank}`;
    node.querySelector(".ticker").textContent = `${r.ticker}${r.pe ? ` · PER ${r.pe.toFixed(1)}x` : ""}`;
    node.querySelector(".name").textContent = r.name;
    node.querySelector(".sector").textContent = [r.sector, r.industry].filter(Boolean).join(" · ");

    node.querySelector(".total-score-value").textContent = r.total_score.toFixed(0);

    node.querySelector(".price-current").textContent = fmtUSD(r.price);
    node.querySelector(".price-current-eur").textContent = fmtEUR(r.price_eur);
    node.querySelector(".price-target").textContent = fmtUSD(r.target_price);
    node.querySelector(".price-target-eur").textContent = fmtEUR(r.target_price_eur);
    node.querySelector(".upside").textContent = fmtPct(r.upside_pct);
    node.querySelector(".price-stop").textContent = fmtUSD(r.stop_loss);
    node.querySelector(".price-stop-eur").textContent = fmtEUR(r.stop_loss_eur);
    node.querySelector(".stoppct").textContent = `-${Math.abs(r.stop_loss_pct).toFixed(1)}%`;

    node.querySelector(".tech-fill").style.width = `${clampPct(r.technical_score)}%`;
    node.querySelector(".tech-num").textContent = r.technical_score.toFixed(0);
    node.querySelector(".fund-fill").style.width = `${clampPct(r.fundamental_score)}%`;
    node.querySelector(".fund-num").textContent = r.fundamental_score.toFixed(0);

    const list = node.querySelector(".rationale");
    for (const point of r.rationale) {
      const li = document.createElement("li");
      li.textContent = point;
      list.appendChild(li);
    }

    resultsEl.appendChild(node);
  }

  resultsEl.classList.remove("hidden");
}

function renderChanges(changes) {
  changesList.innerHTML = "";

  if (!changes || changes.length === 0) {
    changesList.innerHTML = '<p class="changes-empty">Sin cambios registrados en los ultimos 3 meses todavia.</p>';
    return;
  }

  for (const c of changes) {
    const node = changeTemplate.content.cloneNode(true);
    const polarity = CHANGE_POLARITY[c.type] || "neutral";
    const label = CHANGE_LABELS[c.type] || c.type;

    const badge = node.querySelector(".change-badge");
    badge.textContent = label;
    badge.classList.add(polarity);

    const [y, m, d] = c.date.slice(0, 10).split("-").map(Number);
    node.querySelector(".change-date").textContent = new Date(y, m - 1, d).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
    node.querySelector(".change-ticker").textContent = `${c.ticker} · ${c.name}`;
    node.querySelector(".change-desc").textContent = c.description;

    changesList.appendChild(node);
  }
}

function clampPct(v) {
  return Math.max(0, Math.min(100, v));
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

btn.addEventListener("click", loadData);
window.addEventListener("DOMContentLoaded", loadData);
