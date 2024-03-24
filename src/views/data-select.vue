<template>
    <div v-show="activeTab === 'prediction'" id="cesiumcontainer" class="container">
        <div class="title">
            <h1>卫星轨道预测及可视化系统</h1>
        </div>
        <div class="select_box" :style="selectBoxStyles">
            <div class="buttons">
                <el-button @click="changeTab('prediction')"
                    :style="{ width: '50%', 'background-color': activeTab === 'prediction' ? '#283848' : '#2c3e50' }">轨道模拟</el-button>
                <el-button @click="changeTab('transit')"
                    :style="{ width: '50%', 'background-color': activeTab === 'transit' ? '#283848' : '#2c3e50' }">过境预测</el-button>
            </div>
            <div v-if="activeTab === 'prediction'" style="margin-top: 5vh;">
                <p style="color: aliceblue;z-index: 1000;font-weight: bold; text-align: center;font-size: 18px">
                    卫星轨道预测与可视化</p>
                <div style="display: flex; flex-direction: column;">
                    <label for="timeRange"
                        style="font-size: 16px;margin-top: 10px;margin-bottom: 10px;background-color:#283848;">开始和结束时间</label>
                    <div class="quick-select" style="margin-top: 10px;margin-bottom: 10px;">
                        <el-button @click="selecthour">未来一小时</el-button>
                        <el-button @click="selectday">未来一天</el-button>
                        <el-button @click="select3day">未来三天</el-button>
                    </div>
                    <el-date-picker v-model="timeRange" type="datetimerange" range-separator="至"
                        start-placeholder="开始日期" end-placeholder="结束日期" :shortcuts="shortcuts"
                        style="width: 23vw;"></el-date-picker>
                    <label for="selectedsatellite"
                        style="font-size: 16px;margin-top: 10px;margin-bottom: 10px;background-color:#283848; width: 100%;">卫星选择</label>
                </div>

                <div class="checkbox-container">
                    <el-checkbox-group v-model="selectedsatellite">
                        <el-checkbox v-for="satellite in satellite_list" :label="satellite" :key="satellite"
                            class="el-checkbox-button">
                            {{ satellite }}
                        </el-checkbox>
                    </el-checkbox-group>
                </div>

                <div class="buttons">
                    <el-button @click="reset" :style="{ width: '50%' }">重置</el-button>
                    <el-button @click="confirm" :style="{ width: '50%' }">确认</el-button>
                </div>
            </div>
        </div>
        <div class="geo_info" v-if="status.viewHeight && status.lot && status.lat">
            <p>视高: {{ status.viewHeight }}m</p>
            <p>经度: {{ status.lot }}°</p>
            <p>纬度: {{ status.lat }}°</p>
        </div>
        <div class="collapse-arrow" @click="toggleSelectBox" :style="arrow">
            <el-icon size='30px'>
                <ArrowRight v-if="isCollapsed" />
                <ArrowLeft v-else />
            </el-icon>
        </div>
    </div>

    <div ref="mapContainer" v-show="activeTab === 'transit'" class="map-container">
        <div class="title">
            <h1>卫星轨道预测及可视化系统</h1>
        </div>
        <div class="select_box" :style="selectBoxStyles">
            <div class="buttons">
                <el-button @click="changeTab('prediction')"
                    :style="{ width: '50%', 'background-color': activeTab === 'prediction' ? '#283848' : '#2c3e50' }">轨道模拟</el-button>
                <el-button @click="changeTab('transit')"
                    :style="{ width: '50%', 'background-color': activeTab === 'transit' ? '#283848' : '#2c3e50' }">过境预测</el-button>
            </div>

            <div v-if="activeTab === 'transit'" style="margin-top: 5vh;">
                <p style="color: aliceblue;z-index: 1000;font-weight: bold; text-align: center;font-size: 18px">
                    卫星过境预测</p>
                <div style="position: relative;display: flex;z-index: 1000;flex-direction:row;width: 25vw;">
                    <el-button @click="change_dataselect_way('drag_box')"
                        :style="{ width: '50%', 'background-color': box_data_select === 'drag_box' ? '#283848' : '#2c3e50' }">地图框选</el-button>
                    <el-button @click="change_dataselect_way('draw_free')"
                        :style="{ width: '50%', 'background-color': box_data_select === 'draw_free' ? '#283848' : '#2c3e50' }">自由绘制</el-button>
                </div>
                <div v-if="box_data_select === 'drag_box'" style="width: 100%;margin-top: 10px;">
                    <el-cascader v-model="selectedData" :options="options" @change="handleChange" placeholder="请选择地区"
                        :props="cascaderProps" clearable style="width: 100%">
                    </el-cascader>
                </div>
                <div v-if="box_data_select === 'draw_free'" style="display:flex;margin-top: 10px;">
                    <el-tooltip class="item" effect="dark" content="绘制一个多边形,点击左键开始,绘制三个以上点后,点击右键结束" placement="top">
                        <el-button @click="startDrawing('Polygon')" style="width: 33%;">绘制面</el-button>
                    </el-tooltip>
                    <el-tooltip class="item" effect="dark" content="绘制一个矩形,点击左键开始,拖动到指定位置,点击左键结束" placement="top">
                        <el-button @click="startDrawing('Rectangle')" style="width: 33%;">绘制矩形</el-button>
                    </el-tooltip>
                    <el-button @click="draw_del" style="width: 33%;">清空选择</el-button>
                </div>
                <div style="display: flex; flex-direction: column;position:relative;">
                    <label for="timeRange2"
                        style="font-size: 16px;margin-top: 10px;margin-bottom: 10px;background-color:#283848;">开始和结束时间</label>
                    <div class="quick-select" style="margin-top: 10px;margin-bottom: 10px;">
                        <el-button @click="selecthour2">未来一周</el-button>
                        <el-button @click="selectday2">未来一月</el-button>
                        <el-button @click="select3day2">未来一年</el-button>
                    </div>
                    <el-date-picker v-model="timeRange2" type="datetimerange" range-separator="至"
                        start-placeholder="开始日期" end-placeholder="结束日期" style="width: 23vw;"></el-date-picker>
                </div>

                <div class="checkbox-container">
                    <el-checkbox-group v-model="selectedsatellite2">
                        <el-checkbox v-for="satellite in satellite_list" :label="satellite" :key="satellite"
                            class="el-checkbox-button">
                            {{ satellite }}
                        </el-checkbox>
                    </el-checkbox-group>
                </div>
                <div class="buttons">
                    <el-button @click="reset2" :style="{ width: '50%' }">重置</el-button>
                    <el-button @click="confirm2" :style="{ width: '50%' }">确认</el-button>
                </div>
            </div>
        </div>
        <div id="mouse-position" class="mouse-position"></div>
        <div class="collapse-arrow" @click="toggleSelectBox" :style="arrow">
            <el-icon size='30px'>
                <ArrowRight v-if="isCollapsed" />
                <ArrowLeft v-else />
            </el-icon>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue';
