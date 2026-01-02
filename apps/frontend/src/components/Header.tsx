import React from "react";
import { ChartIcon, SettingsIcon, GithubIcon } from "../assets/Icons";
import { ConnectionIndicator } from "./ConnectionIndicator";

interface HeaderProps {
  isConnected: boolean;
  lastPingTime: number | null;
  showDashboard: boolean;
  onToggleDashboard: () => void;
  onOpenSettings: () => void;
}

export const Header = React.memo(
  ({
    isConnected,
    lastPingTime,
    showDashboard,
    onToggleDashboard,
    onOpenSettings,
  }: HeaderProps) => {
    return (
      <header>
        <div className="brand">
          <div className="brand-icon"></div>
          voice2machine
        </div>

        <div className="header-actions">
          <ConnectionIndicator
            isConnected={isConnected}
            lastPingTime={lastPingTime}
          />

          <div className="header-divider"></div>

          <a
            href="https://github.com/zarvent/voice2machine"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-icon"
            title="Code on GitHub"
            aria-label="Code on GitHub"
          >
            <GithubIcon />
          </a>

          <button
            onClick={onToggleDashboard}
            className={`btn-icon ${showDashboard ? "active" : ""}`}
            title="System Metrics"
            aria-label={
              showDashboard ? "Hide System Metrics" : "Show System Metrics"
            }
          >
            <ChartIcon />
          </button>

          <button
            onClick={onOpenSettings}
            className="btn-icon"
            title="Settings"
            aria-label="Settings"
          >
            <SettingsIcon />
          </button>
        </div>
      </header>
    );
  }
);

Header.displayName = "Header";
