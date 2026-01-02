# Bolt's Journal

## 2024-05-22 - Initial Journal Creation
**Learning:** Journal created to track performance learnings.
**Action:** Always check this journal before starting work.

## 2024-05-22 - Frontend Polling Optimization
**Learning:** Frequent polling (500ms) can cause excessive root-level re-renders if the polled state (even a timestamp) is unconditionally updated in the React state.
**Action:** Throttle non-critical state updates (like "last ping time") to a slower interval (e.g., 5s) while keeping the actual data polling frequent. Use `useRef` to track the last update time without triggering re-renders.

## 2025-05-23 - Fuzzy Telemetry Comparison
**Learning:** Strict equality checks (`===`) on floating-point telemetry data (CPU/RAM %) cause excessive React re-renders even when the system is effectively stable (e.g., 10.123% vs 10.124%). This propagates updates to graphs and layouts unnecessarily every 500ms.
**Action:** Implement fuzzy comparison (epsilon) for floating-point telemetry fields to ignore negligible fluctuations. Only trigger state updates when the change is visually relevant (e.g., > 0.1%).