import * as Cesium from 'cesium';
import CesiumNavigation from 'cesium-navigation-es6';
import axios from 'axios';
import { ElDatePicker, ElCheckbox, ElCheckboxGroup, ElButton, ElMessage, ElCascader } from 'element-plus';
import { useRouter } from 'vue-router';
import { ArrowRight, ArrowLeft } from '@element-plus/icons-vue';
import 'element-plus/theme-chalk/dark/css-vars.css'
import 'ol/ol.css';
import { Map, View } from 'ol';
import { Tile as TileLayer } from 'ol/layer';
import XYZ from 'ol/source/XYZ';
import { Draw } from 'ol/interaction';
import { Vector as VectorLayer } from 'ol/layer';
import { Vector as VectorSource } from 'ol/source';
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style';
import { createBox } from 'ol/interaction/Draw';
import { toLonLat } from 'ol/proj';
import { defaults as defaultControls, FullScreen, ScaleLine, OverviewMap, ZoomSlider, Rotate } from 'ol/control';
const mapContainer = ref(null);
const map = reactive({ value: null });
const vectorSource = new VectorSource();
const drawStyle = new Style({
    fill: new Fill({
        color: 'rgba(255, 255, 255, 0.2)',
    }),
    stroke: new Stroke({
        color: '#ffcc33',
        width: 2,
    }),
});
const router = useRouter();
const isCollapsed = ref(false); // 使用ref创建响应式数据
const timeRange = ref([]);
const timeRange2 = ref([]);
const selectedsatellite = ref([]);
const selectedsatellite2 = ref([]);
const satellite_list = ref([]);
const orbit_data = ref([]);
const orbit_data2 = ref([]);
const select_box_data = ref({ geometry: null });
const activeTab = ref('prediction');
const box_data_select = ref('drag_box');
let drawInteraction;
const viewer = ref(null);
const default_orbit_data = ref(null);
const currentTime = ref(new Date());
const nextDayTime = ref(new Date(currentTime.value.getTime() + 60 * 60 * 1000));
const availability = ref(null);
const orientation = ref(null);
const satellitePositions = {};
const positions = ref([]);
const position = ref([]);
const position2 = ref([]);
const orbitPolylines = {};
const aircraftEntitys = {};
const labels = {};
const satelliteEntities = ref({});
const selectedData = ref([]);
const status = reactive({
    viewHeight: '',
    lot: '',
    lat: '',
});
const options = ref([
    {
        value: '中国',
        label: '中国',
        children: []
    }
]);

