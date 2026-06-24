#!/bin/bash
set -e

echo "=== Money Radar — Frontend Installer ==="
echo ""

FEEDSFUN_DIR="${1:-./feeds.fun}"
SOURCE_DIR="${2:-.}"

if [ ! -d "$FEEDSFUN_DIR/site" ]; then
    echo "ERROR: feeds.fun frontend not found at $FEEDSFUN_DIR/site"
    echo "Run setup.sh first."
    exit 1
fi

SITE_DIR="$FEEDSFUN_DIR/site"
SRC_DIR="$SOURCE_DIR/frontend"

echo "[1/5] Copying i18n files..."
mkdir -p "$SITE_DIR/src/i18n"
cp "$SRC_DIR/i18n/zh-CN.json" "$SITE_DIR/src/i18n/"
echo "  Copied zh-CN.json"

echo "[2/5] Copying CSS overrides..."
mkdir -p "$SITE_DIR/src/styles"
cp "$SRC_DIR/styles/money-radar.css" "$SITE_DIR/src/styles/"
echo "  Copied money-radar.css"

echo "[3/5] Copying theme switcher components..."
mkdir -p "$SITE_DIR/src/components"
cp "$SRC_DIR/components/theme-switcher.js" "$SITE_DIR/src/components/"
cp "$SRC_DIR/components/ThemeSwitcher.vue" "$SITE_DIR/src/components/"
echo "  Copied theme-switcher.js and ThemeSwitcher.vue"

echo "[4/5] Creating theme initialization script..."
cat > "$SITE_DIR/src/init-theme.js" << 'EOF'
/**
 * Money Radar — Theme Initialization
 * 
 * Add this to your main.js or App.vue:
 *   import './init-theme';
 */

(function() {
  var THEME_KEY = 'money-radar-theme';
  var DEFAULT_THEME = 'authoritative';
  
  try {
    var theme = localStorage.getItem(THEME_KEY) || DEFAULT_THEME;
    document.documentElement.setAttribute('data-theme', theme);
  } catch (e) {
    document.documentElement.setAttribute('data-theme', DEFAULT_THEME);
  }
})();
EOF
echo "  Created init-theme.js"

echo "[5/5] Creating integration instructions..."
cat > "$SITE_DIR/MONEY_RADAR_INTEGRATION.md" << 'EOF'
# Money Radar Frontend Integration

## Quick Integration (3 steps)

### Step 1: Import CSS
Add to your `src/main.js` or `src/App.vue`:
```js
import './styles/money-radar.css';
import './init-theme';
```

### Step 2: Add Theme Switcher
In your Settings page or Sidebar:
```vue
<script setup>
import ThemeSwitcher from './components/ThemeSwitcher.vue';
</script>

<template>
  <ThemeSwitcher />
  <!-- or compact version: -->
  <ThemeSwitcher compact />
</template>
```

### Step 3: Use i18n (optional)
If you want to use the Chinese translations:
```js
import zhCN from './i18n/zh-CN.json';

// Use in your components:
const t = (key) => zhCN[key] || key;
```

## Theme CSS Variables

Use these variables in your components:
- `var(--mr-bg-primary)` — Main background
- `var(--mr-bg-secondary)` — Secondary background
- `var(--mr-text-primary)` — Main text
- `var(--mr-text-secondary)` — Secondary text
- `var(--mr-accent)` — Accent color
- `var(--mr-border)` — Border color
- `var(--mr-font-serif)` — Serif font (headings)
- `var(--mr-font-sans)` — Sans-serif font (body)
- `var(--mr-font-mono)` — Monospace font (scores/data)

## Available Themes
- `authoritative` — Professional news style (default)
- `eink` — Pure black and white
- `easyeyes` — Warm tones, easy on eyes
EOF
echo "  Created MONEY_RADAR_INTEGRATION.md"

echo ""
echo "=== Frontend Installation Complete ==="
echo ""
echo "Next steps:"
echo "  1. Read $SITE_DIR/MONEY_RADAR_INTEGRATION.md"
echo "  2. Add CSS import to main.js"
echo "  3. Add ThemeSwitcher component to Settings"
echo "  4. Rebuild frontend: cd $FEEDSFUN_DIR && npm run build"
