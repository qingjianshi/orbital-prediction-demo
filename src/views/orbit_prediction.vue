<template>
    <div id="cesiumcontainer" class="container">
        <div class="title">
            <h1>卫星轨道预测可视化</h1>
        </div>
        <div v-if="orbitData && selectedData" class="selected_info" style="max-height: 15vh;overflow: hidden;overflow-y: scroll;">
            <div style="font-size: 14px;">
                <ul>
                    <li v-for="satellite in selectedData.satellite" :key="satellite">
                        {{ satellite }}
                    </li>
                </ul>
            </div>
            <div style="margin-left: 1vw;font-size: 14px;">
                <p>开始时间: {{ selectedData.time_start }}</p>
                <p>结束时间: {{ selectedData.time_end }}</p>
            </div>
        </div>
        <div v-if="orbitData && selectedData" class="opera_box" :style="selectBoxStyles">
            <p style="background-color:#283848; width: 100%;font-size: 16px;">轨道显示</p>
            <div class="satellite-list" style="max-height: 25vh; overflow: hidden;overflow-y: scroll;">
                <div v-for="(satellite, index) in selectedData.satellite" :key="satellite" class="satellite-item">
                    <div class="radio-group">
                        {{ satellite }}
                        <el-checkbox-group v-model="selectedFeatures[satellite]">
                            <div class="checkbox-row">
                                <el-checkbox :label="`orbit-line-${index}`"
                                    @change="toggleOrbitVisibility(satellite, $event)">轨道线</el-checkbox>
                                <el-checkbox :label="`real-time-box-${index}`"
                                    @change="toggleOrbitVisibility_width(satellite, $event)">幅宽</el-checkbox>
                                <el-checkbox :label="`model-${index}`"
                                    @change="toggleOrbitVisibility_model(satellite, $event)">模型</el-checkbox>
                            </div>
                            <div class="checkbox-row">
                                <el-checkbox :label="`sub-satellite-area-${index}`"
                                    @change="toggleOrbitVisibility_sub_area(satellite, $event)">星下区</el-checkbox>
                                <el-checkbox :label="`real-time-scan-${index}`"
                                    @change="toggleOrbitVisibility_scan(satellite, $event)">实时扫过区域</el-checkbox>
                                <el-checkbox :label="`tag-${index}`"
                                    @change="toggleOrbitVisibility_tag(satellite, $event)">标签</el-checkbox>
                            </div>
                        </el-checkbox-group>

                    </div>
                </div>
            </div>
        </div>
        <div v-if="orbitData && selectedData" class="custom_box" :style="selectBoxStyles">
            <p style="background-color:#283848; width: 100%;font-size: 16px;">播放速率</p>
            <el-button @click="setPlaybackSpeed(1)">1X</el-button>
            <el-button @click="setPlaybackSpeed(5)">5X</el-button>
            <el-button @click="setPlaybackSpeed(30)">30X</el-button>
            <el-button @click="setPlaybackSpeed(60)">60X</el-button>
            <p style="background-color:#283848; width: 100%;font-size: 16px;">观测视角</p>
            <div>
                <el-cascader v-model="cascaderValue" v-if="cascaderOptions.length > 0" :options="cascaderOptions"
                    :props="{ expandTrigger: 'hover' }" @change="handleCascaderChange"></el-cascader>
            </div>
            <div>
                <el-cascader v-if="cascaderOptions_eyes.length > 0" v-model="cascaderValue_eye"
                    :options="cascaderOptions_eyes" :props="{ expandTrigger: 'hover' }"
                    @change="handleEyesViewChange"></el-cascader>
            </div>
            <div>
                <el-button @click="resetCascader">重置视图</el-button>
                <el-button @click="destroy_eye">退出鹰眼图</el-button>
            </div>


        </div>
        <div class="geo_info" v-if="status.viewHeight && status.lot && status.lat">
            <p>视高: {{ status.viewHeight }}m</p>
            <p>经度: {{ status.lot }}°</p>
            <p>纬度: {{ status.lat }}°</p>
        </div>
        <div id="eyecontainer" class="container2" v-show=show_eye>
        </div>
        <div class="collapse-arrow" @click="toggleSelectBox" :style="arrow">
            <el-icon size='30px'>
                <ArrowRight v-if="isCollapsed" />
                <ArrowLeft v-else />
            </el-icon>
        </div>
    </div>
