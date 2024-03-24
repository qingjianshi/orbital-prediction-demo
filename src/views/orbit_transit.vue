<template>
    <div ref="mapContainer" class="map-container">
        <div class="title">
            <h1>卫星过境预测</h1>
        </div>
        <div v-if="orbitData2 && selectedData" class="selected_info"
            style="max-height:25vh;max-width:35vw;overflow: hidden;overflow-y: auto;overflow-x: auto;">
            <div style="margin-left: 1vw;font-size: 14px;">
                <p>地点:{{ selectedData.area }}</p>
                <p>开始时间: {{ selectedData.time_start }}</p>
                <p>结束时间: {{ selectedData.time_end }}</p>
            </div>
        </div>
        <div class="select_box" :style="selectBoxStyles">
            <el-table :data="satelliteData" @row-click="handleRowClick"
                style="margin-bottom: 20px;max-height: 50vh;overflow: auto;">
                <el-table-column prop="chinese_name" label="卫星名"></el-table-column>
                <el-table-column label="过境时间(UTC)">
                    <template v-slot="{ row }">
                        <div v-for="(time, index) in row.orbit" :key="index">
                            {{ formatUTCDate(time.time_iso) }}
                        </div>
                    </template>
                </el-table-column>
            </el-table>
        </div>
        <div id="mouse-position" class="mouse-position"></div>
        <div class="collapse-arrow" @click="toggleSelectBox" :style="arrow">
            <el-icon size='30px'>
                <ArrowRight v-if="isCollapsed" />
                <ArrowLeft v-else />
            </el-icon>
        </div>
        <div id="infoBox" class="ol-popup" style="display: none;">
            <div id="infoContent"></div>
        </div>

    </div>
</template>
<script setup>
import { onMounted, ref, reactive, onBeforeUnmount, computed } from 'vue';
import 'ol/ol.css';
import { Map, View } from 'ol';
import { Tile as TileLayer } from 'ol/layer';
import XYZ from 'ol/source/XYZ';
import { Vector as VectorLayer } from 'ol/layer';
import { Vector as VectorSource } from 'ol/source';
import { toLonLat } from 'ol/proj';
import { defaults as defaultControls, FullScreen, ScaleLine, OverviewMap, ZoomSlider, Rotate } from 'ol/control';
import Feature from 'ol/Feature';
import { Fill, Stroke, Style } from 'ol/style';
import { Polygon } from 'ol/geom';
import Overlay from 'ol/Overlay';
import { transform } from 'ol/proj';


// 解决ResizeObserver报错问题
const debounce = (callback, delay) => {
    let tid;
    return function (...args) {
        const ctx = self;
        tid && clearTimeout(tid);
        tid = setTimeout(() => {
            callback.apply(ctx, args);
        }, delay);
    };
};
const _ = window.ResizeObserver;
window.ResizeObserver = class ResizeObserver extends _ {
    constructor(callback) {
        callback = debounce(callback, 20);
        super(callback);
    }
};
const orbitData2 = ref(null);
const mapContainer = ref(null);
const map = reactive({ value: null });
const selectedData = ref(null);
const isCollapsed = ref(false);
const satelliteData = ref([]);
const currentSelectedFeature = ref(null);
const vectorSource = reactive(new VectorSource());
const arrow = computed(() => ({
    marginLeft: isCollapsed.value ? '0' : '30%',
}));
const toggleSelectBox = () => {
    isCollapsed.value = !isCollapsed.value; // 修改响应式数据的值
};
const selectBoxStyles = computed(() => ({
    transition: 'width 0.5s',
    marginTop: '25vh',
    width: isCollapsed.value ? '0' : '30%',
    overflow: isCollapsed.value ? 'hidden' : 'visible', // 当折叠时隐藏内容
}));
// 假设这是我们的默认样式
const defaultStyle = new Style({
    fill: new Fill({
        color: 'rgba(255, 255, 255, 0.0)' // 白色透明
    }),
    stroke: new Stroke({
        color: '#3399CC', // 可以保留原始边框颜色，或者也可以调整
        width: 1
    })
});

const formatUTCDate=(dateString)=> {
      // 解析ISO 8601字符串为Date对象
      const date = new Date(dateString);

      // 使用getUTC*方法获取UTC时间的年、月、日、小时等信息
      const year = date.getUTCFullYear(); // 年
      const month = date.getUTCMonth() + 1; // 月（getUTCMonth()返回的月份是0-11，需要加1）
      const day = date.getUTCDate(); // 日
      const hour = date.getUTCHours(); // 小时

      // 格式化为两位数
      const monthFormatted = month.toString().padStart(2, '0');
      const dayFormatted = day.toString().padStart(2, '0');
      const hourFormatted = hour.toString().padStart(2, '0');

      // 组合成最终的字符串格式
      return `${year}年${monthFormatted}月${dayFormatted}日${hourFormatted}时(UTC)`;
    }

// 更新我们的高亮样式为蓝色透明
const highlightStyle = new Style({
    fill: new Fill({
        color: 'rgba(0, 0, 255, 0.6)' // 蓝色透明
    }),
    stroke: new Stroke({
        color: '#ffcc33', // 高亮边框颜色可以保留，或者也可以调整以匹配新的填充颜色
        width: 2
    })
});


