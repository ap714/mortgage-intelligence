import { useState } from "react";
import BorrowerForm from "./components/BorrowerForm.jsx";
import RecommendationPanel from "./components/RecommendationPanel.jsx";
import styles from "./App.module.css";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(formData) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server error ${res.status}`);
      }
      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>⬡</span>
          <span>Mortgage Renewal Intelligence</span>
        </div>
        <p className={styles.tagline}>Data-backed renewal strategy for Canadian brokers</p>
      </header>

      <main className={styles.main}>
        <section className={styles.formSection}>
          <BorrowerForm onSubmit={handleSubmit} loading={loading} />
        </section>

        <section className={styles.resultSection}>
          {loading && <LoadingState />}
          {error && <ErrorState message={error} />}
          {result && <RecommendationPanel data={result} />}
          {!loading && !error && !result && <EmptyState />}
        </section>
      </main>
    </div>
  );
}

function LoadingState() {
  return (
    <div style={{ textAlign: "center", padding: "3rem 1rem", color: "var(--muted)" }}>
      <div className="spinner" style={{
        width: 36, height: 36, border: "3px solid var(--border)",
        borderTopColor: "var(--accent)", borderRadius: "50%",
        animation: "spin 0.8s linear infinite", margin: "0 auto 1rem",
      }} />
      <p>Analysing renewal strategies…</p>
      <p style={{ fontSize: "0.85rem", marginTop: "0.4rem" }}>Fetching live rates · Running NPV model · Generating advice</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function ErrorState({ message }) {
  return (
    <div style={{
      background: "rgba(240,96,96,0.08)", border: "1px solid rgba(240,96,96,0.3)",
      borderRadius: "var(--radius)", padding: "1.25rem 1.5rem",
    }}>
      <p style={{ color: "var(--red)", fontWeight: 600, marginBottom: "0.3rem" }}>Analysis failed</p>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{message}</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{ textAlign: "center", padding: "3rem 1rem", color: "var(--muted)" }}>
      <p style={{ fontSize: "2rem", marginBottom: "0.75rem" }}>📋</p>
      <p>Fill in the borrower details and click <strong style={{ color: "var(--text)" }}>Analyse</strong> to get a strategy recommendation.</p>
    </div>
  );
}
