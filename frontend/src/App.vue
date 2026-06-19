<template>
  <div id="app-root">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
  background: #f5f5f7;
  color: #1d1d1f;
  line-height: 1.5;
}
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
</style>
