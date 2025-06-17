<template>
  <div class="home-container">

    <!-- 顶部 -->
    <section class="section title-section">
      <h1>🛰️ WebGIS 三维轨道可视化平台</h1>
      <p class="subtitle">华东师范大学 · 遥感与GIS硕士 · Vue3 + Cesium 项目实践</p>
    </section>

    <!-- 功能模块 / 技术栈 -->
    <section class="section cards-section">
      <el-card class="card hover-card">
        <h2 class="module-title">🔧 模块功能亮点</h2>
        <p>三维轨道渲染、过境路径预测、动态轨迹参数控制与调试、地图图层切换配置。</p>
        <router-link to="/data-select">
          <el-button type="primary" size="small">进入模块演示</el-button>
        </router-link>
      </el-card>
      <el-card class="card hover-card">
        <h2 class="module-title">🛠️ 技术实现</h2>
        <ul class="tech-list">
          <li>Vue3 + TypeScript 前端模块化开发</li>
          <li>CesiumJS 构建 WebGL 三维地球</li>
          <li>Element Plus 快速 UI 构建</li>
          <li>GitHub Pages 自动部署</li>
        </ul>
      </el-card>
    </section>

    <!-- 项目截图展示 -->
    <section class="section preview-section">
      <h2 class="module-title">📸 项目效果图片</h2>
      <div class="screenshot-row">
        <img src="demo2.jpg" alt="示意图2" class="screenshot-img" />
        <img src="demo3.jpg" alt="示意图3" class="screenshot-img" />
        <img src="demo5.jpg" alt="示意图5" class="screenshot-img" />
        <img src="demo6.jpg" alt="示意图6" class="screenshot-img" />
      </div>
      <p class="carousel-note">支持科研演示、教学展示、可集成部署使用</p>
    </section>

    <!-- 简历 & 联系方式 -->
    <section class="section contact-section">
      <h2 class="module-title">📄 简历 & 联系方式</h2>
      <div class="contact-content">
        <div class="contact-left">
          <el-link
            href="resume.pdf"
            target="_blank"
            download
            class="resume-link"
          >
            <el-icon><Document /></el-icon>
            下载简历 PDF
          </el-link>
          <el-link
            href="https://github.com/qingjianshi/orbital-prediction-demo"
            target="_blank"
          >
            💻 GitHub 项目仓库
          </el-link>
        </div>
        <!-- 点击二维码放大 -->
        <div class="qr-box">
          <el-image
            style="width: 120px; border-radius: 8px"
            :src="'wechat_qr.jpg'"
            :preview-src-list="['wechat_qr.jpg']"
          />
          <p>📱 微信扫码联系我</p>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { Document } from '@element-plus/icons-vue'
</script>

<style scoped>
body {
  background-color: #0f0f0f;
  color: #f0f0f0;
}
.home-container {
  /* padding: 2rem 4vw; */
  max-width: 1400px;
  margin: 0 auto;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

/* .section {
  margin-bottom: 48px;
} */

/* 顶部标题 */
.title-section {
  text-align: center;
}
.title-section h1 {
  font-size: 2.6rem;
  font-weight: bold;
  background: linear-gradient(to right, #42a5f5, #00e5ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.subtitle {
  font-size: 1.1rem;
  color: #aaa;
  margin-top: 0.5rem;
}

/* 模块标题 */
.module-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #03e9f4;
}

/* 卡片展示 */
.cards-section {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}
.card {
  background: #1e1e1e;
  border: 1px solid #333;
  /* padding: 1.4rem; */
  border-radius: 10px;
  flex: 1;
  min-width: 320px;
  color: #ddd;
  transition: all 0.3s ease;
}
.hover-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 0 14px rgba(0, 170, 255, 0.15);
}
.tech-list {
  line-height: 1.6;
  font-size: 0.95rem;
  padding-left: 1.2rem;
  color: #bbb;
}

/* 项目截图 */
.preview-section h2 {
  text-align: center;
}
.screenshot-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
.screenshot-img {
  height: 180px;
  border-radius: 8px;
  border: 1px solid #444;
  object-fit: contain;
  background-color: #111;
  padding: 6px;
  transition: transform 0.2s ease;
}
.screenshot-img:hover {
  transform: scale(1.05);
}
.carousel-note {
  text-align: center;
  font-size: 0.9rem;
  color: #888;
  margin-top: 10px;
}

/* 联系方式 & 简历 */
.contact-content {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  align-items: center;
  gap: 24px;
}
.contact-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.resume-link {
  font-weight: bold;
  color: #00e0ff;
}
.resume-link:hover {
  color: #41ec91;
  transform: scale(1.05);
}
.qr-box p {
  text-align: center;
  font-size: 0.85rem;
  color: #aaa;
  margin-top: 6px;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .cards-section {
    flex-direction: column;
  }
  .contact-content {
    flex-direction: column;
    align-items: flex-start;
  }
  .screenshot-img {
    height: auto;
    width: 100%;
  }
}
</style>
