import { useState, useRef, useEffect } from "react";
import styles from "./Tooltip.module.css";

export default function Tooltip({ text }) {
  const [visible, setVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setVisible(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <span ref={ref} className={styles.wrap}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setVisible((v) => !v)}
        aria-label="More info"
      >
        ?
      </button>
      {visible && (
        <span className={styles.bubble} role="tooltip">
          {text}
        </span>
      )}
    </span>
  );
}
