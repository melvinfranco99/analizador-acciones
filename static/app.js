const btn = document.getElementById("analyze-btn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");
const metaBar = document.getElementById("meta-bar");
const template = document.getElementById("card-template");

const fmtUSD = (v) =>
  v == null ? "—" : v.toLocaleString("es-ES", { style: "currency", currency: "USD" });

const fmtPct = (v, withSign = true) => {
  if (v == null) return "—";
  const sign = withSign && v > 0 ? "+" : "";
  return `${sign}${v.toFixed(1)}%`;
};

async function runAnalysis() {
  btn.disabled = true;
  btn.textContent = "Analizando… (puede tardar 1-2 min)";
  statusEl.classList.remove("hidden");
  statusEl.innerHTML = "<p>Descargando precios y fundamentales del mercado, calculando indicadores tecnicos y puntuando cada candidato…</p>";
  resultsEl.classList.add("hidden");
  metaBar.classList.add("hidden");

  try {
    const res = await fetch("/api/analyze", { method: "POST" });
    const payload = await res.json();

    if (!res.ok) {
      throw new Error(payload.error || "Error desconocido durante el analisis.");
    }

    renderMeta(payload);
    renderResults(payload.results);
    statusEl.classList.add("hidden");
  } catch (err) {
    statusEl.innerHTML = `<div class="error-box">No se pudo completar el analisis: ${escapeHtml(err.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Actualizar analisis";
  }
}

function renderMeta(payload) {
  const date = new Date(payload.generated_at);
  metaBar.innerHTML = `
    <span>Generado: <b>${date.toLocaleString("es-ES")}</b></span>
    <span>Universo analizado: <b>${payload.universe_size}</b> tickers</span>
    <span>Con datos validos: <b>${payload.tickers_with_data}</b></span>
    <span>Preseleccionados por tecnico: <b>${payload.candidates_analyzed}</b></span>
    <span>Retorno S&amp;P 500 (3m): <b>${fmtPct(payload.benchmark_return_3m)}</b></span>
    <span>Tiempo de calculo: <b>${payload.duration_seconds}s</b></span>
  `;
  metaBar.classList.remove("hidden");
}

function renderResults(results) {
  resultsEl.innerHTML = "";

  if (!results || results.length === 0) {
    resultsEl.innerHTML = '<div class="error-box">No se encontraron candidatos validos en esta ejecucion. Intentalo de nuevo.</div>';
    resultsEl.classList.remove("hidden");
    return;
  }

  for (const r of results) {
    const node = template.content.cloneNode(true);

    node.querySelector(".rank").textContent = `#${r.rank}`;
    node.querySelector(".ticker").textContent = `${r.ticker}${r.pe ? ` · PER ${r.pe.toFixed(1)}x` : ""}`;
    node.querySelector(".name").textContent = r.name;
    node.querySelector(".sector").textContent = [r.sector, r.industry].filter(Boolean).join(" · ");

    node.querySelector(".total-score-value").textContent = r.total_score.toFixed(0);

    node.querySelector(".price-current").textContent = fmtUSD(r.price);
    node.querySelector(".price-target").textContent = fmtUSD(r.target_price);
    node.querySelector(".upside").textContent = fmtPct(r.upside_pct);
    node.querySelector(".price-stop").textContent = fmtUSD(r.stop_loss);
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

function clampPct(v) {
  return Math.max(0, Math.min(100, v));
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

btn.addEventListener("click", runAnalysis);