const cascaderProps = {
    value: 'value',
    label: 'label',
    children: 'children',
    checkStrictly: true, // 非严格的父子节点选择关系
};

const apiEndpoint = 'https://api-orbital.remotesensing.sh.cn/remotesensing/region_res';

// 根据选择的值获取下一个级别的选项
async function fetchOptions(value, level) {
    try {
        const response = await axios.get(`${apiEndpoint}/${value}`);
        console.log(response.data)
        if (level === 1) {
            options.value[0].children = response.data.data.map(province => ({
                value: province, // 省份代码作为值
                label: province, // 省份名称作为标签
                children: [] // 为市级数据预留空数组
            }));
        } else if (level === 2) {
            const province = options.value[0].children.find(p => p.value === value);
            if (province) {
                province.children = response.data.data.map(city => ({
                    value: city, // 市级代码作为值
                    label: city, // 市级名称作为标签
                }));
            }
        }
    } catch (error) {
        console.error('Error fetching options:', error);
    }
}

const handleChange = (value) => {
    if (value){
    const level = value.length;
    console.log(value);
    console.log(level);
    if (level <= 2) {
        fetchOptions(value[value.length - 1], level);
        select_box_data.value.geometry = value[value.length - 1];
        console.log(select_box_data.value.geometry)
    } else if (level === 3) {
        console.log(value[value.length - 1])
        select_box_data.value.geometry = value[value.length - 1];
        console.log(select_box_data.value.geometry)
    }
}};


// 切换标签页的函数
const changeTab = (tab) => {
    activeTab.value = tab;
    draw_del();
};

const toggleSelectBox = () => {
    isCollapsed.value = !isCollapsed.value; // 修改响应式数据的值
};

const selectBoxStyles = computed(() => ({
    transition: 'width 0.5s',
    marginTop: '15vh',
    width: isCollapsed.value ? '0' : '25vw',
    overflow: isCollapsed.value ? 'hidden' : 'visible', // 当折叠时隐藏内容
}));

const arrow = computed(() => ({
    marginLeft: isCollapsed.value ? '0' : '25vw',
}));

const change_dataselect_way = (tab) => {
    box_data_select.value = tab;
    reset2();
    selectedData.value = [];
};


const vector = new VectorLayer({
    source: new VectorSource(),
});

function draw_del() {
    // 这里应该是您已有的移除当前所有交互的逻辑
    const interactions = map.value.getInteractions().getArray();
    interactions.forEach((interaction) => {
        if (interaction instanceof Draw) {
            map.value.removeInteraction(interaction);
        }
    });
    // 同时也清除矢量图层中的要素
    vector.getSource().clear();
    select_box_data.value.geometry = null;
}