// 用来存储当前高亮的特征
let currentHighlightedFeatures = [];

// 用于处理行点击事件的函数
function handleRowClick(row) {
    const id = row.chinese_name;
    // 先将之前的高亮特征恢复到默认样式
    currentHighlightedFeatures.forEach(feature => {
        feature.setStyle(defaultStyle);
    });
    // 清空当前高亮特征列表
    currentHighlightedFeatures = [];

    // 查找所有匹配的特征并应用高亮样式
    const matchingFeatures = vectorSource.getFeatures().filter(f => f.get('id') === id);
    matchingFeatures.forEach(feature => {
        feature.setStyle(highlightStyle);
        // 将这个特征添加到当前高亮特征列表中
        currentHighlightedFeatures.push(feature);
    });
}

onMounted(() => {
    const storedData = localStorage.getItem('orbitData2');
    const storedData2 = localStorage.getItem('select_area');
    if (storedData && storedData2) {
        // 将JSON字符串转换回对象
        orbitData2.value = JSON.parse(storedData);
        selectedData.value = JSON.parse(storedData2);
    }
    // 数据处理
    const processSatelliteData = () => {
        if (orbitData2 && orbitData2.value) {
            Object.values(orbitData2.value).forEach(satellite => {
                satelliteData.value.push({
                    ...satellite.info,
                    orbit: satellite.orbit,
                });
            });
        }
    };
    processSatelliteData();
    console.log(satelliteData.value)
    // function processSatellitesData(satellites) {
    //     let result = {};
    //     satellites.forEach(satellite => {
    //         satellite.orbit.forEach(orbit => {
    //             const date = orbit.time_iso.split('T')[0]; // Extract the date
    //             const key = `${satellite.chinese_name}-${date}`;

    //             if (!result[key]) {
    //                 result[key] = {
    //                     name: satellite.chinese_name,
    //                     width: satellite.width,
    //                     date: date,
    //                     lineString: []
    //                 };
    //             }

    //             result[key].lineString.push([orbit.lon, orbit.lat]);
    //         });
    //     });
    //     return Object.values(result).map(item => ({
    //         name: item.name,
    //         width: item.width,
    //         date: item.date,
    //         lineString: {
    //             type: "LineString",
    //             coordinates: item.lineString
    //         }
    //     }));
    // }
    // const processedData = processSatellitesData(satelliteData.value);

    const overviewMapControl = new OverviewMap({
        // 这里可以设置一些选项，比如collapsed和label等
        layers: [
            new TileLayer({
                source: new XYZ({
                    url: 'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetPurplishBlue/MapServer/tile/{z}/{y}/{x}',
                })
            })
        ],
        collapseLabel: '\u00BB',
        label: '\u00AB',
        collapsed: false
    });

    map.value = new Map({
        target: mapContainer.value,
        layers: [
            //   new TileLayer({
            //     source: new XYZ({
            //       url: 'https://t0.tianditu.gov.cn/DataServer?x={x}&y={y}&l={z}&T=vec_c&tk=9df1e2d38f43b8983357c36603d366e5',
            //     }),
            //   }),
            //   new TileLayer({
            //   source: new XYZ({
            //     url: 'https://t0.tianditu.gov.cn/DataServer?x={x}&y={y}&l={z}&T=cva_c&tk=9df1e2d38f43b8983357c36603d366e5',
            //   }),
            // }),
            new TileLayer({
                source: new XYZ({
                    url: 'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetPurplishBlue/MapServer/tile/{z}/{y}/{x}'
                })
            }),
        ],
        view: new View({
            center: [12923468.57, 4865948.20], // 使用墨卡托坐标范围内的一个点
            zoom: 3, // 适当的缩放级别
            projection: 'EPSG:3857' // 使用墨卡托投影
        }),
        // 添加默认控件
        controls: defaultControls().extend([
            new FullScreen(), // 全屏控件
            new ScaleLine(), // 比例尺控件
            overviewMapControl,
            new ZoomSlider(), // 缩放滑块
            new Rotate() // 旋转控件
        ]),
    });
    // 获取鼠标位置的容器引用
    const mousePositionContainer = document.getElementById('mouse-position');

    // 添加鼠标移动事件的监听器
    map.value.on('pointermove', function (evt) {
        // 确保默认行为不会发生，比如地图平移
        evt.preventDefault();

        // 获取鼠标位置的OpenLayers坐标
        const coordinate = map.value.getEventCoordinate(evt.originalEvent);

        // 将OpenLayers坐标转换为经纬度
        const lonLat = toLonLat(coordinate);

        // 格式化经纬度为字符串
        const lonLatStr = lonLat.map(function (coord) {
            return coord.toFixed(6);
        }).join(', ');

        // 更新显示容器的内容
        mousePositionContainer.innerText = `Lon: ${lonLatStr.split(', ')[0]}, Lat: ${lonLatStr.split(', ')[1]}`;
    });
    // 遍历数据，绘制LineString和对应的缓冲区
    satelliteData.value.forEach(item => {
        // // 假设item.lineString.coordinates是EPSG:4326坐标
        // const lineStringCoords4326 = item.lineString.coordinates;
        // const lineString4326 = new LineString(lineStringCoords4326);

        // // 创建与LineString旋转角度一致的矩形缓冲区
        // // 计算LineString的方向并生成矩形的四个角点
        // const generateRectangle = (coords, width) => {
        //     if (coords.length < 2) return null;
        //     const start = coords[0];
        //     const end = coords[coords.length - 1];
        //     const angle = Math.atan2(end[1] - start[1], end[0] - start[0]);
        //     const dx = (width / 2) * Math.sin(angle);
        //     const dy = (width / 2) * Math.cos(angle);
        //     return [
        //         [start[0] - dx, start[1] + dy],
        //         [end[0] - dx, end[1] + dy],
        //         [end[0] + dx, end[1] - dy],
        //         [start[0] + dx, start[1] - dy],
        //         [start[0] - dx, start[1] + dy] // 闭合多边形
        //     ];
        // };
        console.log(item);
        // 以最小外接矩形为基础创建多边形，这里简化处理：直接使用LineString的端点和指定宽度
        const rectangleCoords = item.orbit[0].image_coordinates.coordinates[0].map(coord => transform(coord, 'EPSG:4326', 'EPSG:3857'));
        console.log(rectangleCoords)
        const rectanglePolygon = new Polygon([rectangleCoords]);

        // 创建Feature，并设置id和data属性
        const bufferFeature = new Feature({
            geometry: rectanglePolygon,
            id: item.chinese_name, // 假设卫星名存储在item.name中
            data: formatUTCDate(item.orbit[0].time_iso) // 假设过境时间存储在item.passTime中
        });
        bufferFeature.getGeometry();

        vectorSource.addFeature(bufferFeature);

        // 创建矢量图层，并应用样式
        const vectorLayer = new VectorLayer({
            source: vectorSource,
            style: defaultStyle,
        });

        // 将图层添加到地图
        map.value.addLayer(vectorLayer);
    });

    map.value.on('click', function (evt) {
        let featureFound = false; // Flag to indicate if a feature is found
        map.value.forEachFeatureAtPixel(evt.pixel, function (feature) {
            if (!featureFound && feature.getGeometry().getType() === 'Polygon') {
                // 获取Feature的名字和数据
                const name = feature.get('id'); // 获取卫星名字
                const date = feature.get('data');; // 获取过境日期
                showInfoBox(evt.coordinate, name, date); // 调用函数显示信息框
                featureFound = true; // Set flag to true as we found at least one feature
            }
        });
        if (!featureFound) {
            infoOverlay.setPosition(undefined); // 隐藏信息框
        }
    });


    function showInfoBox(coordinate, name, date) {
        // 获取用于显示信息的HTML元素
        const infoContent = document.getElementById('infoContent');
        // 设置HTML内容
        infoContent.innerHTML = `<h3>${name}</h3><p>过境时间: ${date}</p>`;
        // 设定Overlay的位置（基于地图坐标）
        infoOverlay.setPosition(coordinate);
        // 显示信息框
        document.getElementById('infoBox').style.display = 'block';
    }
    // 创建Overlay
    const infoOverlay = new Overlay({
        element: document.getElementById('infoBox'), // 信息框的HTML元素
        autoPan: true, // 如果需要，自动平移地图以确保信息框完全可见
        autoPanAnimation: {
            duration: 250 // 平移动画的持续时间（毫秒）
        }
    });

    // 将Overlay添加到地图中
    map.value.addOverlay(infoOverlay);

    return { handleRowClick, map };

})
</script>
<style scoped>
.map-container {
    height: 98vh;
    position: relative;
    z-index: 1000;
}