</template>
<script setup>
// 在/orbit_prediction页面的组件中
import { onMounted, ref, reactive, onBeforeUnmount, watch, watchEffect,computed } from 'vue';
import * as Cesium from 'cesium';
import { ElCheckboxGroup, ElCheckbox, ElCascader, ElButton } from 'element-plus';
import CesiumNavigation from 'cesium-navigation-es6';
import { ArrowRight, ArrowLeft } from '@element-plus/icons-vue';
import 'element-plus/theme-chalk/dark/css-vars.css'
const orbitData = ref(null);
const show_eye=ref(false);
const selectedData = ref(null);
const availability = ref(null);
const orientation = ref(null);
const satellitePositions = {};
const playbackSpeed = ref(1);
const positions = ref([]);
const position = ref([]);
const position2 = ref([]);
const orbitPolylines = {};
const aircraftEntitys = {};
const labels = {};
const corridors = {};
const outlineOnlys = {};
const satelliteEntities = ref({});
const corridorEntitys = {};
let viewer;
let viewer_eye;
const infoDialogs = {}; // 创建一个对象来存储卫星信息对话框
const status = reactive({
    viewHeight: '',
    lot: '',
    lat: '',
});
// 存储每个卫星对应的观测角度选择
const cascaderValue = ref(null);
const cascaderValue_eye = ref(null);
// 初始化选中的特征对象，每个卫星对应一个选中特征的数组
const selectedFeatures = reactive({});
const cascaderOptions = ref([]);
const cascaderOptions_eyes = ref([]);
const isCollapsed=ref(false)
const toggleSelectBox = () => {
    isCollapsed.value = !isCollapsed.value; // 修改响应式数据的值
};
const toggleOrbitVisibility = (satellite, checked) => {
    if (orbitPolylines[satellite]) {
        orbitPolylines[satellite].show = checked;
    }
};
const toggleOrbitVisibility_width = (satellite, checked) => {
    if (outlineOnlys[satellite]) {
        outlineOnlys[satellite].show = checked;
    }
};
const toggleOrbitVisibility_model = (satellite, checked) => {
    if (aircraftEntitys[satellite]) {
        aircraftEntitys[satellite].show = checked;
    }
};
const toggleOrbitVisibility_sub_area = (satellite, checked) => {
    if (corridors[satellite]) {
        corridors[satellite].show = checked;
    }
};
const toggleOrbitVisibility_scan = (satellite, checked) => {
    if (corridorEntitys[satellite]) {
        corridorEntitys[satellite].show = checked;
    }
};
const toggleOrbitVisibility_tag = (satellite, checked) => {
    // 检查该卫星的轨道线是否存在
    if (labels[satellite]) {
        // 如果存在，根据复选框的状态设置实体的可见性
        labels[satellite].show = checked;
    }
};
const setPlaybackSpeed = (speedMultiplier) => {
    // 设置播放速率
    playbackSpeed.value = speedMultiplier;
    viewer.clock.multiplier = speedMultiplier;
};

const resetCascader = () => {
    cascaderValue.value = null;
    viewer.camera.flyHome(1);
};

