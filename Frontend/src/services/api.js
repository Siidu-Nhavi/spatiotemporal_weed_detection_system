const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export async function analyzeImage(file, settings) {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('rows', settings.rows)
  formData.append('columns', settings.columns)
  formData.append('low_threshold', settings.lowThreshold)
  formData.append('high_threshold', settings.highThreshold)

  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    body: formData,
  })
  const body = await response.json()
  if (!response.ok) {
    throw new Error(body.detail || 'Analysis failed')
  }
  return body
}

export async function exportAnalysis(file, settings, format) {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('export_format', format)
  formData.append('rows', settings.rows)
  formData.append('columns', settings.columns)
  formData.append('low_threshold', settings.lowThreshold)
  formData.append('high_threshold', settings.highThreshold)

  const response = await fetch(`${API_BASE_URL}/export`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    let message = 'Export failed'
    try {
      const body = await response.json()
      message = body.detail || message
    } catch {
      // Preserve the generic message when the server does not return JSON.
    }
    throw new Error(message)
  }
  return response.blob()
}
