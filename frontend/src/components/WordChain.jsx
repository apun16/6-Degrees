import styles from './wordchain.module.css'

function WordChain({ startWord, endWord, chain, onRemoveWord }) {
  const allWords = [startWord, ...chain]
  
  return (
    <div className={styles.chain}>
      {chain.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.step}>
            <div className={`${styles.word} ${styles.startWord}`}>
              {startWord.toUpperCase()}
            </div>
          </div>
          <div className={styles.emptyChain}>
            <div className={styles.emptyCircle}></div>
            <div className={styles.emptyLine}></div>
            <div className={styles.emptyCircle}></div>
            <div className={styles.emptyLine}></div>
            <div className={styles.emptyCircle}></div>
          </div>
          <span className={styles.emptyText}>your chain will appear here</span>
          <span className={styles.emptyHint}>type a word to begin</span>
        </div>
      ) : (
        <>
          {allWords.map((word, index) => {
            const isChainWord = index > 0
            const chainIndex = index - 1 // Index in chain array (not including start word)
            const isLastWord = index === allWords.length - 1
            
            return (
              <div key={`${word}-${index}`} className={styles.step}>
                <div 
                  className={`${styles.word} ${index === 0 ? styles.startWord : styles.chainWord}`}
                  onClick={isChainWord && isLastWord && onRemoveWord ? () => onRemoveWord(chainIndex) : undefined}
                  role={isChainWord && isLastWord ? 'button' : undefined}
                  tabIndex={isChainWord && isLastWord ? 0 : undefined}
                  title={isChainWord && isLastWord ? 'Click to remove' : undefined}
                >
                  {word.toUpperCase()}
                  {isChainWord && isLastWord && (
                    <span 
                      className={styles.removeHint}
                      onClick={(e) => {
                        e.stopPropagation()
                        if (onRemoveWord) onRemoveWord(chainIndex)
                      }}
                    >×</span>
                  )}
                </div>
              
                {index < allWords.length - 1 && (
                  <div className={styles.connector}>
                    <div className={styles.line} />
                    <span className={styles.stepNumber}>{index + 1}</span>
                  </div>
                )}
              </div>
            )
          })}          
          <div className={styles.step}>
            <div className={styles.connector}>
              <div className={styles.lineDashed} />
              <span className={styles.stepNumber}>?</span>
            </div>
          </div>
          <div className={styles.step}>
            <div className={`${styles.word} ${styles.targetWord}`}>
              {endWord.toUpperCase()}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default WordChain