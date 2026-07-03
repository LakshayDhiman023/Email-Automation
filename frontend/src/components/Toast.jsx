import { createContext, useCallback, useContext, useState } from "react";

const ToastCtx = createContext(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const push = useCallback((message, type = "info") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);

  const colors = {
    info: "bg-brand-ink",
    success: "bg-emerald-500",
    error: "bg-rose-500",
  };

  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div
        className="fixed bottom-5 right-5 z-50 space-y-2"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`${colors[t.type]} text-white text-sm px-4 py-2.5 rounded-lg shadow-lg animate-[slidein_0.2s_ease-out]`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
