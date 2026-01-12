import { useRef, useEffect } from 'react'
import styles from './wordinput.module.css'

function WordInput({ 
  value, 
  onChange, 
  onKeyDown, 
  placeholder, 
  disabled, 
  error 
}) {
  const inputRef = useRef(null)

  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus()
    }
  }, [disabled])

  const handleChange = (e) => {
    // convert to uppercase for display
    onChange(e.target.value.toUpperCase())
  }

  return (
    <input
      ref={inputRef}
      type="text"
      value={value}
      onChange={handleChange}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      className={`${styles.input} ${error ? styles.inputError : ''}`}
      autoComplete="off"
      autoCorrect="off"
      autoCapitalize="characters"
      spellCheck="false"
    />
  )
}

export default WordInput