import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import data_select from '../views/data-select.vue'
import orbit_prediction from '../views/orbit_prediction.vue'
import orbit_transit from '../views/orbit_transit.vue'

const routes: Array<RouteRecordRaw> = [
  
  { path: '/', component: data_select },
  { path: '/orbit_prediction', component: orbit_prediction, meta: { requiresAuth: true },},
  { path: '/orbit_transit', component: orbit_transit, meta: { requiresAuth: true },},
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
