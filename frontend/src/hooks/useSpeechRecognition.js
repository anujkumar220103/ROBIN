// useSpeechRecognition — wraps the browser-native Web Speech API (SpeechRecognition).
// No external services are used beyond what the browser vendor routes internally
// (e.g. Chrome sends audio to Google for recognition; this is handled by the browser,
// not by ROBIN AI).  Users are informed of this via the UI.

import { useCallback, useEffect, useRef, useState } from 'react'

// ── Browser capability check ─────────────────────────────────────────────────
const SpeechRecognitionAPI =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null

export const isSpeechRecognitionSupported = Boolean(SpeechRecognitionAPI)

// ── Permissions Policy check ─────────────────────────────────────────────────
// Returns true when the document's effective Permissions-Policy allows
// microphone access.  Uses featurePolicy (Chrome/Edge) with a fallback that
// assumes allowed when the API is unavailable (Firefox, Safari).
function isMicrophoneAllowedByPolicy() {
  try {
    // featurePolicy is available in Chrome/Edge.
    if (typeof document !== 'undefined' && document.featurePolicy) {
      return document.featurePolicy.allowsFeature('microphone')
    }
    // permissionsPolicy is the newer spec name (not yet widely implemented).
    if (typeof document !== 'undefined' && document.permissionsPolicy) {
      return document.permissionsPolicy.allowsFeature('microphone')
    }
  } catch {
    // Any access error → assume allowed; the browser will gate it properly.
  }
  return true
}

/**
 * @param {object}   opts
 * @param {string}   opts.lang         BCP-47 language tag, e.g. 'en-IN' or 'hi-IN'
 * @param {function} opts.onResult     Called with the final transcript string
 * @param {function} [opts.onInterim]  Called with live interim transcript (optional)
 */
export default function useSpeechRecognition({ lang = 'en-IN', onResult, onInterim } = {}) {
  const [listening, setListening] = useState(false)
  const [error, setError] = useState(null) // null | string
  const recognitionRef = useRef(null)
  // Keep stable refs to callbacks so the recognition event handlers always
  // call the latest version without needing to re-instantiate.
  const onResultRef = useRef(onResult)
  const onInterimRef = useRef(onInterim)
  useEffect(() => { onResultRef.current = onResult }, [onResult])
  useEffect(() => { onInterimRef.current = onInterim }, [onInterim])

  // Build (or rebuild) the recognition instance whenever the language changes.
  useEffect(() => {
    if (!SpeechRecognitionAPI) return

    const rec = new SpeechRecognitionAPI()
    rec.lang = lang
    rec.continuous = false       // single utterance per press
    rec.interimResults = true    // show partial results while speaking
    rec.maxAlternatives = 1

    rec.onstart = () => {
      setListening(true)
      setError(null)
    }

    rec.onend = () => {
      setListening(false)
    }

    rec.onerror = (event) => {
      setListening(false)
      switch (event.error) {
        case 'not-allowed':
        case 'permission-denied':
          // Distinguish between a Permissions-Policy block (server config) and
          // a user-initiated browser permission denial — they produce the same
          // error code but require different remediation steps.
          if (!isMicrophoneAllowedByPolicy()) {
            setError(
              'Microphone access is blocked by this page\'s security policy. ' +
              'Please contact the site administrator.'
            )
          } else {
            setError(
              'Microphone permission was denied. ' +
              'Click the camera/microphone icon in your browser\'s address bar and allow access, then try again.'
            )
          }
          break
        case 'no-speech':
          setError('No speech was detected. Please try again.')
          break
        case 'audio-capture':
          setError('No microphone was found. Please connect a microphone and try again.')
          break
        case 'network':
          setError('A network error occurred during speech recognition. Please check your connection.')
          break
        case 'aborted':
          // User stopped listening — not an error worth showing.
          setError(null)
          break
        case 'service-not-allowed':
          setError(
            'Speech recognition is not available on this page. ' +
            'Ensure the page is served over HTTPS.'
          )
          break
        default:
          setError(`Speech recognition error: ${event.error}`)
      }
    }

    rec.onresult = (event) => {
      let interimTranscript = ''
      let finalTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }
      if (interimTranscript && onInterimRef.current) {
        onInterimRef.current(interimTranscript)
      }
      if (finalTranscript && onResultRef.current) {
        onResultRef.current(finalTranscript)
      }
    }

    recognitionRef.current = rec

    return () => {
      try { rec.abort() } catch { /* already stopped */ }
      recognitionRef.current = null
    }
  }, [lang])

  const startListening = useCallback(() => {
    if (!SpeechRecognitionAPI) {
      setError('Speech recognition is not supported in this browser. Please use Chrome or Edge.')
      return
    }
    // Check the Permissions Policy before attempting to start — this gives a
    // clearer error immediately instead of waiting for onerror to fire.
    if (!isMicrophoneAllowedByPolicy()) {
      setError(
        'Microphone access is blocked by this page\'s security policy. ' +
        'Please contact the site administrator.'
      )
      return
    }
    if (!recognitionRef.current) return
    setError(null)
    try {
      recognitionRef.current.start()
    } catch {
      // If recognition is already started (can happen with rapid clicks) ignore.
    }
  }, [])

  const stopListening = useCallback(() => {
    try { recognitionRef.current?.stop() } catch { /* already stopped */ }
  }, [])

  // Abort immediately (used when TTS starts or component unmounts).
  const abortListening = useCallback(() => {
    try { recognitionRef.current?.abort() } catch { /* already stopped */ }
    setListening(false)
  }, [])

  return { listening, error, startListening, stopListening, abortListening, isSupported: isSpeechRecognitionSupported }
}
