import { useState } from "react";
import styles from "./BorrowerForm.module.css";

const DEFAULTS = {
  balance: "450000",
  contract_rate: "5.24",
  mortgage_type: "fixed",
  maturity_date: "",
  amortization_years_remaining: "20",
  risk_tolerance: "medium",
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

      <Field label="Outstanding balance (CAD)" error={errors.balance}>
        <div className={styles.prefixed}>
          <span>$</span>
          <input
            type="number" min="1" step="1000"
            value={fields.balance}
            onChange={(e) => set("balance", e.target.value)}
            placeholder="450,000"
          />
        </div>
      </Field>

      <Field label="Current contract rate (%)" error={errors.contract_rate}>
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
        <Field label="Mortgage type" error={errors.mortgage_type}>
          <select value={fields.mortgage_type} onChange={(e) => set("mortgage_type", e.target.value)}>
            <option value="fixed">Fixed</option>
            <option value="variable">Variable</option>
          </select>
        </Field>

        <Field label="Risk tolerance" error={errors.risk_tolerance}>
          <select value={fields.risk_tolerance} onChange={(e) => set("risk_tolerance", e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </Field>
      </div>

      <Field label="Maturity date" error={errors.maturity_date}>
        <input
          type="date"
          value={fields.maturity_date}
          onChange={(e) => set("maturity_date", e.target.value)}
        />
      </Field>

      <Field label="Amortization remaining (years)" error={errors.amortization_years_remaining}>
        <input
          type="number" min="1" max="30" step="1"
          value={fields.amortization_years_remaining}
          onChange={(e) => set("amortization_years_remaining", e.target.value)}
          placeholder="20"
        />
      </Field>

      <button
        type="submit"
        disabled={loading}
        className={styles.submitBtn}
      >
        {loading ? "Analysing…" : "Analyse"}
      </button>
    </form>
  );
}

function Field({ label, error, children }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <label style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.35rem", fontWeight: 500 }}>
        {label}
      </label>
      {children}
      {error && <p style={{ color: "var(--red)", fontSize: "0.8rem", marginTop: "0.25rem" }}>{error}</p>}
    </div>
  );
}
