import React from "react";

export const RecordingWaveform: React.FC = React.memo(() => (
  <div className="recording-waveform" aria-hidden="true">
    {[...Array(5)].map((_, i) => (
      <span
        key={i}
        className="waveform-bar"
        style={{ animationDelay: `${i * 0.1}s` }}
      />
    ))}
  </div>
));
RecordingWaveform.displayName = "RecordingWaveform";
