<template>
    <div ref="mapContainer" id='map-container' class="map-container">
        <div class="title">
            <h1>卫星过境预测</h1>
        </div>
        <div v-if="orbitData2 && selectedData" class="selected_info"
            style="max-height:25vh;max-width:35vw;overflow: hidden;margin-left: 1vw;">
            <div style="font-size: 14px;background-color: #2c3e50;width: 25vw;">
                <h2>（结果仅供参考）</h2>
                <p>时间：{{ selectedData.time_start.substring(0, 10) }}至{{ selectedData.time_end.substring(0, 10) }}</p>
            </div>
        </div>
        <div class="select_box" :style="selectBoxStyles">
            <el-table :data="satelliteData" @row-click="handleRowClick"
                style="margin-bottom: 20px; max-height: 50vh; overflow: auto;"
                :header-cell-style="{ background: '#2c3e50', color: 'white' }"
                :column-cell-style="{ background: '#2c3e50', color: 'white' }">
                <!-- 卫星名称列 -->
                <el-table-column prop="chinese_name" label="卫星名"></el-table-column>
                <!-- 过境时间列 -->
                <el-table-column prop="time_local" label="过境时间"></el-table-column>
            </el-table>
            <el-button @click="back_home" style="width: 40%;background-color: #2c3e50;margin-left: 40%;">返回</el-button>

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
        <div id="overviewMap" class="overview-map"></div>


    </div>
