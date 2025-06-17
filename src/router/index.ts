import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router'
import Home from '../views/Home.vue'
import data_select from '../views/data-select.vue'
import orbit_prediction from '../views/orbit_prediction.vue'
import orbit_transit from '../views/orbit_transit.vue'

const routes: Array<RouteRecordRaw> = [
  {path: '/',name: 'Home',component: Home},
  {path: '/data-select',name: 'data_select',component: data_select},
  { path: '/orbit_prediction', component: orbit_prediction, meta: { requiresAuth: true },},
  { path: '/orbit_transit', component: orbit_transit, meta: { requiresAuth: true },},
  {
    path: '/:catchAll(.*)',  // 404 路由处理
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
