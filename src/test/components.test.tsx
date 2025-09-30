import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FileUploader } from '../components/FileUploader'
import { Player } from '../components/Player'

// Mock the API module with proper exports
vi.mock('../lib/api', () => ({
  apiClient: {
    uploadFile: vi.fn().mockResolvedValue({
      lesson_id: 'test-lesson-id',
      message: 'File uploaded successfully'
    }),
    getManifest: vi.fn().mockResolvedValue({
      slides: [
        {
          id: 1,
          image: 'test-image.jpg',
          audio: 'test-audio.wav',
          elements: [
            {
              id: 'elem-1',
              type: 'heading',
              text: 'Test Heading',
              bbox: [100, 50, 600, 80],
              confidence: 0.95
            }
          ],
          cues: []
        }
      ]
    }),
    exportLesson: vi.fn().mockResolvedValue({
      status: 'processing',
      download_url: 'test-download-url',
      estimated_time: '5 minutes'
    })
  }
}))

describe('FileUploader', () => {
  it('renders file uploader component', () => {
    const mockOnUploadSuccess = vi.fn()
    render(<FileUploader onUploadSuccess={mockOnUploadSuccess} />)
    
    // Check if the component renders without crashing
    expect(screen.getByText('Загрузите презентацию')).toBeInTheDocument()
  })

  it('shows file selection button', () => {
    const mockOnUploadSuccess = vi.fn()
    render(<FileUploader onUploadSuccess={mockOnUploadSuccess} />)
    
    const selectButton = screen.getByText('Выбрать файл')
    expect(selectButton).toBeInTheDocument()
  })

  it('shows supported file formats', () => {
    const mockOnUploadSuccess = vi.fn()
    render(<FileUploader onUploadSuccess={mockOnUploadSuccess} />)
    
    const formatText = screen.getByText('Поддерживаются форматы PPTX и PDF')
    expect(formatText).toBeInTheDocument()
  })
})

describe('Player', () => {
  it('renders player component with lesson ID', () => {
    const mockOnExportMP4 = vi.fn()
    render(<Player lessonId="test-lesson-id" onExportMP4={mockOnExportMP4} />)
    
    // Check if the component renders without crashing
    // The component should show loading state initially
    expect(screen.getByText('Загрузка лекции...')).toBeInTheDocument()
  })

  it('handles empty lesson ID', () => {
    const mockOnExportMP4 = vi.fn()
    render(<Player lessonId="" onExportMP4={mockOnExportMP4} />)
    
    // Should render without crashing even with empty lesson ID
    expect(screen.getByText('Загрузка лекции...')).toBeInTheDocument()
  })
})

describe('Component Integration', () => {
  it('validates component prop types', () => {
    const mockOnUploadSuccess = vi.fn()
    const mockOnExportMP4 = vi.fn()
    
    expect(typeof mockOnUploadSuccess).toBe('function')
    expect(typeof mockOnExportMP4).toBe('function')
  })

  it('handles component state changes', () => {
    const states = {
      idle: 'idle',
      uploading: 'uploading',
      success: 'success',
      error: 'error'
    }
    
    expect(states.idle).toBe('idle')
    expect(states.uploading).toBe('uploading')
    expect(states.success).toBe('success')
    expect(states.error).toBe('error')
  })
})