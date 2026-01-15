import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { StudioEditor } from "./StudioEditor";

describe("StudioEditor", () => {
  const defaultProps = {
    content: "Test content",
    lines: ["Test content"],
    isRecording: false,
    isTranscribing: false,
    isProcessing: false,
    isBusy: false,
    timerFormatted: "00:00",
    onContentChange: vi.fn(),
  };

  it("renders content correctly", () => {
    render(<StudioEditor {...defaultProps} />);
    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  it("applies recording styles when isRecording is true", () => {
    const { container } = render(<StudioEditor {...defaultProps} isRecording={true} />);

    // Find the main editor container
    // Based on the refactor, the first child of the rendered component is the container
    const editorContainer = container.firstChild as HTMLElement;

    // Check for the recording class/style
    // In Tailwind migration: border-error shadow-[...] animate-pulse-border
    expect(editorContainer).toHaveClass("border-error");
    expect(editorContainer).toHaveClass("animate-pulse-border");

    // Check for "Recording" badge text
    expect(screen.getByText("Grabando")).toBeInTheDocument();
  });

  it("shows editable badge when not busy or recording", () => {
    render(<StudioEditor {...defaultProps} />);
    expect(screen.getByText("editable")).toBeInTheDocument();
  });
});
