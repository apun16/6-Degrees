'use client'

import { useState } from 'react'
import Landing from '../components/landing'
import styles from '../components/page.module.css'

export default function Page() {
  const [started, setStarted] = useState(false)

  return (
    <div className={styles.app}>
      {started ? (
        <main className={styles.main}>
          {/* game content will go here */}
        </main>
      ) : (
        <Landing onPlay={() => setStarted(true)} />
      )}
    </div>
  )
}