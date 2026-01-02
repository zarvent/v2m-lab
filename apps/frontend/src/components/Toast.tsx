import React, { useEffect, useState, useCallback } from "react";

export type ToastType = "success" | "error" | "info";

interface ToastProps {
  message: string;
  type: ToastType;
  onDismiss: () => void;
  duration?: number;
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type,
  onDismiss,
  duration = 3000,
}) => {
  const [visible, setVisible] = useState(true);

  const handleClose = useCallback(() => {
    setVisible(false);
    setTimeout(onDismiss, 200); // Esperar a la animación de salida
  }, [onDismiss]);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, handleClose]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        handleClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleClose]);

  const getIcon = () => {
    switch (type) {
      case "success":
        return "✓";
      case "error":
        return "✕";
      case "info":
        return "ℹ";
    }
  };

  // Accesibilidad basada en tipo
  const role = type === "error" ? "alert" : "status";
  const ariaLive = type === "error" ? "assertive" : "polite";

  const toastClasses = [
    "toast",
    `toast--${type}`,
    visible ? "toast--visible" : "toast--hidden",
  ].join(" ");

  return (
    <div
      className={toastClasses}
      role={role}
      aria-live={ariaLive}
      aria-atomic="true"
    >
      <span className="toast-icon" aria-hidden="true">
        {getIcon()}
      </span>
      <span className="toast-message">{message}</span>

      <button
        onClick={handleClose}
        aria-label="Cerrar notificación"
        className="toast-close"
      >
        ×
      </button>
    </div>
  );
};

Toast.displayName = "Toast";
