import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { Player } from '@/components/Player'
import { FileUploader } from '@/components/FileUploader'
import { apiClient } from '@/lib/api'

// Mock API client
vi.mock('@/lib/api', () => ({
  apiClient: {
    getManifest: vi.fn(),
    uploadFile: vi.fn(),
  }
}))

// Mock manifest data
const mockManifest = {
  slides: [
    {
      id: 1,
      image: '/assets/test/slides/001.png',
      audio: '/assets/test/audio/001.mp3',
      elements: [
        {
          id: 'elem_1',
          type: 'text',
          bbox: [100, 100, 200, 50],
          text: 'Test Element',
          confidence: 0.95
        }
      ],
      cues: [
        {
          cue_id: 'cue_1',
          t0: 0.5,
          t1: 2.0,
          action: 'highlight',
          bbox: [100, 100, 200, 50],
          element_id: 'elem_1'
        }
      ]
    }
  ],
  timeline: {
    rules: [],
    default_duration: 2.0,
    transition_duration: 0.5,
    min_highlight_duration: 0.8,
    min_gap: 0.2,
    max_total_duration: 90.0,
    smoothness_enabled: true
  }
}

describe('Player Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render loading state initially', () => {
    const mockOnExportMP4 = vi.fn()
    render(<Player lessonId="test-lesson" onExportMP4={mockOnExportMP4} />)
    
    expect(screen.getByText('Загрузка лекции...')).toBeInTheDocument()
  })

  it('should render error state when manifest fails to load', async () => {
    const mockOnExportMP4 = vi.fn()
    vi.mocked(apiClient.getManifest).mockRejectedValue(new Error('Failed to load'))
    
    render(<Player lessonId="test-lesson" onExportMP4={mockOnExportMP4} />)
    
    await waitFor(() => {
      expect(screen.getByText('Ошибка загрузки лекции')).toBeInTheDocument()
    })
  })

  it('should render player when manifest loads successfully', async () => {
    const mockOnExportMP4 = vi.fn()
    vi.mocked(apiClient.getManifest).mockResolvedValue(mockManifest)
    
    render(<Player lessonId="test-lesson" onExportMP4={mockOnExportMP4} />)
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /play/i })).toBeInTheDocument()
    })
  })

  it('should toggle play/pause when play button is clicked', async () => {
    const mockOnExportMP4 = vi.fn()
    vi.mocked(apiClient.getManifest).mockResolvedValue(mockManifest)
    
    render(<Player lessonId="test-lesson" onExportMP4={mockOnExportMP4} />)
    
    await waitFor(() => {
      const playButton = screen.getByRole('button', { name: /play/i })
      fireEvent.click(playButton)
    })
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
    })
  })

  it('should navigate between slides', async () => {
    const mockOnExportMP4 = vi.fn()
    const manifestWithMultipleSlides = {
      ...mockManifest,
      slides: [
        ...mockManifest.slides,
        {
          id: 2,
          image: '/assets/test/slides/002.png',
          audio: '/assets/test/audio/002.mp3',
          elements: [],
          cues: []
        }
      ]
    }
    vi.mocked(apiClient.getManifest).mockResolvedValue(manifestWithMultipleSlides)
    
    render(<Player lessonId="test-lesson" onExportMP4={mockOnExportMP4} />)
    
    await waitFor(() => {
      const nextButton = screen.getByRole('button', { name: /next/i })
      fireEvent.click(nextButton)
    })
    
    // Should be on slide 2 now
    expect(screen.getByText('2 / 2')).toBeInTheDocument()
  })
})

describe('FileUploader Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render upload area', () => {
    const mockOnUploadSuccess = vi.fn()
    render(<FileUploader onUploadSuccess={mockOnUploadSuccess} />)
    
    expect(screen.getByText(/перетащите файл/i)).toBeInTheDocument()
  })

  it('should handle file selection', async () => {
    const mockOnUploadSuccess = vi.fn()
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    vi.mocked(apiClient.uploadFile).mockResolvedValue({ lesson_id: 'test-id' })
    
    render(<FileUploader onUploadSuccess={mockOnUploadSuccess} />)
    
    const fileInput = screen.getByLabelText(/выберите файл/i)
    fireEvent.change(fileInput, { target: { files: [mockFile] } })
    
    await waitFor(() => {
      expect(apiClient.uploadFile).toHaveBeenCalledWith(mockFile)
    })
  })

  it('should reject invalid file types', () => {
    const mockOnUploadSuccess = vi.fn()
    const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
    
    render(<FileUploader onUploadSuccess={mockOnUploadSuccess} />)
    
    const fileInput = screen.getByLabelText(/выберите файл/i)
    fireEvent.change(fileInput, { target: { files: [mockFile] } })
    
    expect(screen.getByText(/ошибка/i)).toBeInTheDocument()
  })

  it('should handle drag and drop', () => {
    const mockOnUploadSuccess = vi.fn()
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    
    render(<FileUploader onUploadSuccess={mockOnUploadSuccess} />)
    
    const dropArea = screen.getByText(/перетащите файл/i).closest('div')
    
    fireEvent.dragOver(dropArea!)
    fireEvent.drop(dropArea!, { dataTransfer: { files: [mockFile] } })
    
    expect(screen.getByText(/загрузка/i)).toBeInTheDocument()
  })
})

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have correct API base URL', () => {
    expect(apiClient.baseUrl).toBe('http://localhost:8000')
  })

  it('should handle upload response correctly', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
    const mockResponse = { lesson_id: 'test-lesson-id' }
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    })
    
    const result = await apiClient.uploadFile(mockFile)
    
    expect(result).toEqual(mockResponse)
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/upload',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData)
      })
    )
  })

  it('should handle manifest request correctly', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockManifest)
    })
    
    const result = await apiClient.getManifest('test-lesson')
    
    expect(result).toEqual(mockManifest)
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/lessons/test-lesson/manifest')
  })

  it('should handle API errors', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Not Found'
    })
    
    await expect(apiClient.getManifest('invalid-lesson')).rejects.toThrow('Failed to fetch manifest: Not Found')
  })
})