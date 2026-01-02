## 2024-05-24 - [Modal Initial Focus Management]
**Learning:** When a modal opens, if focus is not programmatically moved into it, keyboard users (and screen readers) remain focused on the background content, leading to a confusing navigation experience. The simple act of focusing the first interactive element (like the close button) or the modal container itself anchors the user in the new context.
**Action:** Always implement `autoFocus` on the first meaningful interactive element of a modal (often the Close button) or use a `ref` to focus the container if it has a role of `dialog`.

## 2024-05-24 - [Input State Robustness]
**Learning:** Controlled inputs that rely on numerical parsing (e.g., `parseInt`) can become difficult to use if they don't gracefully handle intermediate states like empty strings or `NaN`. This often prevents users from clearing a field to type a new value.
**Action:** When binding number inputs to state, handle `NaN` or empty strings gracefully in the `onChange` handler, either by falling back to a default value only on blur/submit, or by allowing the internal state to be temporarily invalid/empty to facilitate typing.
## 2025-12-13 - [Accessibility of Critical Feedback]
**Learning:** Error banners are critical for user trust, but without `role="alert"` and `aria-live="assertive"`, screen reader users might miss the context of why the app stopped working. Simple inline changes can drastically improve this without needing a full UI component library.
**Action:** Always wrap error messages in a container with `role="alert"` and `aria-live="assertive"`. Ensure close buttons have `aria-label`.

## 2025-12-13 - [Icon-Only Button Accessibility]
**Learning:** Icon-only buttons (like GitHub links or settings toggles) are visually clean but often lack `aria-label`s, relying only on `title`. `title` is not reliably read by all assistive technologies.
**Action:** Always add `aria-label` to buttons that do not have visible text content. Consider dynamic labels for toggle states (e.g., "Show X" vs "Hide X") for better context.
## 2024-05-23 - [Modal Keyboard Accessibility]
**Learning:** Modals often lack basic keyboard accessibility features like closing with the `Escape` key. This is a critical expectation for keyboard users and power users alike, and its absence can make the application feel "trapped" or unpolished.
**Action:** Always add a `keydown` listener for `Escape` in modal components to trigger the close action.

## 2025-12-13 - [Status Indicator Accessibility]
**Learning:** Purely visual status indicators (like colored dots) are invisible to screen readers and often inaccessible to keyboard users.
**Action:** Use `role="status"` and `tabIndex={0}` on status containers. Provide a descriptive `aria-label` that includes the full status state (e.g., "Status: Connected") so keyboard users can tab to it and hear the current state.

## 2025-05-27 - [Toggle Switch Interaction]
**Learning:** Replacing native small checkboxes with larger toggle switches not only improves the "delight" factor but significantly aids motor accessibility by increasing the click target size. When doing so, ensuring the underlying `input` remains accessible (focus management) is critical.
**Action:** Use CSS-only toggle switches that wrap a standard `checkbox` input. Maintain keyboard focus visibility on the input element but visualize it on the slider.
