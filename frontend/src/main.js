import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

import DashboardView from './views/DashboardView.vue'
import ConversationsView from './views/ConversationsView.vue'
import ResultsView from './views/ResultsView.vue'
import ValidationView from './views/ValidationView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/conversations', name: 'conversations', component: ConversationsView },
  { path: '/results', name: 'results', component: ResultsView },
  { path: '/validation', name: 'validation', component: ValidationView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')
