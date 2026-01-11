import styles from './howtoplay.module.css'

// fix rules
function HowToPlay({ onClose }) {
  return (
    <div className={styles.howToPlay}>
      <h2 className={styles.title}>how to play</h2>
      
      <div className={styles.content}>
        <p className={styles.intro}>
          Connect two words by building a chain of associations.
          Each word must be semantically related (ex: synonyms, similar themes, etc) to the previous one.
        </p>

        <div className={styles.example}>
          <div className={styles.exampleTitle}>example</div>
          <div className={styles.chain}>
            <span className={styles.word}>ocean</span>
            <span className={styles.connector}>→</span>
            <span className={styles.word}>wave</span>
            <span className={styles.connector}>→</span>
            <span className={styles.word}>sound</span>
            <span className={styles.connector}>→</span>
            <span className={styles.word}>music</span>
            <span className={styles.connector}>→</span>
            <span className={styles.word}>piano</span>
            <span className={styles.connector}>→</span>
            <span className={styles.word}>key</span>
            <span className={styles.connector}>→</span>
            <span className={styles.word}>keyboard</span>
          </div>
        </div>

        <div className={styles.rules}>
          <h3 className={styles.rulesTitle}>rules</h3>
          <ul className={styles.rulesList}>
            <li>Maximum of <strong>6 steps</strong> between words</li>
            <li>Each word must exist in our database</li>
            <li>Each word must connect to the previous</li>
            <li>No repeated words</li>
          </ul>
        </div>

        <div className={styles.scoring}>
          <h3 className={styles.scoringTitle}>scoring</h3>
          <div className={styles.scoreTable}>
            <div className={styles.scoreRow}>
              <span>🤖 Beat the algorithm</span>
              <span className={styles.points}>120</span>
            </div>
            <div className={styles.scoreRow}>
              <span>🎯 Perfect path</span>
              <span className={styles.points}>100</span>
            </div>
            <div className={styles.scoreRow}>
              <span>+1 extra step</span>
              <span className={styles.points}>90</span>
            </div>
            <div className={styles.scoreRow}>
              <span>+2 extra steps</span>
              <span className={styles.points}>80</span>
            </div>
            <div className={styles.scoreRow}>
              <span>+3 extra steps</span>
              <span className={styles.points}>60</span>
            </div>
            <div className={styles.scoreRow}>
              <span>Completed (longer)</span>
              <span className={styles.points}>50</span>
            </div>
          </div>
          <p className={styles.tip}>
            💡 Find a shorter path than the algorithm to score 120!
          </p>
        </div>
      </div>

      <button className="btn btn--primary" onClick={onClose}>
        got it
      </button>
    </div>
  )
}

export default HowToPlay