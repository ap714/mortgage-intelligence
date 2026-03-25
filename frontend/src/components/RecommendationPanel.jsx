import styles from "./RecommendationPanel.module.css";

const STRATEGY_LABELS = {
  renew_fixed: "Renew Fixed",
  renew_variable: "Renew Variable",
  break_and_rewrite: "Break & Rewrite",
  blend_and_extend: "Blend & Extend",
};

const STRATEGY_DESCRIPTIONS = {
  renew_fixed: "Lock in at today's 5-year fixed rate at maturity",
  renew_variable: "Move to a variable rate tied to the BoC overnight rate",
  break_and_rewrite: "Break the current term early and rewrite at a better rate",
  blend_and_extend: "Blend existing rate with today's rate, extend through your lender",
};

function fmt(n, opts = {}) {
  return new Intl.NumberFormat("en-CA", { minimumFractionDigits: 0, maximumFractionDigits: 0, ...opts }).format(n);
}

function fmtCurrency(n) {
  return "$" + fmt(Math.abs(n));
}

function fmtPct(n) {
  return (n * 100).toFixed(2) + "%";
}

function ConfidenceBadge({ score }) {
  const pct = Math.round(score * 100);
  const color = pct >= 75 ? "var(--green)" : pct >= 50 ? "var(--yellow)" : "var(--red)";
  return (
    <span style={{
      background: `color-mix(in srgb, ${color} 15%, transparent)`,
      border: `1px solid color-mix(in srgb, ${color} 40%, transparent)`,
      color,
      borderRadius: 20,
      padding: "0.2rem 0.7rem",
      fontSize: "0.82rem",
      fontWeight: 600,
    }}>
      {pct}% confidence
    </span>
  );
}

function StrategyCard({ strategy, isRecommended }) {
  const label = STRATEGY_LABELS[strategy.strategy] ?? strategy.strategy;
  const desc = STRATEGY_DESCRIPTIONS[strategy.strategy] ?? "";

  return (
    <div className={`${styles.strategyCard} ${isRecommended ? styles.recommended : ""}`}>
      <div className={styles.strategyHeader}>
        <div>
          <span className={styles.strategyLabel}>{label}</span>
          {isRecommended && <span className={styles.recommendedBadge}>Recommended</span>}
          <p className={styles.strategyDesc}>{desc}</p>
        </div>
      </div>

      <div className={styles.metrics}>
        <Metric label="Monthly payment" value={fmtCurrency(strategy.estimated_monthly_payment)} />
        <Metric label="5yr interest" value={fmtCurrency(strategy.total_interest_5yr)} />
        <Metric
          label="Break penalty"
          value={strategy.break_penalty > 0 ? fmtCurrency(strategy.break_penalty) : "—"}
          warn={strategy.break_penalty > 0}
        />
        <Metric label="5yr NPV" value={fmtCurrency(strategy.net_present_value)} />
      </div>

      {strategy.notes && (
        <p className={styles.strategyNotes}>{strategy.notes}</p>
      )}
    </div>
  );
}

function Metric({ label, value, warn }) {
  return (
    <div className={styles.metric}>
      <span className={styles.metricLabel}>{label}</span>
      <span className={styles.metricValue} style={warn ? { color: "var(--yellow)" } : {}}>
        {value}
      </span>
    </div>
  );
}

export default function RecommendationPanel({ data }) {
  const sorted = [...data.strategies].sort((a, b) => b.net_present_value - a.net_present_value);

  return (
    <div className={styles.panel}>
      {/* Top recommendation */}
      <div className={styles.hero}>
        <div className={styles.heroLeft}>
          <h3>Recommendation</h3>
          <h2 className={styles.heroStrategy}>
            {STRATEGY_LABELS[data.recommended_strategy] ?? data.recommended_strategy}
          </h2>
          <p className={styles.rationale}>{data.rationale}</p>
        </div>
        <ConfidenceBadge score={data.confidence_score} />
      </div>

      {/* Rate environment */}
      <div className={styles.rateBox}>
        <h3>Rate Environment</h3>
        <p className={styles.rateSummary}>{data.rate_environment_summary}</p>
      </div>

      {/* Strategy comparison */}
      <div>
        <h3 style={{ marginBottom: "1rem" }}>Strategy Comparison</h3>
        <div className={styles.strategyGrid}>
          {sorted.map((s) => (
            <StrategyCard
              key={s.strategy}
              strategy={s}
              isRecommended={s.strategy === data.recommended_strategy}
            />
          ))}
        </div>
      </div>

      <p className={styles.footer}>
        Generated {data.generated_at} · All monetary values in CAD · For broker use only
      </p>
    </div>
  );
}