const destroy_eye=()=>{
    show_eye.value=false;
    cascaderValue_eye.value=null;
}
const selectBoxStyles = computed(() => ({
    transition: 'width 0.5s',
    width: isCollapsed.value ? '0' : '25vw',
    overflow: isCollapsed.value ? 'hidden' : 'visible', // 当折叠时隐藏内容
}));
const arrow= computed(() => ({
    marginLeft: isCollapsed.value ? '0' : '25vw',
}));
// 观测角度选择变化时调用的函数
const handleCascaderChange = (value) => {
    const selectedOption = value;
    if (!selectedOption || selectedOption.length === 0) return;

    // 假设entity是你的卫星实体
    const entity = aircraftEntitys[selectedOption[0]];

    if (!entity) return;
    const currentTime = viewer.clock.currentTime;
    const position = entity.position.getValue(currentTime);

    if (!position) return;

    const camera = viewer.camera;
    let offset;
    switch (selectedOption[1]) {
        case 'top':
            offset = new Cesium.HeadingPitchRange(0, -Cesium.Math.PI_OVER_TWO, 15000); // 俯视角度和距离
            break;
        case 'side':
            offset = new Cesium.HeadingPitchRange(0.5, -0.5, 15000); // 侧视角度和距离
            break;
        case 'follow':
            viewer.trackedEntity = entity; // 跟随
            return
    }
    // 瞬间切换到指定卫星的视角
    viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY); // 重置相机变换
    viewer.camera.lookAt(
        position,
        offset
    );
};
// 观测角度选择变化时的函数，添加处理鹰眼视图的逻辑
const handleEyesViewChange = (value) => {
    if (!value || value.length === 0) return;
    show_eye.value=true;
    const entity = aircraftEntitys[value[0]];
    if (!entity) return;

    // 设置鹰眼视图的跟随目标为选中的卫星实体
    viewer_eye.trackedEntity = entity;
    
    // 确保鹰眼视图相机始终指向卫星
    const updateCameraView = () => {
        const currentTime = viewer.clock.currentTime;
        const position = entity.position.getValue(currentTime);
        if (position) {
            const offset = new Cesium.HeadingPitchRange(0, -Cesium.Math.PI_OVER_TWO, 15000);
            viewer_eye.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
            viewer_eye.camera.lookAt(position, offset);
        }
    };

    // 注册一个事件监听器来持续更新鹰眼视图相机
    viewer.clock.onTick.addEventListener(updateCameraView);

    // 存储这个函数，以便之后可以移除事件监听器
    viewer_eye._updateCameraViewCallback = updateCameraView;
};

