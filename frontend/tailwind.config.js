/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./frontend/index.html",
    "./frontend/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F7F8F6',
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#F1F3F0',
          hover: '#E8ECE6',
        },
        foreground: {
          DEFAULT: '#17211F',
          secondary: '#64716D',
          muted: '#8D9B97',
        },
        primary: {
          DEFAULT: '#245C52',
          hover: '#19483F',
          soft: '#EAF2EF',
          light: '#377E71',
          dark: '#12352E',
        },
        border: {
          DEFAULT: '#E4E8E4',
          subtle: '#EDF0ED',
          strong: '#D0D6D0',
        },
        status: {
          success: '#277451',
          'success-soft': '#EBF5EF',
          warning: '#A36B25',
          'warning-soft': '#FDF6E9',
          danger: '#B44848',
          'danger-soft': '#FBEFEF',
          info: '#2C5D88',
          'info-soft': '#EEF4FA',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          '"Liberation Mono"',
          '"Courier New"',
          'monospace',
        ],
      },
      borderRadius: {
        card: '12px',
        control: '8px',
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(23, 33, 31, 0.05)',
        card: '0 1px 3px 0 rgba(23, 33, 31, 0.04), 0 1px 2px -1px rgba(23, 33, 31, 0.04)',
        elevated: '0 4px 6px -1px rgba(23, 33, 31, 0.06), 0 2px 4px -2px rgba(23, 33, 31, 0.04)',
        modal: '0 20px 25px -5px rgba(23, 33, 31, 0.08), 0 8px 10px -6px rgba(23, 33, 31, 0.04)',
      },
    },
  },
  plugins: [],
}
