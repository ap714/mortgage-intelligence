import { useState } from "react";
import Tooltip from "./Tooltip.jsx";
import styles from "./BorrowerForm.module.css";

const DEFAULTS = {
  balance: "450000",
  contract_rate: "5.24",
  mortgage_type: "fixed",
  maturity_date: "",
  amortization_years_remaining: "20",
  risk_tolerance: "medium",
};

const TIPS = {
  balance:
    "The principal still owing on the mortgage — not the original amount. Check your most recent mortgage statement.",
  contract_rate:
    "The interest rate in your current mortgage contract, shown as a percentage (e.g. 5.24). Not the APR.",
  mortgage_type:
    "Fixed: your rate is locked for the term. Variable: your rate moves with the Bank of Canada's overnight rate.",
  maturity_date:
    "The date your current mortgage term ends — when renewal is due. Found on your mortgage statement or commitment letter.",
  amortization_years_remaining:
    "Total years left until the mortgage is fully paid off (not just until renewal). A 25-year mortgage started 5 years ago has 20 years remaining.",
  risk_tolerance:
    "Low: prefer payment certainty, avoid variable rates. Medium: balanced approach. High: comfortable with rate fluctuations for potential savings.",
};

export default function BorrowerForm({ onSubmit, loading }) {
  const [fields, setFields] = useState(DEFAULTS);
  const [errors, setErrors] = useState({});

  function set(key, value) {
    setFields((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: undefined }));
  }

  function validate() {
    const errs = {};
    if (!fields.balance || isNaN(Number(fields.balance)) || Number(fields.balance) <= 0)
      errs.balance = "Enter a positive balance";
    if (!fields.contract_rate || isNaN(Number(fields.contract_rate)) ||
        Number(fields.contract_rate) <= 0 || Number(fields.contract_rate) >= 100)
      errs.contract_rate = "Enter a rate between 0 and 100";
    if (!fields.maturity_date)
      errs.maturity_date = "Required";
    if (!fields.amortization_years_remaining || Number(fields.amortization_years_remaining) <= 0)
      errs.amortization_years_remaining = "Enter remaining amortization years";
    return errs;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    onSubmit({
      balance: Number(fields.balance),
      contract_rate: Number(fields.contract_rate) / 100,
      mortgage_type: fields.mortgage_type,
      maturity_date: fields.maturity_date,
      amortization_years_remaining: Number(fields.amortization_years_remaining),
      risk_tolerance: fields.risk_tolerance,
    });
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <h2 className={styles.title}>Borrower Profile</h2>

      <p className={styles.intro}>
        Enter the client's mortgage details below. The tool fetches live Bank of Canada
        rate data, runs a quantitative NPV comparison across four renewal strategies,
        and generates a data-backed recommendation via Claude.
      </p>

      <Field label="Outstanding balance (CAD)" error={errors.balance} tip={TIPS.balance}>
        <div className={styles.prefixed}>
          <span>$</span>
          <input
            type="number" min="1" max="99999999" step="1000"
            value={fields.balance}
            onChange={(e) => set("balance", e.target.value)}
            placeholder="450000"
          />
        </div>
      </Field>

      <Field label="Current contract rate (%)" error={errors.contract_rate} tip={TIPS.contract_rate}>
        <div className={styles.suffixed}>
          <input
            type="number" min="0.01" max="99.99" step="0.01"
            value={fields.contract_rate}
            onChange={(e) => set("contract_rate", e.target.value)}
            placeholder="5.24"
          />
          <span>%</span>
        </div>
      </Field>

      <div className={styles.row}>
        <Field label="Mortgage type" tip={TIPS.mortgage_type}>
          <select value={fields.mortgage_type} onChange={(e) => set("mortgage_type", e.target.value)}>
            <option value="fixed">Fixed</option>
            <option value="variable">Variable</option>
          </select>
        </Field>

        <Field label="Risk tolerance" tip={TIPS.risk_tolerance}>
          <select value={fields.risk_tolerance} onChange={(e) => set("risk_tolerance", e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </Field>
      </div>

      <Field label="Maturity date" error={errors.maturity_date} tip={TIPS.maturity_date}>
        <input
          type="date"
          value={fields.maturity_date}
          onChange={(e) => set("maturity_date", e.target.value)}
        />
      </Field>

      <Field
        label="Amortization remaining (years)"
        error={errors.amortization_years_remaining}
        tip={TIPS.amortization_years_remaining}
      >
        <input
          type="number" min="1" max="30" step="1"
          value={fields.amortization_years_remaining}
          onChange={(e) => set("amortization_years_remaining", e.target.value)}
          placeholder="20"
        />
      </Field>

      <div className={styles.hint}>
        Analysis fetches live BoC rate data and calls Claude — expect ~15–30 seconds.
      </div>

      <button type="submit" disabled={loading} className={styles.submitBtn}>
        {loading ? "Analysing…" : "Analyse"}
      </button>
    </form>
  );
}

function Field({ label, error, tip, children }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <label style={{
        display: "flex", alignItems: "center",
        fontSize: "0.82rem", color: "var(--muted)",
        marginBottom: "0.35rem", fontWeight: 500,
      }}>
        {label}
        {tip && <Tooltip text={tip} />}
      </label>
      {children}
      {error && <p style={{ color: "var(--red)", fontSize: "0.8rem", marginTop: "0.25rem" }}>{error}</p>}
    </div>
  );
}
