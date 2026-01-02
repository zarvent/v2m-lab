import React from "react";

interface ConnectionIndicatorProps {
  isConnected: boolean;
  lastPingTime: number | null;
}

export const ConnectionIndicator: React.FC<ConnectionIndicatorProps> = ({
  isConnected,
  lastPingTime,
}) => {
  const timeString = lastPingTime
    ? new Date(lastPingTime).toLocaleTimeString()
    : "--:--";

  const statusText = isConnected ? "Conectado" : "Desconectado";
  const label = `Estado: ${statusText} (Último ping: ${timeString})`;

  return (
    <div
      role="status"
      tabIndex={0}
      aria-label={label}
      title={label}
      className="connection-indicator"
    >
      <div
        className="connection-dot"
        data-status={isConnected ? "connected" : "disconnected"}
        aria-hidden="true"
      />
    </div>
  );
};

ConnectionIndicator.displayName = "ConnectionIndicator";
