<template>
  <nav class="navbar">
    <div class="nav-brand">客服对话提取系统</div>
    <div class="nav-links">
      <router-link to="/" class="nav-link">仪表盘</router-link>
      <router-link to="/conversations" class="nav-link">对话列表</router-link>
      <router-link to="/results" class="nav-link">提取结果</router-link>
      <router-link to="/validation" class="nav-link">验证</router-link>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  background: #1a1a2e;
  color: #eee;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
}
.nav-brand {
  font-size: 18px;
  font-weight: 600;
}
.nav-links {
  display: flex;
  gap: 8px;
}
.nav-link {
  color: #aaa;
  padding: 8px 16px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 14px;
  transition: background 0.2s, color 0.2s;
}
.nav-link:hover,
.nav-link.router-link-active {
  background: rgba(255,255,255,0.1);
  color: #fff;
}
</style>
