// API utility functions for backend communication
// In production, set NEXT_PUBLIC_API_URL in Vercel environment variables
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (
  typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:5001/api'
    : 'https://YOUR-RAILWAY-URL.up.railway.app/api'  // Replace with your Railway URL
)

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  try {
    const response = await fetch(url, config)
    
    // Handle non-JSON responses
    let data
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    } else {
      const text = await response.text()
      throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`)
    }
    
    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`)
    }
    
    return data
  } catch (error) {
    // More detailed error logging
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      console.error(`Network Error: Cannot connect to backend at ${url}`)
      console.error('Make sure the backend server is running on http://localhost:5000')
      throw new Error('Cannot connect to server. Please ensure the backend is running.')
    }
    console.error(`API Error (${endpoint}):`, error)
    throw error
  }
}

export const api = {
  // Get new game puzzle
  getNewGame: async () => {
    const data = await apiRequest('/game/new')
    // Also get optimal path length for display
    const pathData = await apiRequest('/game/path', {
      method: 'POST',
      body: JSON.stringify({
        startWord: data.startWord,
        targetWord: data.targetWord,
      }),
    })
    return {
      start_word: data.startWord,
      end_word: data.targetWord,
      optimal_length: pathData.steps || 0,
    }
  },

  // Validate a word in the chain
  validateWord: async (word, currentPath, startWord) => {
    // Build full path including start word for duplicate check
    const fullPath = startWord ? [startWord, ...(currentPath || [])] : (currentPath || [])
    
    return apiRequest('/game/validate', {
      method: 'POST',
      body: JSON.stringify({
        word,
        currentPath: currentPath || [],
        startWord,
        fullPath: fullPath, // Include full path for duplicate checking
      }),
    })
  },

  // Submit completed chain
  submitChain: async (path, startWord, targetWord) => {
    return apiRequest('/game/submit', {
      method: 'POST',
      body: JSON.stringify({
        path,
        startWord,
        targetWord,
      }),
    })
  },

  // Get hint
  getHint: async (startWord, targetWord, currentPath = [], hintLevel = 1) => {
    const pathStr = currentPath.join(',')
    return apiRequest(`/game/hint?startWord=${encodeURIComponent(startWord)}&targetWord=${encodeURIComponent(targetWord)}&currentPath=${encodeURIComponent(pathStr)}&hintLevel=${hintLevel}`)
  },

  // Get stats
  getStats: async () => {
    return apiRequest('/stats')
  },
}