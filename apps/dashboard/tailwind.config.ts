import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f7ff',
          500: '#5a67ff',
          600: '#4a55e0',
          900: '#1a1f4a',
        },
      },
    },
  },
  plugins: [],
};
export default config;
