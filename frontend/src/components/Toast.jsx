import { useCallback, useEffect, useRef, useState } from "react";

export function useToast() {
  const [message, setMessage] = useState("");
  const timer = useRef(null);

  const show = useCallback((text) => {
    clearTimeout(timer.current);
    setMessage(text);
    timer.current = setTimeout(() => setMessage(""), 2500);
  }, []);

  useEffect(() => () => clearTimeout(timer.current), []);
  return [message, show];
}

export default function Toast({ message }) {
  return (
    <div className={`toast ${message ? "visible" : ""}`} role="status" aria-live="polite">
      {message}
    </div>
  );
}
