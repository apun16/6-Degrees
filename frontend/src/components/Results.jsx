import { useState } from 'react'
import styles from './results.module.css'

function Results({ result, onPlayAgain }) {
  const [copied, setCopied] = useState(false)
  const [sharing, setSharing] = useState(false)
  
  const {
    start_word,
    end_word,
    player_path,
    optimal_path,
    player_length,
    optimal_length,
    score,
    valid,
  } = result

  // Use valid flag from backend - path is valid only if semantically connected
  const isValid = valid === true
  const beatAlgorithm = isValid && player_length < optimal_length
  const hasPartialCredit = !isValid && score > 0

  // calculate how many words were connected correctly (for partial credit on broken paths)
  const getConnectedCount = () => {
    if (isValid) return player_length
    // for broken paths, count how many steps matched with optimal path
    const fullPath = [start_word, ...player_path, end_word]
    let connected = 0
    for (let i = 0; i < fullPath.length - 1; i++) {
      // check if this word appears in optimal path in sequence
      const optIdx = optimal_path.indexOf(fullPath[i])
      const nextOptIdx = optimal_path.indexOf(fullPath[i + 1])
      if (optIdx !== -1 && nextOptIdx !== -1 && nextOptIdx === optIdx + 1) {
        connected++
      }
    }
    return connected
  }

  const connectedCount = getConnectedCount()

  const getScoreLabel = () => {
    if (!isValid && hasPartialCredit) return 'PARTIAL CREDIT'
    if (!isValid) return 'PATH NOT CONNECTED'
    if (score >= 110) return 'YOU BEAT THE ALGORITHM!'
    if (score === 100) return 'PERFECT'
    if (score >= 90) return 'EXCELLENT'
    if (score >= 80) return 'GREAT'
    if (score >= 70) return 'GOOD'
    if (score >= 60) return 'NICE'
    if (score >= 50) return 'COMPLETED'
    return 'TRY AGAIN'
  }

  const getScoreEmoji = () => {
    if (!isValid) return '🔗'
    if (score >= 110) return '🤖💥'
    if (score === 100) return '🎯'
    if (score >= 90) return '⭐'
    if (score >= 80) return '✓'
    if (score >= 70) return '✓'
    if (score >= 60) return '✓'
    if (score >= 50) return '🔗'
    return '🔗'
  }

  const getScoreColor = () => {
    if (!isValid && hasPartialCredit) return '#fbbf24' // Yellow for partial
    if (!isValid) return 'var(--text-muted)'
    if (score >= 110) return '#ff6b6b'
    if (score >= 90) return 'var(--success)'
    if (score >= 70) return 'var(--accent)'
    if (score >= 50) return 'var(--text-primary)'
    return 'var(--text-muted)'
  }

  // check if native share is available (mobile devices)
  const canShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function'

  const handleShare = async () => {
    setSharing(true)
    const shareText = generateShareText()
    const fullShareText = shareText + '\n\nPlay: https://play6degrees.com'
    
    try {
      // try native share (Messages, Notes, etc.)
      if (canShare) {
        await navigator.share({ 
          text: fullShareText
        })
        setSharing(false)
        return
      }
      
      // desktop: copy to clipboard
      await navigator.clipboard.writeText(fullShareText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      // user cancelled share or error - try clipboard
      if (err.name !== 'AbortError') {
        try {
          await navigator.clipboard.writeText(fullShareText)
          setCopied(true)
          setTimeout(() => setCopied(false), 2000)
        } catch {
          console.error('Share failed:', err)
        }
      }
    }
    
    setSharing(false)
  }

  const generateShareText = () => {
    // status line with emoji
    let statusLine = ''
    let chainVisual = ''
    
    if (!isValid) {
      // for broken paths, show partial credit
      const linksConnected = Math.floor(score / 10)
      if (linksConnected > 0) {
        statusLine = `🔗 ${linksConnected} link${linksConnected > 1 ? 's' : ''} connected (+${score} pts)`
        // show green for connected, red for broken
        for (let i = 0; i < linksConnected; i++) chainVisual += '🟩'
        chainVisual += '🟥'
      } else {
        statusLine = '❌ No connections'
      }
    } else {
      // build the visual grid for valid paths
      const maxSteps = 6
      for (let i = 0; i < maxSteps; i++) {
        if (i < player_length) {
          if (beatAlgorithm) {
            chainVisual += '🟪' 
          } else if (player_length === optimal_length) {
            chainVisual += '🟩' 
          } else if (i < optimal_length) {
            chainVisual += '🟨' 
          } else {
            chainVisual += '🟧'
          }
        } else {
          chainVisual += '⬜'
        }
      }
      
      if (beatAlgorithm) {
        statusLine = `🤖💥 Beat the algorithm!`
      } else if (player_length === optimal_length) {
        statusLine = '🎯 Perfect!'
      } else {
        statusLine = `📊 ${player_length}/${optimal_length} steps`
      }
    }    
    return `6° DEGREES

${start_word} → ${end_word}
${chainVisual}

${statusLine}
Score: ${score}`
  }

  const getMessage = () => {
    // First check if path is valid - if not, show error message
    if (!isValid) {
      return "Your chain didn't connect the words. One or more words weren't linked."
    }
    // Only show comparison messages if path is valid
    if (beatAlgorithm) {
      const diff = optimal_length - player_length
      return `You found a path ${diff} step${diff > 1 ? 's' : ''} shorter than the algorithm!`
    }
    if (player_length === optimal_length) {
      return "You matched the optimal path."
    }
    const diff = player_length - optimal_length
    return `${diff} step${diff > 1 ? 's' : ''} longer than optimal.`
  }

  // generate visual chain squares
  const getChainSquares = () => {
    const maxSteps = 6
    const squares = []
    
    for (let i = 0; i < maxSteps; i++) {
      let colorClass = styles.squareEmpty
      if (i < player_length) {
        if (!isValid) {
          colorClass = styles.squareRed
        } else if (beatAlgorithm) {
          colorClass = styles.squarePurple
        } else if (player_length === optimal_length) {
          colorClass = styles.squareGreen
        } else if (i < optimal_length) {
          colorClass = styles.squareYellow
        } else {
          colorClass = styles.squareOrange
        }
      }
      squares.push(<div key={i} className={`${styles.square} ${colorClass}`} />)
    }
    return squares
  }

  return (
    <div className={styles.results}>
      <div className={styles.scoreSection}>
        <div className={styles.scoreEmoji}>{getScoreEmoji()}</div>
        <div 
          className={styles.score}
          style={{ color: getScoreColor() }}
        >
          {score}
        </div>
        <div className={styles.scoreLabel}>{getScoreLabel()}</div>
      </div>
      {isValid && (
        <div className={styles.chainVisual}>
          {getChainSquares()}
        </div>
      )}      
      {hasPartialCredit && (
        <div className={styles.partialCredit}>
          <span className={styles.partialCreditText}>
            {Math.floor(score / 10)} link{Math.floor(score / 10) > 1 ? 's' : ''} connected (+{score} pts)
          </span>
        </div>
      )}
      <div className={styles.puzzle}>
        <span className={styles.word}>{start_word}</span>
        <span className={styles.arrow}>→</span>
        <span className={styles.word}>{end_word}</span>
      </div>
      <p className={styles.message}>{getMessage()}</p>
      <div className={styles.comparison}>
        <div className={`${styles.pathSection} ${!isValid ? styles.invalidPath : ''}`}>
          <h3 className={styles.pathTitle}>your path {!isValid && '(broken)'}</h3>
          <div className={styles.path}>
            <span className={styles.pathWord}>{start_word}</span>
            {player_path.map((word, i) => (
              <span key={i} className={styles.pathWord}>{word}</span>
            ))}
            <span className={styles.pathWord}>{end_word}</span>
          </div>
          <div className={styles.pathLength}>
            {player_path.length + 1} step{player_path.length !== 0 ? 's' : ''}
          </div>
        </div>

        <div className={styles.pathSection}>
          <h3 className={styles.pathTitle}>working path</h3>
          {optimal_path && optimal_path.length > 0 ? (
            <>
              <div className={`${styles.path} ${styles.optimalPath}`}>
                {optimal_path.map((word, i) => (
                  <span key={i} className={styles.pathWord}>{word}</span>
                ))}
              </div>
              <div className={styles.pathLength}>
                {optimal_length > 0 ? `${optimal_length} step${optimal_length !== 1 ? 's' : ''}` : 'No path found'}
              </div>
            </>
          ) : (
            <div className={styles.pathLength}>
              No path found
            </div>
          )}
        </div>
      </div>
      <div className={styles.actions}>
        <button 
          className={`btn ${styles.shareBtn} ${copied ? styles.copied : ''}`} 
          onClick={handleShare}
          disabled={sharing}
        >
          {sharing ? '...' : copied ? '✓ copied!' : canShare ? '📤 share' : '📋 copy'}
        </button>
        <button className="btn btn--primary" onClick={onPlayAgain}>
          play again
        </button>
      </div>
    </div>
  )
}

export default Results