function startDrawing(type) {
    draw_del(); // 清除之前的绘制交互
    let geometryFunction;
    if (type === 'Rectangle') {
        geometryFunction = createBox();
    } else {
        geometryFunction = undefined; // 多边形不需要特殊的几何函数
    }

    drawInteraction = new Draw({
        source: vector.getSource(), // 使用矢量源
        type: type === 'Rectangle' ? 'Circle' : 'Polygon',
        geometryFunction: geometryFunction,
        style: drawStyle, // 应用样式
    });

    map.value.addInteraction(drawInteraction);

    drawInteraction.on('drawend', event => {
        const feature = event.feature;
        vector.getSource().addFeature(feature); // 将绘制的要素添加到矢量源

        if (!map.value.getLayers().getArray().includes(vector)) {
            map.value.addLayer(vector); // 更正后的方法
        }

        const geometry = feature.getGeometry();
        let coordinates;
        let geometryString;

        // 根据绘制的类型处理坐标数据
        if (type === 'Rectangle') {
            // 矩形的几何类型是多边形，其坐标数组是多层嵌套的
            coordinates = geometry.getCoordinates()[0];
            geometryString = `POLYGON((${coordinates.map(coord => toLonLat(coord).join(' ')).join(',')}))`;
        } else if (type === 'Polygon') {
            coordinates = geometry.getCoordinates()[0];
            geometryString = `POLYGON((${coordinates.map(coord => toLonLat(coord).join(' ')).join(',')}))`;
        }

        select_box_data.value.geometry = geometryString;
        console.log('Finished drawing:', select_box_data.value);
        // 绘制结束后，移除交互
        vector.getSource().clear();
    });
}

const get_satellite_list = async () => {
    try {
        const response = await axios.get('https://api-orbital.remotesensing.sh.cn/remotesensing/orbitlist_res/');

        // 创建一个映射以将汉字数字转换为阿拉伯数字
        const chineseToNumber = {
            '一': 1,
            '二': 2,
            '三': 3,
            '四': 4,
            '五': 5,
            '六': 6,
            '七': 7,
            '八': 8,
            '九': 9,
            '十': 10,
            // ...根据需要添加更多的映射
        };

        // 定义一个函数来将汉字数字转换为阿拉伯数字
        const chineseNumberToArabic = (chineseNumber) => {
            return chineseToNumber[chineseNumber] || 0;
        };

        // 排序逻辑
        response.data.satellite_list.sort((a, b) => {
            const aMatch = a.match(/^(\D{2})([\u4e00-\u9fa5])/);
            const bMatch = b.match(/^(\D{2})([\u4e00-\u9fa5])/);

            if (aMatch && bMatch) {
                const aPrefix = aMatch[1];
                const bPrefix = bMatch[1];
                const aNumber = chineseNumberToArabic(aMatch[2]);
                const bNumber = chineseNumberToArabic(bMatch[2]);

                if (aPrefix === bPrefix) {
                    return aNumber - bNumber;
                } else {
                    return aPrefix.localeCompare(bPrefix);
                }
            } else {
                // 如果格式不匹配，则回退到基本字符串比较
                return a.localeCompare(b);
            }
        });
        satellite_list.value = response.data.satellite_list;
    } catch (error) {
        console.error('Error fetching orbits:', error);
    }
};


const shortcuts = [
    {
        text: '未来一小时',
        value: () => {
            const end = new Date()
            const start = new Date()
            end.setTime(start.getTime() + 3600 * 1000)
            return [start, end]
        },
    },
    {
        text: '未来一天',
        value: () => {
            const end = new Date();
            const start = new Date();
            end.setTime(start.getTime() + 3600 * 1000 * 24);
            return [start, end];
        }
    },
    {
        text: '未来三天',
        value: () => {
            const end = new Date()
            const start = new Date()
            end.setTime(start.getTime() + 3600 * 1000 * 24 * 3)
            return [start, end]
        },
    },
]

const selecthour = () => {
    const end = new Date();
    const start = new Date();
    end.setTime(start.getTime() + 3600 * 1000);
    timeRange.value = [start, end];

};

const selectday = () => {
    const end = new Date();
    const start = new Date();
    end.setTime(start.getTime() + 3600 * 1000 * 24);
    timeRange.value = [start, end];
};

const select3day = () => {
    const end = new Date();
    const start = new Date();
    end.setTime(start.getTime() + 3600 * 1000 * 24 * 3);
    timeRange.value = [start, end];
}

const selecthour2 = () => {
    const end = new Date();
    const start = new Date();
    end.setTime(start.getTime() + 7 * 24 * 3600 * 1000);
    timeRange2.value = [start, end];

};

const selectday2 = () => {
    const end = new Date();
    const start = new Date();
    end.setTime(start.getTime() + 3600 * 1000 * 24 * 30);
    timeRange2.value = [start, end];
};