</template>
<script setup>
import { onMounted, ref, reactive, onBeforeUnmount, computed } from 'vue';
import 'ol/ol.css';
import { useRouter } from 'vue-router';
const router = useRouter();
import { Map, View } from 'ol';
import { Tile as TileLayer } from 'ol/layer';
import XYZ from 'ol/source/XYZ';
import { Vector as VectorLayer } from 'ol/layer';
import { Vector as VectorSource } from 'ol/source';
import { toLonLat } from 'ol/proj';
import { defaults as defaultControls, FullScreen, ScaleLine, OverviewMap, ZoomSlider, Rotate } from 'ol/control';
import Feature from 'ol/Feature';
import { Fill, Stroke, Style } from 'ol/style';
import { MultiPolygon, Polygon } from 'ol/geom';
import Overlay from 'ol/Overlay';
import WKT from 'ol/format/WKT';
const vector = new VectorLayer({
    source: new VectorSource(),
});



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
    marginLeft: isCollapsed.value ? '0' : '26vw',
}));
const toggleSelectBox = () => {
    isCollapsed.value = !isCollapsed.value; // 修改响应式数据的值
};
const selectBoxStyles = computed(() => ({
    transition: 'width 0.5s',
    marginTop: '35vh',
    marginLeft:'1vw',
    width: isCollapsed.value ? '0' : '25vw',
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

const back_home = () => {
    router.push({
        path: '/',
    });
}
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

let previouslyHighlightedRowId = null; // 用于跟踪上一次点击的行ID

function handleRowClick(row) {
    const id = row.chinese_name + row.time_local;
    console.log(id)
    // 检查是否点击了相同的行
    if (previouslyHighlightedRowId === id) {
        // 如果是相同的行，则移除高亮并重置previouslyHighlightedRowId
        currentHighlightedFeatures.forEach(feature => {
            feature.setStyle(defaultStyle);
        });
        currentHighlightedFeatures = [];
        previouslyHighlightedRowId = null;
    } else {
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

        // 更新previouslyHighlightedRowId为当前行ID
        previouslyHighlightedRowId = id;
    }
}

const restoreSelections = () => {
    // const storedSelections2 = localStorage.getItem('selectedOptions');
    const storedGeometryString = localStorage.getItem('storedGeometry');
    if (storedGeometryString) {
        const format = new WKT();
        const storedFeature = format.readFeature(storedGeometryString, {
            dataProjection: 'EPSG:4326',
            featureProjection: map.value.getView().getProjection()
        });
        vector.getSource().addFeature(storedFeature);
        map.value.addLayer(vector);
    }
    // if (storedSelections2){
    //     selectedData.value = JSON.parse(storedSelections2);
    //     if (selectedData.value.length > 0) {
    //   fetchOptions(selectedData.value[0], 1);
    // }
    // }
};

onMounted(() => {
    const storedData = localStorage.getItem('orbitData2');
    const storedData2 = localStorage.getItem('select_area');
    if (storedData && storedData2) {
        // 将JSON字符串转换回对象
        orbitData2.value = JSON.parse(storedData);
        selectedData.value = JSON.parse(storedData2);
    }


    // 数据处理
    console.log(orbitData2.value);
    const processSatelliteData = () => {
        if (orbitData2 && orbitData2.value) {
            Object.values(orbitData2.value).forEach(satellite => {
                satellite.orbit.forEach(orbitItem => {
                    satelliteData.value.push({
                        chinese_name: satellite.info.chinese_name,
                        time_local: orbitItem.properties.time_local,
                        orbit: orbitItem,
                    })
                });
            });
        }
    };
    processSatelliteData();
    
    const overviewMapControl = new OverviewMap({
        
        // 这里可以设置一些选项，比如collapsed和label等
        layers: [
            new TileLayer({
                source: new XYZ({
                    url: 'https://t0.tianditu.gov.cn/DataServer?x={x}&y={y}&l={z}&T=vec_w&tk=9df1e2d38f43b8983357c36603d366e5',
                    tileLoadFunction: function (imageTile, src) {
                        // 使用滤镜 将白色修改为深色
                        let img = new Image()
                        img.crossOrigin = ''
                        // 设置图片不从缓存取，从缓存取可能会出现跨域，导致加载失败
                        img.setAttribute('crossOrigin', 'anonymous')
                        img.onload = function () {
                            let canvas = document.createElement('canvas')
                            let w = img.width
                            let h = img.height
                            canvas.width = w
                            canvas.height = h
                            let context = canvas.getContext('2d')
                            context.filter = 'grayscale(98%) invert(100%) sepia(20%) hue-rotate(180deg) saturate(1600%) brightness(80%) contrast(90%)'
                            context.drawImage(img, 0, 0, w, h, 0, 0, w, h)
                            imageTile.getImage().src = canvas.toDataURL('image/png')
                        }
                        img.src = src
                    },
                }),
            }),
            new TileLayer({
                source: new XYZ({
                    url: 'https://t0.tianditu.gov.cn/DataServer?x={x}&y={y}&l={z}&T=cva_w&tk=9df1e2d38f43b8983357c36603d366e5',
                    tileLoadFunction: function (imageTile, src) {
                        // 使用滤镜 将白色修改为深色
                        let img = new Image()
                        img.crossOrigin = ''
                        // 设置图片不从缓存取，从缓存取可能会出现跨域，导致加载失败
                        img.setAttribute('crossOrigin', 'anonymous')
                        img.onload = function () {
                            let canvas = document.createElement('canvas')
                            let w = img.width
                            let h = img.height
                            canvas.width = w
                            canvas.height = h
                            let context = canvas.getContext('2d')
                            context.filter = 'grayscale(98%) invert(100%) sepia(20%) hue-rotate(180deg) saturate(1600%) brightness(80%) contrast(90%)'
                            context.drawImage(img, 0, 0, w, h, 0, 0, w, h)
                            imageTile.getImage().src = canvas.toDataURL('image/png')
                        }
                        img.src = src
                    },
                }),
            }),
            // new TileLayer({
            //     source: new XYZ({
            //         url: 'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetPurplishBlue/MapServer/tile/{z}/{y}/{x}',
            //     })
            // })
        ],
        collapseLabel: '\u00BB',
        label: '\u00AB',
        collapsed: false,
        collapsible: false, // 按需设定
        target: 'overviewMap', // 指定target为刚才创建的div的id
    });

    map.value = new Map({
        target: mapContainer.value,
        layers: [
            new TileLayer({
                source: new XYZ({
                    url: 'https://t0.tianditu.gov.cn/DataServer?x={x}&y={y}&l={z}&T=vec_w&tk=9df1e2d38f43b8983357c36603d366e5',
                    tileLoadFunction: function (imageTile, src) {
                        // 使用滤镜 将白色修改为深色
                        let img = new Image()
                        img.crossOrigin = ''
                        // 设置图片不从缓存取，从缓存取可能会出现跨域，导致加载失败
                        img.setAttribute('crossOrigin', 'anonymous')
                        img.onload = function () {
                            let canvas = document.createElement('canvas')
                            let w = img.width
                            let h = img.height
                            canvas.width = w
                            canvas.height = h
                            let context = canvas.getContext('2d')
                            context.filter = 'grayscale(98%) invert(100%) sepia(20%) hue-rotate(180deg) saturate(1600%) brightness(80%) contrast(90%)'
                            context.drawImage(img, 0, 0, w, h, 0, 0, w, h)
                            imageTile.getImage().src = canvas.toDataURL('image/png')
                        }
                        img.src = src
                    },
                }),
            }),
            new TileLayer({
                source: new XYZ({
                    url: 'https://t0.tianditu.gov.cn/DataServer?x={x}&y={y}&l={z}&T=cva_w&tk=9df1e2d38f43b8983357c36603d366e5',
                    tileLoadFunction: function (imageTile, src) {
                        // 使用滤镜 将白色修改为深色
                        let img = new Image()
                        img.crossOrigin = ''
                        // 设置图片不从缓存取，从缓存取可能会出现跨域，导致加载失败
                        img.setAttribute('crossOrigin', 'anonymous')
                        img.onload = function () {
                            let canvas = document.createElement('canvas')
                            let w = img.width
                            let h = img.height
                            canvas.width = w
                            canvas.height = h
                            let context = canvas.getContext('2d')
                            context.filter = 'grayscale(98%) invert(100%) sepia(20%) hue-rotate(180deg) saturate(1600%) brightness(80%) contrast(90%)'
                            context.drawImage(img, 0, 0, w, h, 0, 0, w, h)
                            imageTile.getImage().src = canvas.toDataURL('image/png')
                        }
                        img.src = src
                    },
                }),
            }),
            // new TileLayer({
            //     source: new XYZ({
            //         url: 'http://map.geoq.cn/ArcGIS/rest/services/ChinaOnlineStreetPurplishBlue/MapServer/tile/{z}/{y}/{x}'
            //     })
            // }),
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

    function getArrayDepth(value) {
        return Array.isArray(value)
            ? 1 + Math.max(...value.map(getArrayDepth))
            : 0;
    }
    // 遍历数据，绘制LineString和对应的缓冲区
    satelliteData.value.forEach(item => {
        console.log(item)
        if (getArrayDepth(item.orbit.geometry) === 4) {
            const rectangleCoords = item.orbit.geometry;
            console.log(rectangleCoords)
            const rectanglePolygon = new MultiPolygon(rectangleCoords);

            // 创建Feature，并设置id和data属性
            const bufferFeature = new Feature({
                geometry: rectanglePolygon,
                name:item.chinese_name,
                id: item.chinese_name + item.orbit.properties.time_local,
                data: item.orbit.properties.time_local
            });
            bufferFeature.getGeometry();

            vectorSource.addFeature(bufferFeature);

        }
        else {
            const rectangleCoords = item.orbit.geometry;
            console.log(rectangleCoords)
            const rectanglePolygon = new Polygon(rectangleCoords);

            // 创建Feature，并设置id和data属性
            const bufferFeature = new Feature({
                geometry: rectanglePolygon,
                id: item.chinese_name + item.orbit.properties.time_local,
                name:item.chinese_name,
                data: item.orbit.properties.time_local
            });
            bufferFeature.getGeometry();

            vectorSource.addFeature(bufferFeature);
        }
        // 创建矢量图层，并应用样式
        const vectorLayer = new VectorLayer({
                source: vectorSource,
                style: defaultStyle,
            });

            // 将图层添加到地图
            map.value.addLayer(vectorLayer)
    });

    map.value.on('click', function (evt) {
        let featureFound = false; // Flag to indicate if a feature is found
        map.value.forEachFeatureAtPixel(evt.pixel, function (feature) {
            if (!featureFound && (feature.getGeometry().getType() === 'Polygon' || feature.getGeometry().getType() === 'MultiPolygon')) {
                // 获取Feature的名字和数据
                const name = feature.get('name'); // 获取卫星名字
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
    restoreSelections();
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
    top: 21vh;
    /* 放到底部 */
    left: 0;
    /* 放到右边 */
    display: flex;
    /* 使用flex布局 */
    flex-direction: row;
    /* 子元素水平排列 */
    align-items: center;
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
.overview-map {
  position: absolute;
  bottom: 7vh;
  right: 0;
  height: 150px;
  width: 150px;
  z-index: 1000;
}
</style>