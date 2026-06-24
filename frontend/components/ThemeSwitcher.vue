<!--
  Money Radar — Theme Switcher Vue Component
  
  Usage:
    <ThemeSwitcher />
    <ThemeSwitcher compact />  <!-- Small inline version -->
-->

<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps({
  compact: { type: Boolean, default: false },
});

const THEME_KEY = 'money-radar-theme';
const currentTheme = ref('authoritative');

const themes = [
  { id: 'authoritative', name: '权威', desc: '专业新闻风格', icon: '📰' },
  { id: 'eink', name: '墨水屏', desc: '纯黑白，像报纸', icon: '📖' },
  { id: 'easyeyes', name: '养眼', desc: '暖色调，不累眼', icon: '🌅' },
];

function switchTheme(themeId) {
  currentTheme.value = themeId;
  document.documentElement.setAttribute('data-theme', themeId);
  try {
    localStorage.setItem(THEME_KEY, themeId);
  } catch {}
  window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: themeId } }));
}

onMounted(() => {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved && themes.find(t => t.id === saved)) {
      currentTheme.value = saved;
      document.documentElement.setAttribute('data-theme', saved);
    }
  } catch {}
});
</script>

<template>
  <div class="theme-switcher" :class="{ compact }">
    <template v-if="!compact">
      <div class="theme-label">主题</div>
      <div class="theme-options">
        <button
          v-for="theme in themes"
          :key="theme.id"
          class="theme-option"
          :class="{ active: currentTheme === theme.id }"
          @click="switchTheme(theme.id)"
        >
          <span class="theme-icon">{{ theme.icon }}</span>
          <span class="theme-name">{{ theme.name }}</span>
          <span class="theme-desc">{{ theme.desc }}</span>
        </button>
      </div>
    </template>
    <template v-else>
      <div class="theme-toggle">
        <button
          v-for="theme in themes"
          :key="theme.id"
          class="theme-btn"
          :class="{ active: currentTheme === theme.id }"
          :title="theme.name"
          @click="switchTheme(theme.id)"
        >
          {{ theme.icon }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.theme-switcher {
  padding: 16px 0;
}

.theme-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--mr-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 12px;
}

.theme-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--mr-border);
  border-left: 2px solid transparent;
  background: transparent;
  cursor: pointer;
  text-align: left;
  width: 100%;
  font-family: var(--mr-font-sans);
  transition: all 0.1s ease;
}

.theme-option:hover {
  background: var(--mr-bg-secondary);
}

.theme-option.active {
  border-left-color: var(--mr-accent);
  background: var(--mr-accent-dim);
}

.theme-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.theme-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--mr-text-primary);
}

.theme-desc {
  font-size: 11px;
  color: var(--mr-text-tertiary);
  margin-left: auto;
}

/* Compact mode */
.theme-toggle {
  display: flex;
  gap: 2px;
  background: var(--mr-bg-tertiary);
  padding: 2px;
  border-radius: 4px;
}

.theme-btn {
  padding: 4px 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  border-radius: 2px;
  transition: background 0.1s ease;
}

.theme-btn:hover {
  background: var(--mr-bg-hover);
}

.theme-btn.active {
  background: var(--mr-bg-primary);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
</style>
