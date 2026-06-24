/**
 * Money Radar — Theme Switcher
 * 
 * Manages 3 themes: authoritative, eink, easyeyes
 * Persists choice in localStorage
 * 
 * Usage:
 *   import { initTheme, switchTheme, getTheme } from './theme-switcher';
 *   initTheme(); // Call on app start
 *   switchTheme('eink'); // Switch theme
 */

const THEME_KEY = 'money-radar-theme';
const THEMES = ['authoritative', 'eink', 'easyeyes'];
const DEFAULT_THEME = 'authoritative';

/**
 * Get current theme from localStorage
 */
export function getTheme() {
  try {
    return localStorage.getItem(THEME_KEY) || DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

/**
 * Set theme on document and persist to localStorage
 */
export function switchTheme(theme) {
  if (!THEMES.includes(theme)) {
    console.warn(`Unknown theme: ${theme}. Using default.`);
    theme = DEFAULT_THEME;
  }

  // Set data-theme attribute on html element
  document.documentElement.setAttribute('data-theme', theme);

  // Persist
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    // localStorage not available
  }

  // Dispatch event for other components
  window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
}

/**
 * Initialize theme on app start
 */
export function initTheme() {
  const theme = getTheme();
  switchTheme(theme);
}

/**
 * Get all available themes with metadata
 */
export function getThemes() {
  return [
    {
      id: 'authoritative',
      name: '权威',
      description: '专业新闻风格，白色背景',
      preview: {
        bg: '#ffffff',
        text: '#1a1a1a',
        accent: '#c41e3a',
      },
    },
    {
      id: 'eink',
      name: '墨水屏',
      description: '纯黑白，像报纸',
      preview: {
        bg: '#ffffff',
        text: '#000000',
        accent: '#000000',
      },
    },
    {
      id: 'easyeyes',
      name: '养眼',
      description: '暖色调，长时间阅读不累',
      preview: {
        bg: '#f8f6f1',
        text: '#3d3529',
        accent: '#8b6914',
      },
    },
  ];
}

/**
 * Cycle to next theme
 */
export function cycleTheme() {
  const current = getTheme();
  const idx = THEMES.indexOf(current);
  const next = THEMES[(idx + 1) % THEMES.length];
  switchTheme(next);
  return next;
}
