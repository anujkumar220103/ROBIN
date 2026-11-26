// Tailwind CSS configuration — scans JSX files for class names.

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ROBIN AI design tokens
        background: '#F8FAFC',
        surface: '#FFFFFF',
        'primary-text': '#0F172A',
        'secondary-text': '#64748B',
        accent: '#2563EB',
        'accent-hover': '#1D4ED8',
        border: '#E2E8F0',
        success: '#16A34A',
        error: '#DC2626',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