const select3day2 = () => {
    const end = new Date();
    const start = new Date();
    end.setTime(start.getTime() + 3600 * 1000 * 24 * 365);
    timeRange2.value = [start, end];
}

const reset = () => {
    timeRange.value = [];
    selectedsatellite.value = [];
    orbit_data.value = [];
};

const reset2 = () => {
    draw_del();
    selectedData.value = [];
    selectedsatellite2.value = [];
    if (timeRange2) {
        timeRange2.value = [];
    }
    orbit_data2.value = [];
};

const confirm = async () => {
    if (timeRange.value.length !== 2) {
        ElMessage.warning('请选择时间');
        return;
    }
    if (selectedsatellite.value.length <= 0) {
        ElMessage.warning('请选择卫星');
        return;
    }

    // 将UTC时间转换为目标时区的时间，这里减去8小时
    const timeStart = new Date(timeRange.value[0]).toISOString();
    const timeEnd = new Date(timeRange.value[1]).toISOString();

    // 根据需要调整时间
    const offsetMs = 8 * 60 * 60 * 1000; // 8小时的毫秒数
    const timeStartAdjusted2 = new Date(new Date(timeStart).getTime() + offsetMs).toISOString();
    const timeEndAdjusted2 = new Date(new Date(timeEnd).getTime() + offsetMs).toISOString();

    const payload = {
        satellite: selectedsatellite.value,
        time_start: timeStart,
        time_end: timeEnd,
    };

    const payload2 = {
        satellite: selectedsatellite.value,
        time_start: timeStartAdjusted2,
        time_end: timeEndAdjusted2,
    };
    try {
        const response = await axios.post('https://api-orbital.remotesensing.sh.cn/remotesensing/orbit_res/', payload);
        orbit_data.value = response.data;
        localStorage.setItem('orbitData', JSON.stringify(orbit_data.value));
        localStorage.setItem('payload2', JSON.stringify(payload2));
        router.push({
            path: '/orbit_prediction',
        });
    } catch (error) {
        console.error('Error posting data:', error);
    }
    saveSelections(); // 保存选择
};

const confirm2 = async () => {
    let payload;
    let payload2;
    console.log(select_box_data.value.geometry)
    if (select_box_data.value.geometry === null || select_box_data.value.geometry.length < 3) {
        ElMessage.warning('请选择正确区域');
        return;
    }
    if (timeRange2.value.length !== 2) {
        ElMessage.warning('请选择时间');
        return;
    }
    else {
        // 将UTC时间转换为目标时区的时间，这里减去8小时
        const timeStart = new Date(timeRange2.value[0]).toISOString();
        const timeEnd = new Date(timeRange2.value[1]).toISOString();
        // 根据需要调整时间
        const offsetMs = 8 * 60 * 60 * 1000; // 8小时的毫秒数
        const timeStartAdjusted2 = new Date(new Date(timeStart).getTime() + offsetMs).toISOString();
        const timeEndAdjusted2 = new Date(new Date(timeEnd).getTime() + offsetMs).toISOString();
        payload2 = {
            area: select_box_data.value.geometry,
            time_start: timeStartAdjusted2,
            time_end: timeEndAdjusted2
        }
        localStorage.setItem('select_area', JSON.stringify(payload2));
        if (box_data_select.value === 'draw_free') {
            payload = {
                geometry: select_box_data.value.geometry,
                time_start: timeStart,
                time_end: timeEnd,
                satellite: selectedsatellite2.value,
            };
        }
        else {
            payload = {
                county: select_box_data.value.geometry,
                time_start: timeStart,
                time_end: timeEnd,
                satellite: selectedsatellite2.value,
            };
        }
    }
    try {
        console.log(payload)
        const response = await axios.post('https://api-orbital.remotesensing.sh.cn/remotesensing/orbit_res/', payload);
        orbit_data2.value = response.data;
        console.log(orbit_data2.value);
        localStorage.setItem('orbitData2', JSON.stringify(orbit_data2.value));
        router.push({
            path: '/orbit_transit',
        });
    } catch (error) {
        console.error('Error posting data:', error);
    }
};

const saveSelections = () => {
    const selections = {
        timeRange: timeRange.value,
        selectedsatellite: selectedsatellite.value,
    };
    localStorage.setItem('userSelections', JSON.stringify(selections));
};

