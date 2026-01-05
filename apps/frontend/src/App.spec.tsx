import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from './App'
import { invoke } from '@tauri-apps/api/core'

// Mock de componentes complejos para aislar la prueba de App
vi.mock('./components/Sidebar', () => ({
  Sidebar: ({ activeNav, onNavChange, onOpenSettings }: any) => (
    <div data-testid="sidebar">
      <button onClick={() => onNavChange('studio')}>Studio</button>
      <button onClick={() => onNavChange('overview')}>Overview</button>
      <button onClick={onOpenSettings}>Settings</button>
    </div>
  )
}))

vi.mock('./components/Studio', () => ({
  Studio: ({ status }: any) => <div data-testid="studio-view">Status: {status}</div>
}))

vi.mock('./components/Overview', () => ({
  Overview: () => <div data-testid="overview-view">Overview Content</div>
}))

// Mock de useBackend para controlar el estado
const mockBackendState = {
  status: 'idle',
  transcription: '',
  telemetry: null,
  cpuHistory: [],
  ramHistory: [],
  errorMessage: '',
  isConnected: true,
  lastPingTime: Date.now(),
  history: []
}

const mockActions = {
  startRecording: vi.fn(),
  stopRecording: vi.fn(),
  setTranscription: vi.fn(),
  clearError: vi.fn(),
  translateText: vi.fn(),
  restartDaemon: vi.fn(),
  shutdownDaemon: vi.fn(),
  togglePause: vi.fn()
}

vi.mock('./hooks/useBackend', () => ({
  useBackend: () => [mockBackendState, mockActions]
}))

// Mock de useTimer
vi.mock('./hooks/useTimer', () => ({
  useTimer: () => ({ formatted: '00:00' })
}))

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renderiza la vista inicial (Studio) correctamente', () => {
    render(<App />)
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('studio-view')).toBeInTheDocument()
    expect(screen.queryByTestId('overview-view')).not.toBeInTheDocument()
  })

  it('cambia de vista al navegar', () => {
    render(<App />)

    // Simular clic en Overview desde el Sidebar mockeado
    fireEvent.click(screen.getByText('Overview'))

    expect(screen.getByTestId('overview-view')).toBeInTheDocument()
    expect(screen.queryByTestId('studio-view')).not.toBeInTheDocument()
  })

  it('maneja el atajo de teclado global para grabación (Ctrl+Space)', () => {
    render(<App />)

    // Simular Ctrl+Space
    fireEvent.keyDown(window, { key: ' ', code: 'Space', ctrlKey: true })

    expect(mockActions.startRecording).toHaveBeenCalled()
  })
})
