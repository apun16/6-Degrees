const SUPABASE_URL = 'https://ncbnvjvqfleehxqhlpzv.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jYm52anZxZmxlZWh4cWhscHp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgxODY1NjUsImV4cCI6MjA4Mzc2MjU2NX0.ZNB0nh8xOaBTMcLTNHcrpBH6P_foePF7Vpz-UJibqc4'

export async function saveGame(gameResult) {
  try {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/games`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify({
        start_word: gameResult.start_word,
        end_word: gameResult.end_word,
        player_path: gameResult.player_path?.join(',') || '',
        optimal_path: gameResult.optimal_path?.join(',') || '',
        player_length: gameResult.player_length,
        optimal_length: gameResult.optimal_length,
        score: gameResult.score,
        valid: gameResult.valid || false,
        hints_used: gameResult.hints_used || 0,
      }),
    })

    if (!response.ok) {
      console.error('Failed to save game to Supabase:', response.status)
      return false
    }

    return true
  } catch (error) {
    console.error('Error saving game to Supabase:', error)
    return false
  }
}

export async function getTotalGames() {
  try {
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/games?select=count`,
      {
        method: 'HEAD',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Prefer': 'count=exact',
        },
      }
    )

    if (!response.ok) {
      console.error('Failed to get game count:', response.status)
      return null
    }

    const count = response.headers.get('content-range')
    if (count) {
      const total = count.split('/')[1]
      return parseInt(total, 10)
    }

    return 0
  } catch (error) {
    console.error('Error getting game count:', error)
    return null
  }
}

export async function getGameStats() {
  try {
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/games?select=score,player_length,optimal_length&order=completed_at.desc&limit=100`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    )

    if (!response.ok) {
      return null
    }

    const games = await response.json()
    
    if (!games.length) {
      return { total: 0, perfect: 0, avgScore: 0 }
    }

    const total = games.length
    const perfect = games.filter(g => g.score === 100).length
    const avgScore = games.reduce((sum, g) => sum + g.score, 0) / total

    return { total, perfect, avgScore: Math.round(avgScore) }
  } catch (error) {
    console.error('Error getting stats:', error)
    return null
  }
}