const restoreSelections = () => {
    const storedSelections = localStorage.getItem('userSelections');
    if (storedSelections) {
        const selections = JSON.parse(storedSelections);
        timeRange.value = selections.timeRange;
        selectedsatellite.value = selections.selectedsatellite;
    }
};
const createPositionData = (data, key) => {
    data.sort((a, b) => {
        return new Date(a.time_iso) - new Date(b.time_iso);
    });
    const one_position = [];
    const position_ground1 = [];
    const orbit_time = []
    const properties = {
        property: new Cesium.SampledPositionProperty(),
        property2: new Cesium.SampledPositionProperty()
    };
    satellitePositions[key] = { property: new Cesium.SampledPositionProperty(), property2: new Cesium.SampledPositionProperty() };
    data.forEach((item) => {

        const time = Cesium.JulianDate.fromIso8601(item.time_iso);
        const lon = item.lon;
        const lat = item.lat;
        const height = item.height;
        const position = Cesium.Cartesian3.fromDegrees(lon, lat, height);
        orbit_time.push(time);
        position_ground1.push(lon, lat);
        one_position.push(position);
        properties.property.addSample(time, position);
        const position2 = Cesium.Cartesian3.fromDegrees(lon, lat, 0);
        properties.property2.addSample(time, position2);
        satellitePositions[key] = properties; // 存储卫星位置信息
        positions.value.push(position);
    });
    return { properties, one_position, position_ground1, satellitePositions, orbit_time };
};
watch([timeRange, selectedsatellite], () => {
    saveSelections(); // 当时间范围或选定的卫星更改时保存
    console.log(selectedsatellite.value)
});