.select_box {
    position: absolute;
    z-index: 1000;
}

.title {
    position: absolute;
    color: white;
    z-index: 1000;
    height: 2vh;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    display: flex;
    justify-content: center;
    /* 水平居中 */
}

.collapse-arrow {
    position: absolute;
    margin-top: 35vh;
    margin-left: 28vw;
    transform: translateY(-50%);
    background-color: transparent;
    /* 可选：透明背景 */
    border: none;
    /* 取消边框 */
    color: #077ef4;
    z-index: 1010;
    /* 确保图标在 select_box 之上 */
}

.mouse-position {
    position: absolute;
    bottom: 3vh;
    right: 0;
    z-index: 1000;
    /* 确保它在地图层之上 */
}

.selected_info {
    position: absolute;
    display: flex;
    justify-content: center;
    align-items: center;
    top: 8vh;
    /* 放到底部 */
    left: 0;
    /* 放到右边 */
    display: flex;
    /* 使用flex布局 */
    flex-direction: row;
    /* 子元素水平排列 */
    align-items: center;
    border-width: 2px;
    border-style: dashed;
    border-color: #2c3e50;
    z-index: 1000;
}

html,
body {
    height: 100vh;
    width: 100vw;
    margin: 0;
    padding: 0;
    overflow: hidden;
}
</style>