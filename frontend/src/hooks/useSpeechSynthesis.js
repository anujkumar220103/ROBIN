// useSpeechSynthesis — wraps the browser-native Web Speech Synthesis API.
// Strips Markdown formatting before speaking so users hear clean prose.
// Prevents overlapping utterances; exposes a per-message speaking state.

import { useCallback, useEffect, useRef, useState } from 'react'

// ── Browser capability check ─────────────────────────────────────────────────
export const isSpeechSynthesisSupported =
  typeof window !== 'undefined' && Boolean(window.speechSynthesis)

// ── Markdown → plain text ────────────────────────────────────────────────────
// Strips common Markdown so the synthesizer reads clean prose.
export function stripMarkdown(text) {
  if (!text) return ''
  return text
    // Fenced code blocks → remove entirely (not useful when spoken)
    .replace(/```[\s\S]*?```/g, 'code block.')
    // Inline code
    .replace(/`[^`]+`/g, (m) => m.slice(1, -1))
    // Headings
    .replace(/^#{1,6}\s+/gm, '')
    // Bold / italic
    .replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1')
    .replace(/_{1,3}([^_]+)_{1,3}/g, '$1')
    // Links — keep the label
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    // Images — drop
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    // Citation markers like [1], [2]
    .replace(/\[\d+\]/g, '')
    // Blockquotes
    .replace(/^>\s+/gm, '')
    // Horizontal rules
    .replace(/^[-*_]{3,}\s*$/gm, '')
    // List bullets / numbered items
    .replace(/^[\s]*[-*+]\s+/gm, '')
    .replace(/^[\s]*\d+\.\s+/gm, '')
    // Extra whitespace
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

// ── Voice selection ──────────────────────────────────────────────────────────
// Preference order for each language prefix.
const VOICE_PRIORITY = {
  'hi': ['Google हिन्दी', 'Microsoft Swara', 'hi-IN', 'hi'],
  'en': ['Google UK English Female', 'Google US English', 'Microsoft Zira', 'en-IN', 'en-GB', 'en-US', 'en'],
}

function pickVoice(lang) {
  if (!isSpeechSynthesisSupported) return null
  const voices = window.speechSynthesis.getVoices()
  if (!voices.length) return null

  const prefix = lang.split('-')[0].toLowerCase()
  const priorities = VOICE_PRIORITY[prefix] || []

  // 1. Exact name match
  for (const name of priorities) {
    const v = voices.find((v) => v.name === name)
    if (v) return v
  }
  // 2. Name contains the priority string (case-insensitive)
  for (const name of priorities) {
    const v = voices.find((v) => v.name.toLowerCase().includes(name.toLowerCase()))
    if (v) return v
  }
  // 3. Any voice whose lang starts with the right prefix
  const v = voices.find((v) => v.lang.toLowerCase().startsWith(prefix))
  if (v) return v

  // 4. First available voice (last resort)
  return voices[0] || null
}

/**
 * @returns {{
 *   speakingId: string|null,
 *   speak: (text: string, id: string, lang?: string) => void,
 *   stop: () => void,
 *   isSupported: boolean,
 * }}
 */
export default function useSpeechSynthesis() {
  // null when nothing is playing; a message id when actively speaking.
  const [speakingId, setSpeakingId] = useState(null)
  const utteranceRef = useRef(null)
  // Voices load asynchronously in some browsers — track readiness.
  const [voicesReady, setVoicesReady] = useState(false)

  useEffect(() => {
    if (!isSpeechSynthesisSupported) return
    const synth = window.speechSynthesis

    function handleVoicesChanged() {
      if (synth.getVoices().length > 0) setVoicesReady(true)
    }

    // Voices may already be loaded (Firefox loads synchronously).
    if (synth.getVoices().length > 0) setVoicesReady(true)
    synth.addEventListener('voiceschanged', handleVoicesChanged)

    return () => {
      synth.removeEventListener('voiceschanged', handleVoicesChanged)
      synth.cancel()
    }
  }, [])

  const stop = useCallback(() => {
    if (!isSpeechSynthesisSupported) return
    window.speechSynthesis.cancel()
    setSpeakingId(null)
    utteranceRef.current = null
  }, [])

  const speak = useCallback((text, id, lang = 'en-IN') => {
    if (!isSpeechSynthesisSupported) return
    const synth = window.speechSynthesis

    // If the same message is already playing, treat the button as a stop.
    if (speakingId === id) {
      stop()
      return
    }

    // Cancel any in-progress speech first.
    synth.cancel()

    const clean = stripMarkdown(text)
    if (!clean) return

    const utterance = new SpeechSynthesisUtterance(clean)
    utterance.lang = lang
    utterance.rate = 1.0
    utterance.pitch = 1.0
    utterance.volume = 1.0

    // Assign voice — wait for voices if they haven't loaded yet.
    const assignVoice = () => {
      const voice = pickVoice(lang)
      if (voice) utterance.voice = voice
    }

    if (voicesReady) {
      assignVoice()
    } else {
      // Fallback: try again just before speaking (browser may have loaded by then).
      const once = () => {
        assignVoice()
        synth.removeEventListener('voiceschanged', once)
      }
      synth.addEventListener('voiceschanged', once)
    }

    utterance.onstart = () => setSpeakingId(id)
    utterance.onend = () => {
      setSpeakingId(null)
      utteranceRef.current = null
    }
    utterance.onerror = () => {
      setSpeakingId(null)
      utteranceRef.current = null
    }

    utteranceRef.current = utterance
    synth.speak(utterance)
  }, [speakingId, stop, voicesReady])

  return { speakingId, speak, stop, isSupported: isSpeechSynthesisSupported }
}
