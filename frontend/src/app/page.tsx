'use client'

import { useState, useEffect, useCallback } from 'react'
import Landing from '../components/Landing'
import Game from '../components/Game'
import Results from '../components/Results'
import HowToPlay from '../components/HowToPlay'
import GitHubIcon from '../components/GitHubIcon' 
import { api } from '../utils/api'
import styles from '../styles/page.module.css'

interface Puzzle {
  start_word: string
  end_word: string
  optimal_length: number
}

interface Hint {
  hint: string
  hint_level: number
  word?: string
  masked_word?: string
  word_length?: number
  fully_revealed?: boolean
  steps_remaining?: number
}

interface ResultData {
  start_word: string
  end_word: string
  player_path: string[]
  optimal_path: string[]
  player_length: number
  optimal_length: number
  score: number
  valid: boolean
}

export default function Page() {
  const [started, setStarted] = useState(false)
  const [showHowToPlay, setShowHowToPlay] = useState(false)
  const [puzzle, setPuzzle] = useState<Puzzle | null>(null)
  const [chain, setChain] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [hint, setHint] = useState<Hint | null>(null)
  const [hintsUsed, setHintsUsed] = useState(0)
  const [showResults, setShowResults] = useState(false)
  const [resultData, setResultData] = useState<ResultData | null>(null)

  // Load new game
  const loadNewGame = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    setChain([])
    setHint(null)
    setHintsUsed(0)
    setShowResults(false)
    setResultData(null)
    
    try {
      const newPuzzle = await api.getNewGame()
      setPuzzle(newPuzzle)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load new game'
      setError(errorMessage)
      console.error('Error loading game:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initialize game when starting
  useEffect(() => {
    if (started && !puzzle) {
      loadNewGame()
    }
  }, [started, puzzle, loadNewGame])

  // Add word to chain
  const handleAddWord = useCallback(async (word: string) => {
    if (!puzzle) return false
    
    setError(null)
    setIsLoading(true)
    
    try {
      const result = await api.validateWord(word, chain, puzzle.start_word)
      
      if (result.valid) {
        setChain([...chain, word])
        // Reset hints when a new word is added
        setHint(null)
        setHintsUsed(0)
        return true
      } else {
        setError(result.error || 'Invalid word')
        return false
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to validate word'
      setError(errorMessage)
      return false
    } finally {
      setIsLoading(false)
    }
  }, [puzzle, chain])

  // Remove word from chain
  const handleRemoveWord = useCallback((index: number) => {
    setChain(chain.filter((_, i) => i !== index))
    setError(null)
  }, [chain])

  // Submit chain
  const handleSubmit = useCallback(async () => {
    if (!puzzle || chain.length === 0) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const fullPath = [puzzle.start_word, ...chain, puzzle.end_word]
      const result = await api.submitChain(fullPath, puzzle.start_word, puzzle.end_word)
      
      // Prepare result data for Results component
      // API returns playerSteps = len(path) - 1 (number of steps/connections)
      // player_path should be just the chain words (not including start/end)
      // player_length should be the number of steps
      setResultData({
        start_word: puzzle.start_word,
        end_word: puzzle.end_word,
        player_path: chain,
        optimal_path: result.algorithmPath || [],
        player_length: result.playerSteps || chain.length,
        optimal_length: result.algorithmSteps || 0,
        score: result.score || 0,
        valid: result.valid !== undefined ? result.valid : (result.score > 0),
      })
      
      setShowResults(true)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit chain'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [puzzle, chain])

  // Get hint
  const handleGetHint = useCallback(async () => {
    if (!puzzle) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const hintLevel = hintsUsed + 1
      const result = await api.getHint(puzzle.start_word, puzzle.end_word, chain, hintLevel)
      
      if (result.success && result.hint) {
        const hintData: Hint = {
          hint: result.hint.message,
          hint_level: result.hint.hint_level || hintLevel,
          word: result.hint.word,
          masked_word: result.hint.masked_word,
          word_length: result.hint.word_length,
          fully_revealed: result.hint.fully_revealed || false,
          steps_remaining: result.hint.optimalPathLength - chain.length,
        }
        
        setHint(hintData)
        setHintsUsed(hintLevel)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get hint'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }, [puzzle, chain, hintsUsed])

  // Clear hint
  const handleClearHint = useCallback(() => {
    setHint(null)
  }, [])

  // Handle new game
  const handleNewGame = useCallback(() => {
    loadNewGame()
  }, [loadNewGame])

  return (
    <div className={styles.app}>
      {started ? (
        <>
          <header className={styles.header}>
            <div className={styles.inner}>
              <button 
                className={styles.iconBtn} 
                onClick={() => setShowHowToPlay(true)}
                aria-label="How to Play"
              >
                ?
              </button>
              <button 
                className={styles.iconBtn} 
                onClick={handleNewGame}
                aria-label="New game"
                disabled={isLoading}
              >
                ↻
              </button>
            </div>
          </header>

          <main className={styles.main}>
            {showResults && resultData ? (
              <Results
                result={resultData}
                onPlayAgain={loadNewGame}
              />
            ) : (
              <Game
                puzzle={puzzle}
                chain={chain}
                error={error}
                isLoading={isLoading}
                hint={hint}
                hintsUsed={hintsUsed}
                onAddWord={handleAddWord}
                onRemoveWord={handleRemoveWord}
                onSubmit={handleSubmit}
                onGetHint={handleGetHint}
                onClearHint={handleClearHint}
              />
            )}
          </main>

          <footer className={styles.footer}>
            <span className={styles.footerText}>
              connect two words in 6 steps or less
            </span>
            <div className={styles.footerMeta}>
              <span className={styles.copyright}>© 2026</span>
              <a 
                href="https://github.com/apun16/6-Degrees" 
                target="_blank" 
                rel="noopener noreferrer"
                className={styles.githubLink}
                aria-label="View source code on GitHub"
              >
                <GitHubIcon size={18} />
              </a>
            </div>
          </footer>

          {showHowToPlay && (
            <div className={styles.modalOverlay} onClick={() => setShowHowToPlay(false)}>
              <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
                <HowToPlay onClose={() => setShowHowToPlay(false)} />
              </div>
            </div>
          )}
        </>
      ) : (
        <Landing onPlay={() => setStarted(true)} />
      )}
    </div>
  )
}