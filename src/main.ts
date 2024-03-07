import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css'
import 'cesium/Build/Cesium/Widgets/widgets.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import locale from 'element-plus/dist/locale/zh-cn'; // 导入中文语言包
import 'element-plus/theme-chalk/dark/css-vars.css'
const app = createApp(App);
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
app.use(store);
app.use(router);
app.use(ElementPlus, { locale });
app.mount("#app");
document.documentElement.classList.add('dark');