const get_default_orbit_data = async () => {

    const payload = {
        satellite: [
            "高分一号03星",
            "高分一号"
        ],
        time_start: currentTime.value.toISOString(),
        time_end: nextDayTime.value.toISOString(),
    };
    console.log(payload);
    try {
        const response = await axios.post('https://api-orbital.remotesensing.sh.cn/remotesensing/orbit_res/', payload);
        default_orbit_data.value = response.data;
        console.log(default_orbit_data.value);
        //显示渲染轨道等
        for (const key in default_orbit_data.value) {
            console.log('111111')
            const orbit_data = default_orbit_data.value[key]
            console.log(orbit_data)
            const { properties, one_position } = createPositionData(orbit_data['orbit'], key);
            position.value = properties.property;
            position2.value = properties.property2;
            const firstTimeStr = orbit_data['orbit'][0].time_iso;
            const lastTimeStr = orbit_data['orbit'][orbit_data['orbit'].length - 1].time_iso;
            const start = Cesium.JulianDate.fromIso8601(firstTimeStr);
            const stop = Cesium.JulianDate.fromIso8601(lastTimeStr);
            viewer.value.clock.startTime = start.clone();
            viewer.value.clock.stopTime = stop.clone();
            viewer.value.clock.currentTime = start.clone();
            viewer.value.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
            viewer.value.clock.multiplier = 1;
            viewer.value.timeline.zoomTo(start, stop);
            availability.value = new Cesium.TimeIntervalCollection([
                new Cesium.TimeInterval({
                    start: start,
                    stop: stop
                })
            ]);
            orientation.value = new Cesium.VelocityOrientationProperty(
                position.value
            );
            orbitPolylines[orbit_data['info'].chinese_name] = viewer.value.entities.add({
                show: true,
                name: orbit_data['info'].chinese_name,
                polyline: {
                    positions: one_position,
                    width: 2,
                    material: new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString(orbit_data['info'].color)),
                }
            });
            const aircraftModelUrl = 'satellite003.gltf';
            aircraftEntitys[orbit_data['info'].chinese_name] = viewer.value.entities.add({
                show: true,
                name: orbit_data['info'].chinese_name,
                position: position.value,
                orientation: new Cesium.VelocityOrientationProperty(position.value),
                model: {
                    uri: aircraftModelUrl,
                    minimumPixelSize: 5000,
                    maximumScale: 50000,
                    color: Cesium.Color.BLACK,
                }
            });
            satelliteEntities.value[orbit_data['info'].chinese_name] = aircraftEntitys[key];

            labels[orbit_data['info'].chinese_name] = viewer.value.entities.add({
                show: true,
                name: orbit_data['info'].chinese_name,
                position: position.value,
                label: {
                    text: orbit_data['info'].chinese_name,
                    showBackground: false,
                    // backgroundColor: Cesium.Color.RED, // 标签背景颜色
                    fillColor: Cesium.Color.white, // 字体颜色
                    font: '30px sans-serif', // 字体大小和样式
                    pixelOffset: new Cesium.Cartesian2(-10, -30),
                },
            });

        }
    } catch (error) {
        console.error('Error posting data:', error);
    }
}
onMounted(() => {
    get_default_orbit_data();
    console.log(default_orbit_data.value)
    viewer.value = new Cesium.Viewer('cesiumcontainer', { shouldAnimate: true });
    // 添加天地图影像注记底图tk=c66498df4ce5b06fa503fa919f7f4195
    viewer.value.imageryLayers.addImageryProvider(new Cesium.WebMapTileServiceImageryProvider({
        url: "https://t0.tianditu.gov.cn/img_w/wmts?tk=9df1e2d38f43b8983357c36603d366e5",
        layer: "img",
        style: "default",
        tileMatrixSetID: "w",
        format: "tiles",
        maximumLevel: 18
    }))
    viewer.value.imageryLayers.addImageryProvider(new Cesium.WebMapTileServiceImageryProvider({
        url: "https://t0.tianditu.gov.cn/cia_w/wmts?tk=9df1e2d38f43b8983357c36603d366e5",
        layer: "cia",
        style: "default",
        tileMatrixSetID: "w",
        format: "tiles",
        maximumLevel: 18
    }))
    viewer.value._cesiumWidget._creditContainer.style.display = "none";
    const options = {};
    options.defaultResetView = viewer.value.camera.flyHome(0);
    options.enableCompass = true;
    options.enableZoomControls = true;
    options.enableDistanceLegend = true;
    options.enableCompassOuterRing = true;
    options.resetTooltip = "重置视图";
    options.zoomInTooltip = "放大";
    options.zoomOutTooltip = "缩小";
    new CesiumNavigation(viewer.value, options);
    // 在这里添加你的屏幕空间事件逻辑
    let handler3D = new Cesium.ScreenSpaceEventHandler(viewer.value.scene.canvas);
    handler3D.setInputAction(function (movement) {
        let pick = new Cesium.Cartesian2(movement.endPosition.x, movement.endPosition.y);
        if (pick) {
            let cartesian = viewer.value.scene.globe.pick(viewer.value.camera.getPickRay(pick), viewer.value.scene);
            if (cartesian) {
                let cartographic = viewer.value.scene.globe.ellipsoid.cartesianToCartographic(cartesian);
                if (cartographic) {
                    let he = Math.sqrt(
                        viewer.value.scene.camera.positionWC.x * viewer.value.scene.camera.positionWC.x +
                        viewer.value.scene.camera.positionWC.y * viewer.value.scene.camera.positionWC.y +
                        viewer.value.scene.camera.positionWC.z * viewer.value.scene.camera.positionWC.z
                    );
                    let he2 = Math.sqrt(
                        cartesian.x * cartesian.x + cartesian.y * cartesian.y + cartesian.z * cartesian.z
                    );
                    let point = [
                        Cesium.Math.toDegrees(cartographic.longitude),
                        Cesium.Math.toDegrees(cartographic.latitude),
                    ];
                    status.viewHeight = (he - he2).toFixed(1);
                    status.lot = point[0].toFixed(6);
                    status.lat = point[1].toFixed(6);
                }
            }
        }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    // 显示帧率
    viewer.value.scene.debugShowFramesPerSecond = true;
    const distanceLegend = document.querySelector('.distance-legend');
    if (distanceLegend) {
        distanceLegend.style.display = 'block'; // 例如，将display属性设置为block
        distanceLegend.style.zIndex = '1000';
        distanceLegend.style.bottom = '15vh';
    }
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

            new VectorLayer({
                source: vectorSource,
                style: drawStyle,
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

    get_satellite_list()
    restoreSelections();
});
</script>

<style scoped>
.map-container {
    height: 98vh;
    position: relative;
    z-index: 1000;
}

.container {
    width: auto;
    height: 98vh;
    position: relative;
}

.geo_info {
    position: absolute;
    bottom: 2vh;
    /* 放到底部 */
    right: 0;
    /* 放到右边 */
    display: flex;
    /* 使用flex布局 */
    flex-direction: row;
    /* 子元素水平排列 */
    align-items: center;
    /* 子元素在交叉轴上居中对齐 */
    font-size: 12px;
    z-index: 1000;

}

.geo_info>p {
    margin-left: 2vw;
    /* 移除默认的外边距 */
    padding: 2px;
    /* 给点内边距 */
    min-width: 12vh;
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

.buttons {
    position: absolute;
    display: flex;
    z-index: 1000;
    margin-top: 10px;
    width: 25vw;
    /* 将子元素横向排列 */
}

/* 添加到 <style scoped> 中 */
.checkbox-container {
    display: flex;
    /* 使用flex布局 */
    flex-direction: column;
    /* 使子元素垂直排列 */
    gap: 5px;
    /* 设置元素之间的间隙 */
    max-height: 30vh;
    /* 设置一个最大高度 */
    overflow-y: auto;
    overflow-x: hidden;
    /* 内容超出时显示滚动条 */
    margin-top: 10px;
    /* 距离上方的距离 */
}

.checkbox-container2 {
    display: flex;
    /* 使用flex布局 */
    flex-direction: column;
    /* 使子元素垂直排列 */
    gap: 5px;
    /* 设置元素之间的间隙 */
    max-height: 30vh;
    /* 设置一个最大高度 */
    overflow-y: auto;
    overflow-x: hidden;
    margin-top: 5vh;
    /* 内容超出时显示滚动条 */
    /* 距离上方的距离 */
}

.checkbox-container .el-checkbox {
    width: 100%;
    /* 设置复选框占满整行 */
    margin-bottom: 5px;
    /* 设置复选框之间的间隙 */
    color: rgb(255, 255, 255);
    /* 设置标签的字体颜色 */
}

.checkbox-container2 .el-checkbox {
    width: 100%;
    /* 设置复选框占满整行 */
    margin-bottom: 5px;
    /* 设置复选框之间的间隙 */
    color: rgb(255, 255, 255);
    /* 设置标签的字体颜色 */
}

.checkbox-container .el-checkbox-button {
    justify-content: flex-start;
    /* 文本靠左对齐 */
}

.checkbox-container2 .el-checkbox-button {
    justify-content: flex-start;
    /* 文本靠左对齐 */
}

.checkbox-container .el-checkbox__label {
    font-size: 14px;
    /* 设置标签的字体大小 */
    color: rgb(255, 255, 255);
    /* 设置标签的字体颜色 */
}

.checkbox-container2 .el-checkbox__label {
    font-size: 14px;
    /* 设置标签的字体大小 */
    color: rgb(255, 255, 255);
    /* 设置标签的字体颜色 */
}

.select_box {
    /* ...其他样式保持不变... */
    background-color: #2c3e50;
    /* 深蓝/灰色背景色，适合白色字体 */
    border-radius: 10px;
    /* 可选：为方框添加圆角 */
}

/* 设置标签和按钮的颜色，以符合深灰色背景 */
.title h1,
p,
label,
.el-checkbox__label {
    color: white;
    /* 白色字体 */
}

.el-cascader .el-input {
    width: 100%
}

/* 设置按钮默认背景颜色 */
.buttons .el-button {
    background-color: #34495e;
    /* 深灰色背景色 */
    color: white;
    /* 白色文字 */
    border: none;
    /* 取消边框 */
}

/* 按钮在鼠标悬停时的状态 */
.buttons .el-button:hover {
    background-color: #4a69bd;
    /* 更亮的蓝色，鼠标悬停时显示 */
}

/* 设置快速选择按钮的默认背景颜色 */
.quick-select .el-button {
    background-color: #34495e;
    color: white;
    border: none;
    width: 30%;
}

/* 快速选择按钮在激活时的样式 */
.quick-select .el-button[aria-pressed='true'] {
    background-color: #4a69bd;
}

/* 根据激活状态设置按钮背景 */
.buttons .el-button[aria-pressed='true'] {
    background-color: #4a69bd;
    /* 选中时使用更鲜明亮的蓝色 */
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

html,
body {
    height: 100vh;
    width: 100vw;
    margin: 0;
    padding: 0;
    overflow: hidden;
}
</style>