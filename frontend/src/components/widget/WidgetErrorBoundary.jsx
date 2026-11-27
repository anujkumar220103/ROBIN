// React Error Boundary for the embedded public chatbot widget.
// Catches render-time exceptions so a crash does not produce a blank iframe;
// instead it shows a small, recoverable error card.

import { Component } from 'react'

export default class WidgetErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { crashed: false, errorMessage: '' }
    this.handleRetry = this.handleRetry.bind(this)
  }

  static getDerivedStateFromError(error) {
    return {
      crashed: true,
      errorMessage: error?.message || 'An unexpected error occurred.',
    }
  }

  componentDidCatch(error, info) {
    // Log to the browser console so developers can see the original stack.
    console.error('[ROBIN widget] Uncaught error:', error, info?.componentStack)
  }

  handleRetry() {
    this.setState({ crashed: false, errorMessage: '' })
  }

  render() {
    if (this.state.crashed) {
      return (
        <div className="flex h-screen flex-col items-center justify-center gap-4 bg-white p-6 text-center">
          <p className="text-sm font-semibold text-gray-800">Something went wrong</p>
          <p className="text-xs text-gray-500 max-w-xs">
            The chatbot encountered an unexpected error. Please try again.
          </p>
          <button
            onClick={this.handleRetry}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 active:scale-95 transition"
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
