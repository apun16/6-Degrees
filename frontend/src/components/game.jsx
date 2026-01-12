'use client'

import { useState, useCallback } from 'react'
import WordChain from './WordChain'
import WordInput from './WordInput'
import styles from '../styles/game.module.css'

function Game({ 
  puzzle, 
  chain, 
  error, 
  isLoading,
  hint,
  hintsUsed,
  onAddWord, 
  onRemoveWord, 
  onSubmit,
  onGetHint,
  onClearHint,
}) {
  const [inputValue, setInputValue] = useState('')

  const handleSubmitWord = useCallback(async (e) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return
    
    const success = await onAddWord(inputValue)
    if (success) {
      setInputValue('')
    }
  }, [inputValue, isLoading, onAddWord])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Backspace' && inputValue === '' && chain.length > 0) {
      onRemoveWord(chain.length - 1)
    }
  }, [inputValue, chain.length, onRemoveWord])

  if (!puzzle) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadingSpinner} />
        <span className={styles.loadingText}>finding puzzle</span>
      </div>
    )
  }

  const canSubmit = chain.length > 0
  const stepsUsed = chain.length
  const stepsRemaining = 6 - stepsUsed
  const progressPercent = (stepsUsed / 6) * 100

  return (
    <div className={styles.game}>
      <div className={styles.puzzleHeader}>
        <p className={styles.puzzleTitle}>connect these words</p>
        <p className={styles.optimalHint}>
          optimal path: <strong>{puzzle.optimal_length} steps</strong>
        </p>
      </div>

      <div className={styles.puzzle}>
        <div className={styles.wordBox}>
          <div className={styles.wordLabel}>start</div>
          <div className={styles.wordText}>{puzzle.start_word.toUpperCase()}</div>
        </div>
        
        <div className={styles.puzzleConnector}>
          <div className={styles.connectorLine} />
          <span className={styles.connectorSteps}>6 max</span>
        </div>
        
        <div className={styles.wordBox}>
          <div className={styles.wordLabel}>goal</div>
          <div className={styles.wordText}>{puzzle.end_word.toUpperCase()}</div>
        </div>
      </div>

      <div className={styles.progress}>
        <div className={styles.progressBar}>
          <div 
            className={`${styles.progressFill} ${stepsRemaining <= 1 ? styles.warning : ''}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className={styles.progressText}>
          <span>{stepsUsed} OF 6 STEPS USED</span>
          <span className={`${styles.progressSteps} ${stepsRemaining <= 1 ? styles.warning : ''}`}>
            {stepsRemaining} REMAINING
          </span>
        </div>
      </div>

      <WordChain 
        startWord={puzzle.start_word}
        endWord={puzzle.end_word}
        chain={chain}
        onRemoveWord={onRemoveWord}
      />

      <div className={styles.inputSection}>
        <form onSubmit={handleSubmitWord} className={styles.form}>
          <WordInput
            value={inputValue}
            onChange={setInputValue}
            onKeyDown={handleKeyDown}
            placeholder="add next word..."
            disabled={isLoading || stepsRemaining <= 0}
            error={error}
          />
          
          <button 
            type="submit" 
            className={styles.addBtn}
            disabled={isLoading || !inputValue.trim()}
          >
            add →
          </button>
        </form>

        {error && (
          <div className={styles.error}>
            <span className={styles.errorIcon}>!</span>
            <span>{error}</span>
          </div>
        )}
      </div>

      {hint && (
        <div className={styles.hintBox}>
          <div className={styles.hintHeader}>
            <span className={styles.hintIcon}>💡</span>
            <span className={styles.hintTitle}>hint #{hint.hint_level || 1}</span>
            <button 
              className={styles.hintClose} 
              onClick={onClearHint}
              aria-label="Close hint"
            >
              ×
            </button>
          </div>
          
          <p className={styles.hintText}>{hint.hint}</p>
          
          {/* Progressive letter reveal */}
          {hint.masked_word && (
            <div className={styles.maskedWord}>
              {hint.masked_word.split('').map((char, i) => (
                <span 
                  key={i} 
                  className={`${styles.letter} ${char === '_' ? styles.hiddenLetter : styles.revealedLetter}`}
                >
                  {char}
                </span>
              ))}
            </div>
          )}
          
          {hint.word_length && !hint.fully_revealed && (
            <p className={styles.hintMeta}>
              {hint.word_length} letters • tap hint again for more
            </p>
          )}
          
          {hint.fully_revealed && (
            <p className={styles.hintRevealed}>
              ✓ word revealed!
            </p>
          )}
          
          {hint.steps_remaining && (
            <p className={styles.hintSteps}>
              {hint.steps_remaining} step{hint.steps_remaining !== 1 ? 's' : ''} to target
            </p>
          )}
        </div>
      )}

      <div className={styles.actions}>
        <button
          className={styles.hintBtn}
          onClick={onGetHint}
          disabled={isLoading}
        >
          <span>💡</span>
          <span>HINT</span>
        </button>
        
        <button
          className={styles.submitBtn}
          onClick={onSubmit}
          disabled={!canSubmit || isLoading}
        >
          SUBMIT CHAIN
        </button>
      </div>
    </div>
  )
}

export default Game