'use client'

import { useState, useEffect } from 'react'
import styles from './landing.module.css'

const SAMPLE_CHAINS = [
  'HEART → LOVE → FAMILY → HOME → HOUSE',
  'STAR → NIGHT → MOON → TIDE → OCEAN',
  'FIRE → HEAT → SUN → STAR → SPACE',
  'MUSIC → SONG → ROOSTER → BIRD → FLY',
  'OCEAN → WAVE → BEACH → SAND → SANDAL',
  'ART → CANVAS → PAINTING → AUCTION → BID',
];

function Landing({ onPlay }) {
  const [isVisible, setIsVisible] = useState(false)
  const [chainIndex, setChainIndex] = useState(0)
  const [isFading, setIsFading] = useState(false)
  
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 100)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      setIsFading(true)
      setTimeout(() => {
        setChainIndex(prev => (prev + 1) % SAMPLE_CHAINS.length)
        setIsFading(false)
      }, 300)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className={`${styles.landing} ${isVisible ? styles.visible : ''}`}>
      <div className={styles.content}>
        <div className={styles.logo}>
          <span className={styles.six}>6</span>
          <span className={styles.degree}>°</span>
        </div>
        
        <h1 className={styles.title}>degrees</h1>
        
        <p className={styles.tagline}>
          connect any two words in six steps
        </p>
        
        <p className={styles.description}>
          every word links to another. find the path.
        </p>

        <button className={styles.playBtn} onClick={onPlay}>
          <span className={styles.playText}>play</span>
          <span className={styles.playArrow}>→</span>
        </button>
        
        <div className={styles.hint}>
          <span className={styles.hintIcon}>○</span>
          <span className={`${styles.hintText} ${isFading ? styles.fading : ''}`}>
            {SAMPLE_CHAINS[chainIndex]}
          </span>
          <span className={styles.hintIcon}>○</span>
        </div>
      </div>
    </div>
  )
}

export default Landing