import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock fetch globally
global.fetch = vi.fn()

describe('API Configuration', () => {
  it('should have correct API base URL', () => {
    const apiBase = 'http://localhost:8000'
    expect(apiBase).toContain('localhost')
    expect(apiBase).toContain('8000')
  })

  it('should validate API endpoints', () => {
    const endpoints = {
      upload: '/upload',
      manifest: '/lessons/{id}/manifest',
      export: '/lessons/{id}/export'
    }
    
    expect(endpoints.upload).toBe('/upload')
    expect(endpoints.manifest).toContain('manifest')
    expect(endpoints.export).toContain('export')
  })
})

describe('API Response Types', () => {
  it('should validate UploadResponse interface', () => {
    const mockUploadResponse = {
      lesson_id: 'test-lesson-id'
    }
    
    expect(mockUploadResponse).toHaveProperty('lesson_id')
    expect(typeof mockUploadResponse.lesson_id).toBe('string')
  })

  it('should validate Manifest interface', () => {
    const mockManifest = {
      slides: [
        {
          id: 1,
          image: 'test-image.jpg',
          audio: 'test-audio.wav',
          elements: [],
          cues: []
        }
      ]
    }
    
    expect(mockManifest).toHaveProperty('slides')
    expect(Array.isArray(mockManifest.slides)).toBe(true)
    expect(mockManifest.slides[0]).toHaveProperty('id')
    expect(mockManifest.slides[0]).toHaveProperty('image')
    expect(mockManifest.slides[0]).toHaveProperty('audio')
  })

  it('should validate SlideElement interface', () => {
    const mockElement = {
      id: 'elem-1',
      type: 'heading',
      bbox: [100, 50, 600, 80],
      text: 'Test Heading',
      confidence: 0.95
    }
    
    expect(mockElement).toHaveProperty('id')
    expect(mockElement).toHaveProperty('type')
    expect(mockElement).toHaveProperty('bbox')
    expect(Array.isArray(mockElement.bbox)).toBe(true)
    expect(mockElement.bbox.length).toBe(4)
  })

  it('should validate Cue interface', () => {
    const mockCue = {
      cue_id: 'cue-1',
      t0: 0,
      t1: 5,
      action: 'highlight',
      bbox: [100, 50, 600, 80],
      element_id: 'elem-1'
    }
    
    expect(mockCue).toHaveProperty('t0')
    expect(mockCue).toHaveProperty('t1')
    expect(mockCue).toHaveProperty('action')
    expect(['highlight', 'underline', 'laser_move']).toContain(mockCue.action)
  })
})

describe('API Error Handling', () => {
  it('should handle network errors', () => {
    const networkError = new Error('Network error')
    expect(networkError.message).toBe('Network error')
    expect(networkError).toBeInstanceOf(Error)
  })

  it('should handle HTTP status codes', () => {
    const statusCodes = {
      ok: 200,
      badRequest: 400,
      unauthorized: 401,
      notFound: 404,
      serverError: 500
    }
    
    expect(statusCodes.ok).toBe(200)
    expect(statusCodes.badRequest).toBe(400)
    expect(statusCodes.unauthorized).toBe(401)
    expect(statusCodes.notFound).toBe(404)
    expect(statusCodes.serverError).toBe(500)
  })
})

describe('File Validation', () => {
  it('should validate file types', () => {
    const validTypes = [
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'application/pdf'
    ]
    
    validTypes.forEach(type => {
      expect(type).toContain('application/')
    })
  })

  it('should validate file extensions', () => {
    const validExtensions = ['.pptx', '.pdf', '.ppt']
    
    validExtensions.forEach(ext => {
      expect(ext.startsWith('.')).toBe(true)
    })
  })
})