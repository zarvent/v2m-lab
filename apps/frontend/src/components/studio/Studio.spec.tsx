import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Studio } from '../Studio';
import { StudioHeader } from './StudioHeader';
import { StudioEmptyState } from './StudioEmptyState';

// Mocks
vi.mock('../../hooks/useNoteTabs', () => ({
  useNoteTabs: () => ({
    tabs: [{ id: '1', title: 'Test Tab', content: 'Test Content', language: 'es' }],
    activeTabId: '1',
    activeTab: { id: '1', title: 'Test Tab', content: 'Test Content', language: 'es' },
    addTab: vi.fn(),
    removeTab: vi.fn(),
    setActiveTab: vi.fn(),
    updateTabContent: vi.fn(),
    updateTabTitle: vi.fn(),
    updateTabLanguage: vi.fn(),
    reorderTabs: vi.fn(),
  }),
}));

vi.mock('../../utils', () => ({
  countWords: (text: string) => text.split(/\s+/).filter(Boolean).length,
}));

vi.mock('../../assets/Icons', () => ({
  SaveIcon: () => <span data-testid="icon-save" />,
  ExportIcon: () => <span data-testid="icon-export" />,
  MicIcon: () => <span data-testid="icon-mic" />,
  CopyIcon: () => <span data-testid="icon-copy" />,
  CheckIcon: () => <span data-testid="icon-check" />,
  EditIcon: () => <span data-testid="icon-edit" />,
  FileTextIcon: () => <span data-testid="icon-file-text" />,
  FileCodeIcon: () => <span data-testid="icon-file-code" />,
  FileJsonIcon: () => <span data-testid="icon-file-json" />,
  PlusIcon: () => <span data-testid="icon-plus" />,
}));

vi.mock('../TabBar', () => ({
  TabBar: () => <div data-testid="tab-bar" />,
}));

describe('Studio Components', () => {
  describe('StudioHeader', () => {
    it('renders title correctly', () => {
      const props = {
        noteTitle: 'Test Note',
        isEditingTitle: false,
        hasContent: true,
        isBusy: false,
        currentLanguage: 'es' as const,
        copyState: 'idle' as const,
        onTitleChange: vi.fn(),
        onTitleSubmit: vi.fn(),
        onEditTitle: vi.fn(),
        onCopy: vi.fn(),
        onTranslate: vi.fn(),
        onExport: vi.fn(),
        onSaveToLibrary: vi.fn(),
      };

      render(<StudioHeader {...props} />);
      expect(screen.getByText('Test Note')).toBeInTheDocument();
      expect(screen.getByText('Borrador')).toBeInTheDocument();
    });

    it('switches to edit mode on click', () => {
      const onEditTitle = vi.fn();
      const props = {
        noteTitle: 'Test Note',
        isEditingTitle: false,
        hasContent: true,
        isBusy: false,
        currentLanguage: 'es' as const,
        copyState: 'idle' as const,
        onTitleChange: vi.fn(),
        onTitleSubmit: vi.fn(),
        onEditTitle,
        onCopy: vi.fn(),
        onTranslate: vi.fn(),
        onExport: vi.fn(),
        onSaveToLibrary: vi.fn(),
      };

      render(<StudioHeader {...props} />);
      fireEvent.click(screen.getByLabelText('Clic para editar título'));
      expect(onEditTitle).toHaveBeenCalled();
    });
  });

  describe('StudioEmptyState', () => {
    it('renders empty state message', () => {
        const props = {
            isIdle: true,
            recordShortcut: 'Ctrl+Space',
            onStartRecording: vi.fn(),
        };
        render(<StudioEmptyState {...props} />);
        expect(screen.getByText('Captura tus ideas')).toBeInTheDocument();
        expect(screen.getByText('Iniciar Captura')).toBeInTheDocument();
    });
  });

  describe('Studio Integration', () => {
    it('renders full studio', () => {
        const props = {
            status: 'idle' as const,
            transcription: '',
            timerFormatted: '00:00',
            errorMessage: '',
            onStartRecording: vi.fn(),
            onStopRecording: vi.fn(),
            onClearError: vi.fn(),
        };

        // Mock useStudio hook implementation for integration test if needed,
        // or rely on the mock of useNoteTabs and let useStudio run.
        // Since we didn't mock useStudio, it will run.

        render(<Studio {...props} />);

        // useStudio uses useNoteTabs which returns 'Test Tab' as title.
        expect(screen.getAllByText('Test Tab').length).toBeGreaterThan(0);
        expect(screen.getByTestId('tab-bar')).toBeInTheDocument();
    });
  });
});