onMounted(() => {
    viewer = new Cesium.Viewer('cesiumcontainer', { shouldAnimate: true });
    viewer_eye = new Cesium.Viewer('eyecontainer', {
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        baseLayerPicker: false,
        navigationHelpButton: false,
        animation: false,
        timeline: false,
        fullscreenButton: false,
    });
    // 添加天地图影像注记底图
    viewer.imageryLayers.addImageryProvider(new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.gov.cn/img_w/wmts?tk=c66498df4ce5b06fa503fa919f7f4195",
        layer: "img",
        style: "default",
        tileMatrixSetID: "w",
        format: "tiles",
        maximumLevel: 18
    }))
    viewer.imageryLayers.addImageryProvider(new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.gov.cn/cia_w/wmts?tk=c66498df4ce5b06fa503fa919f7f4195",
        layer: "cia",
        style: "default",
        tileMatrixSetID: "w",
        format: "tiles",
        maximumLevel: 18
    }))
    viewer._cesiumWidget._creditContainer.style.display = "none";
    // 添加天地图影像注记底图
    viewer_eye.imageryLayers.addImageryProvider(new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.gov.cn/img_w/wmts?tk=c66498df4ce5b06fa503fa919f7f4195",
        layer: "img",
        style: "default",
        tileMatrixSetID: "w",
        format: "tiles",
        maximumLevel: 18
    }))
    viewer_eye.imageryLayers.addImageryProvider(new Cesium.WebMapTileServiceImageryProvider({
        url: "http://t0.tianditu.gov.cn/cia_w/wmts?tk=c66498df4ce5b06fa503fa919f7f4195",
        layer: "cia",
        style: "default",
        tileMatrixSetID: "w",
        format: "tiles",
        maximumLevel: 18
    }))
    viewer_eye._cesiumWidget._creditContainer.style.display = "none";
    const options = {};
    options.defaultResetView = viewer.camera.flyHome(0);
    options.enableCompass = true;
    options.enableZoomControls = true;
    options.enableDistanceLegend = true;
    options.enableCompassOuterRing = true;
    options.resetTooltip = "重置视图";
    options.zoomInTooltip = "放大";
    options.zoomOutTooltip = "缩小";
    new CesiumNavigation(viewer, options);
    // 在这里添加你的屏幕空间事件逻辑
    let handler3D = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler3D.setInputAction(function (movement) {
        let pick = new Cesium.Cartesian2(movement.endPosition.x, movement.endPosition.y);
        if (pick) {
            let cartesian = viewer.scene.globe.pick(viewer.camera.getPickRay(pick), viewer.scene);
            if (cartesian) {
                let cartographic = viewer.scene.globe.ellipsoid.cartesianToCartographic(cartesian);
                if (cartographic) {
                    let he = Math.sqrt(
                        viewer.scene.camera.positionWC.x * viewer.scene.camera.positionWC.x +
                        viewer.scene.camera.positionWC.y * viewer.scene.camera.positionWC.y +
                        viewer.scene.camera.positionWC.z * viewer.scene.camera.positionWC.z
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
    viewer.scene.debugShowFramesPerSecond = true;
    const distanceLegend = document.querySelector('.distance-legend');
    if (distanceLegend) {
        distanceLegend.style.display = 'block'; // 例如，将display属性设置为block
        distanceLegend.style.zIndex = '1000';
        distanceLegend.style.bottom = '15vh';
    }




    const storedData = localStorage.getItem('orbitData');
    const storedData2 = localStorage.getItem('payload2');
    if (storedData && storedData2) {
        // 将JSON字符串转换回对象
        orbitData.value = JSON.parse(storedData);
        selectedData.value = JSON.parse(storedData2);

        selectedData.value.satellite.forEach((satellite, index) => {
            selectedFeatures[satellite] = [
                `orbit-line-${index}`,
                `model-${index}`,
                `tag-${index}`
            ];
        })
        // 根据更新的selectedData构建级联菜单的选项
        cascaderOptions.value = selectedData.value.satellite.map((satellite) => ({
            value: satellite,
            label: satellite,
            children: [
                { value: 'top', label: '俯视' },
                { value: 'side', label: '侧视' },
                { value: 'follow', label: '跟随' }
            ]
        }));
        cascaderOptions_eyes.value = selectedData.value.satellite.map((satellite) => ({
            value: satellite,
            label: satellite,
            children: [
                { value: 'eyes', label: '鹰眼图' },
            ]
        }));
    }

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
            // 创建 position2
            const position2 = Cesium.Cartesian3.fromDegrees(lon, lat, 0);
            properties.property2.addSample(time, position2);
            satellitePositions[key] = properties; // 存储卫星位置信息
            positions.value.push(position);
        });
        return { properties, one_position, position_ground1, satellitePositions, orbit_time };
    };



    //显示渲染轨道等
    for (const key in orbitData.value) {
        const orbit_data = orbitData.value[key]
        const { properties, one_position, position_ground1, satellitePositions, orbit_time } = createPositionData(orbit_data['orbit'], key);
        position.value = properties.property;
        position2.value = properties.property2;
        const infoDialog = document.createElement("div");
        infoDialog.setAttribute("id", "infoDialog");
        infoDialog.style.display = "none"; // 最初隐藏对话框
        infoDialog.style.position = "absolute";
        infoDialog.style.top = "10px";
        infoDialog.style.left = "10px";
        infoDialog.style.backgroundColor = "white";
        infoDialog.style.padding = "10px";
        infoDialog.style.border = "1px solid #ccc";
        // 将信息对话框添加到 Cesium.Viewer 的容器中
        viewer.container.appendChild(infoDialog);
        infoDialogs[key] = infoDialog; // 为每个卫星存储对应的信息对话框
        const firstTimeStr = orbit_data['orbit'][0].time_iso;
        const lastTimeStr = orbit_data['orbit'][orbit_data['orbit'].length - 1].time_iso;
        const start = Cesium.JulianDate.fromIso8601(firstTimeStr);
        const stop = Cesium.JulianDate.fromIso8601(lastTimeStr);
        viewer.clock.startTime = start.clone();
        viewer.clock.stopTime = stop.clone();
        viewer.clock.currentTime = start.clone();
        viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
        viewer.clock.multiplier = 1;
        viewer.timeline.zoomTo(start, stop);
        availability.value = new Cesium.TimeIntervalCollection([
            new Cesium.TimeInterval({
                start: start,
                stop: stop
            })
        ]);
        orientation.value = new Cesium.VelocityOrientationProperty(
            position.value
        );


        orbitPolylines[orbit_data['info'].chinese_name] = viewer.entities.add({
            show: true,
            name: orbit_data['info'].chinese_name,
            polyline: {
                positions: one_position,
                width: 2,
                material: new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString(orbit_data['info'].color)),
            }
        });
        const aircraftModelUrl = 'satellite003.gltf';
        aircraftEntitys[orbit_data['info'].chinese_name] = viewer.entities.add({
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

        labels[orbit_data['info'].chinese_name] = viewer.entities.add({
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

        outlineOnlys[orbit_data['info'].chinese_name] = viewer.entities.add({
            show: false,
            name: orbit_data['info'].chinese_name,
            position: position2.value,
            orientation: orientation.value, // 将矩形的方向设置为orientation
            plane: {
                plane: new Cesium.Plane(Cesium.Cartesian3.UNIT_Z, 0.0),
                dimensions: new Cesium.Cartesian2(50000, orbit_data['info'].width),
                fill: false,
                outline: true,
                outlineColor: Cesium.Color.RED,
            },
        });

        corridors[orbit_data['info'].chinese_name] = viewer.entities.add({
            show: false,
            corridor: {
                positions: Cesium.Cartesian3.fromDegreesArray(position_ground1),
                material: new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString(orbit_data['info'].color).withAlpha(0.4)),
                width: orbit_data['info'].width,
                clampToGround: true, // 开启贴地
                classificationType: Cesium.ClassificationType.TERRAIN, // 只对地形进行分类
                // classificationType: Cesium.ClassificationType.BOTH, 
                cornerType: Cesium.CornerType.BEVELED,
                height: 1,
            }
        })
        const position_ground = [];
        let lastUpdateTime = null; // 存储上一次更新的时间
        function addPointEntityCallback() {
            const currentTime = viewer.clock.currentTime;

            satellitePositions[key].property.setInterpolationOptions({
                interpolationDegree: 5,
                interpolationAlgorithm: Cesium.HermitePolynomialApproximation
            });
            satellitePositions[key].property2.setInterpolationOptions({
                interpolationDegree: 5,
                interpolationAlgorithm: Cesium.HermitePolynomialApproximation
            });
            const currentPosition = satellitePositions[key].property.getValue(currentTime);
            const currentPosition2 = satellitePositions[key].property2.getValue(currentTime);
            const currentLon = Cesium.Math.toDegrees(Cesium.Cartographic.fromCartesian(currentPosition).longitude);
            const currentLat = Cesium.Math.toDegrees(Cesium.Cartographic.fromCartesian(currentPosition).latitude);
            const currentHeight = Cesium.Cartographic.fromCartesian(currentPosition).height;
            // 创建信息对话框的 HTML 元素
            infoDialogs[key].innerHTML = `
            <div style="color:black;">
              <p>经度: ${currentLon.toFixed(6)}</p>
              <p>纬度: ${currentLat.toFixed(6)}</p>
              <p>高度: ${(currentHeight / 1000).toFixed(3)}千米</p>
              <p>卫星信息：${orbit_data['info'].info}</p>
            </div>
            `;
            // 单击卫星模型时触发的事件
            aircraftEntitys[orbit_data['info'].chinese_name].description = new Cesium.ConstantProperty(infoDialog.innerHTML);
            if (!Cesium.JulianDate.equals(lastUpdateTime, currentTime)) {
                lastUpdateTime = currentTime;
                let index = 1;
                for (let i = 1; i < orbit_time.length; i++) {
                    if (
                        Cesium.JulianDate.secondsDifference(currentTime, orbit_time[i - 1]) > 0 &&
                        Cesium.JulianDate.secondsDifference(currentTime, orbit_time[i]) < 0
                    ) {
                        index = i;
                        break; // 找到匹配项后提前结束循环
                    }
                }
                if (Cesium.JulianDate.secondsDifference(currentTime, stop) < Cesium.JulianDate.secondsDifference(start, stop) / 2000) {
                    if (currentLon !== undefined && currentLat !== undefined) {
                        if (position_ground.length <= 2) {
                            position_ground.length = 0;
                            position_ground.push(position_ground1[0]);
                            position_ground.push(position_ground1[1]);
                            position_ground.push(position_ground1[2]);
                            position_ground.push(position_ground1[3]);
                        }
                        else {
                            if (Cesium.JulianDate.secondsDifference(currentTime, orbit_time[index - 1]) > 0 && Cesium.JulianDate.secondsDifference(currentTime, orbit_time[index]) < 0 && position_ground.length >= 2 + 2 * index) {
                                position_ground[position_ground.length - 2] = currentLon;
                                position_ground[position_ground.length - 1] = currentLat;
                            } else {
                                position_ground.push(currentLon, currentLat);

                            }
                        }
                        return Cesium.Cartesian3.fromDegreesArray(position_ground);
                    }
                } else {
                    position_ground.length = 0;
                }
            }
        }
        viewer.clock.onTick.addEventListener(addPointEntityCallback);

        corridorEntitys[orbit_data['info'].chinese_name] = viewer.entities.add({
            show: false,
            corridor: {
                positions: new Cesium.CallbackProperty(addPointEntityCallback, false),
                width: orbit_data['info'].width,
                cornerType: Cesium.CornerType.BEVELED,
                clampToGround: true, // 开启贴地
                classificationType: Cesium.ClassificationType.TERRAIN, // 只对地形进行分类
                // classificationType: Cesium.ClassificationType.BOTH, 
                height: 1,
                material: new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString(orbit_data['info'].color).withAlpha(0.75))
            }
        });

    }
});
// 在组件即将卸载前移除事件监听器
onBeforeUnmount(() => {
    // 销毁Viewer对象
    if (viewer) {
        viewer.destroy();
        viewer = null;
    }
    if (viewer_eye) {
        viewer_eye.destroy();
        viewer_eye = null;
    }
});

</script>
<style scoped>
.container {
    max-width: 100vw;
    max-height: 100vh;
    position: relative;
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
.container2 {
    width: 25%;
    height: 25%;
    position: absolute;
    right: 0;
    bottom: 10vh;
    z-index: 1000;
}

.opera_box {
    position: absolute;
    background-color: #2c3e50;
    margin-top: 20vh;
    left: 0;
    z-index: 1000;
    width: 25vw;
    font-size: 14px;
    max-height: 35vh;
    overflow: hidden;

}

.custom_box {
    position: absolute;
    background-color: #2c3e50;
    margin-top: 50vh;
    left: 0;
    width: 25vw;
    z-index: 1000;
    font-size: 14px;
    overflow: hidden;
}

.satellite-list {
    display: flex;
    flex-direction: column;
    /* 子元素纵向排列 */
    overflow-y: auto;
    /* 如果内容超出，显示垂直滚动条 */
    max-height: 300px;
    /* 根据需要设置最大高度 */
    border: 1px solid #283848;
    /* 可选，为了更好地看到边界 */
}

.satellite-item {
    padding: 10px;
    /* 或者您喜欢的任何间距 */
    border-bottom: 1px solid #283848;
    /* 每个项之间的分隔线，可选 */
}

.checkbox-row {
    display: flex;
    flex-wrap: nowrap;
    /* 不换行 */
    justify-content: flex-start;
    /* 左对齐 */
    margin-bottom: 5px;
    /* 给行与行之间一些间隔 */
}

/* 如果需要复选框之间有间隔可以添加以下样式 */

.checkbox-row .el-checkbox {
    margin-right: 10px;
    /* 给复选框之间一些间隔 */
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

.title {
    position: absolute;
    color: white;
    z-index: 1000;
}

.geo_info>p {
    margin-left: 2vw;
    /* 移除默认的外边距 */
    padding: 2px;
    /* 给点内边距 */
    min-width: 12vh;
}
</style>