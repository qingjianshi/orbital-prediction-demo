import warnings
import math
import requests
from shapely import wkt

# 例如，忽略所有的运行时警告
warnings.filterwarnings("ignore")
from sgp4.api import Satrec
import matplotlib.pyplot as plt
from astropy.time import Time
from astropy.coordinates import CartesianDifferential, CartesianRepresentation
from astropy.coordinates import TEME, ITRS
from astropy import units as u
from datetime import datetime, timedelta
from pytz import timezone
import pandas as pd
import re
from timezonefinder import TimezoneFinder
from sqlalchemy.orm import declarative_base
import pytz
from sqlalchemy import text
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, TIMESTAMP, Float
import geopandas as gpd
from shapely.geometry import Point, LineString,MultiLineString
from geoalchemy2 import Geometry
from pyproj import Transformer
class OrbitCal():
    def __init__(self,satellite_width,timezone_finder):
        self.satellite_width=satellite_width
        self.timezone_finder=timezone_finder


    def crawl_satellite_data(self,start_time_interval,end_time_interval,delete_data):
        # 计算当前utc时间，设置时间段和间隔
        now = datetime.now()
        utc_now = now.astimezone(timezone('UTC'))
        tstart = utc_now + timedelta(days=start_time_interval)
        stop_offset = '86400s'
        freq = '5min'
        end_date = tstart + timedelta(days=end_time_interval)
        day = 0
        while tstart < end_date:
            day = day + 1
            # tstart = tstart.replace(hour=0, minute=0, second=0, microsecond=0)+pd.to_timedelta('86400s')
            tstart = tstart + pd.to_timedelta('86400s')
            tstop = tstart + pd.to_timedelta(stop_offset)
            times = pd.date_range(tstart, tstop, freq=freq)
            Name = []
            Line1 = []
            Line2 = []

            with open("tle_para_updateday.txt", "r", encoding='utf-8') as file:
                lines = file.readlines()

            # 处理每三行的数据，并添加到相应的列表中
            for i in range(0, len(lines), 3):
                dfs = []
                name = lines[i].strip().replace(" ", "")  # 处理第一行，并移除换行符和空格
                line1 = lines[i + 1].strip()  # 处理第二行，并移除换行符
                line2 = lines[i + 2].strip()  # 处理第三行，并移除换行符
                width = self.satellite_width[name]
                Name.append(name)
                Line1.append(line1)
                Line2.append(line2)
                satellite = Satrec.twoline2rv(line1, line2)
                geodetic_orbit = []
                Lines = []
                Line_part = []
                for time in times:
                    t = Time(time)
                    # 设定速度
                    error_code, teme_p, teme_v = satellite.sgp4(t.jd1, t.jd2)
                    teme_p = CartesianRepresentation(teme_p * u.km)  # 将位置表示为千米单位的卫星TEME坐标。
                    teme_v = CartesianDifferential(teme_v * u.km / u.s)  # 速度表示为千米/秒单位的卫星TEME坐标。
                    teme = TEME(teme_p.with_differentials(teme_v), obstime=t)  # TEME坐标系对象，该对象包含卫星的位置和速度信息，并且与给定的时间相关联。

                    # Convert to ITRS and geodetic coordinates
                    itrs = teme.transform_to(ITRS(obstime=t))
                    geodetic = itrs.earth_location.to_geodetic()
                    target_timezone_str = self.timezone_finder.timezone_at(lng=geodetic.lon.value,
                                                                      lat=geodetic.lat.value)

                    parsed_time = time
                    target_timezone = pytz.timezone(target_timezone_str)
                    local_time = parsed_time.astimezone(target_timezone)
                    local_time=datetime.strptime(str(local_time), "%Y-%m-%d %H:%M:%S.%f%z")
                    geodetic_orbit.append({'time_utc': time,
                                           'lat': geodetic.lat.value,
                                           'lon': geodetic.lon.value,
                                           'time_local': local_time,
                                           'time_local_day': local_time.strftime('%Y-%m-%d'),
                                           })
                    Lines.append(Point(geodetic.lon.value, geodetic.lat.value))
                    df = pd.DataFrame(geodetic_orbit)
                    df.index = df['time_utc']
                    df['name'] = name.strip().replace(" ", "")
                    df['time_utc'] = pd.to_datetime(df['time_utc'])
                    # df['time_iso'] = df['time_utc'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    df.drop_duplicates(inplace=True)
                    dfs.append(df)
                crossing_indices = [i for i in range(1, len(Lines)) if abs(Lines[i].x - Lines[i - 1].x) > 180]
                # 如果有穿越点，分割线段
                if crossing_indices:
                    last_index = 0
                    for index in crossing_indices:
                        # 创建当前分段的LineString并添加到列表中
                        line_part = Lines[last_index:index]
                        if len(line_part) >= 2:
                            Line_part.append(LineString(line_part))
                        last_index = index
                    # 添加最后一个分段
                    line_part = Lines[last_index:]
                    if len(line_part) >= 2:
                        Line_part.append(LineString(line_part))
                else:
                    # 如果没有穿越点，整个Lines是一个线段
                    Line_part.append(LineString(Lines))
                multi_line = MultiLineString(Line_part)
                # 创建一个图和一个坐标轴
                fig, ax = plt.subplots()

                # 遍历MultiLineString对象中的每个LineString
                for line in multi_line.geoms:
                    # 分别得到LineString的x坐标和y坐标
                    x, y = line.xy
                    # 绘制LineString
                    ax.plot(x, y)

                # 设置坐标轴的比例相同
                ax.set_aspect('equal')

                # 显示图形
                plt.show()
                all_data = pd.concat(dfs, ignore_index=True)
                all_data.drop_duplicates(inplace=True)
                all_data.reset_index(drop=True, inplace=True)
                all_data['geometry'] = multi_line.buffer(2,cap_style=2)
                # 创建Transformer对象 - 从WGS84到Web Mercator
                transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
                points=[]
                for j in range(len(all_data)):
                    # 一次调用转换函数获取x，y坐标
                    x, y = all_data['lon'].iloc[j], all_data['lat'].iloc[j]
                    # 创建一个新的Point对象并添加到列表中
                    points.append(Point(x, y))
                # 初始化一个空列表来存储转换后的点
                # transformed_points = []
                # for j in range(len(all_data)):
                #     # 一次调用转换函数获取x，y坐标
                #     x, y = transformer.transform(all_data['lat'].iloc[j], all_data['lon'].iloc[j])
                #     # 创建一个新的Point对象并添加到列表中
                #     transformed_points.append(Point(x, y))
                gdf = gpd.GeoDataFrame(all_data,crs='EPSG:4326', geometry='geometry')
                # gdf.plot()
                # plt.show()
                metadata = MetaData()
                Base = declarative_base()

                class OrbitPrediction(Base):
                    __tablename__ = 'test'
                    id = Column(Integer, primary_key=True, autoincrement=True)
                    name = Column(Text)
                    time_utc = Column(TIMESTAMP(timezone=False))
                    time_local_day = Column(TIMESTAMP(timezone=False))
                    lat = Column(Float)
                    lon = Column(Float)
                    time_local = Column(TIMESTAMP(timezone=False))
                    geometry = Column(Geometry(srid=4326))

                # Create the table if it doesn't exist
                Base.metadata.create_all(self.engine, checkfirst=True)
                with self.engine.connect() as connection:
                    gdf.to_postgis('test', con=connection, schema='postgres', if_exists='append',
                                   index=False)
                    print(f"第{tstart}天,{name}文件数据已成功添加到数据库表中")
        if delete_data:
            today = datetime.today().date()  # 获取今天的日期
            delete_query = text(
                f"DELETE FROM test WHERE time_utc <'{today}'")
            self.engine.connect().execute(delete_query)
            print(f'已经删除{today}之前的数据')

    def CreateConnection(self,database_name,database_username,database_password,database_host,database_post):
        url = 'postgresql://{}:{}@{}:{}/{}'
        url=url.format(database_username,database_password,database_host,database_post,database_name)
        engine = create_engine(url)
        conn=engine.connect()
        self.engine=engine
        return engine

if __name__ == "__main__":
    pd.set_option('display.encoding', 'utf-8')
    satellite_width = {'ZIYUAN1-02C(ZY1-02C)': 60000, 'ZIYUAN3-1(ZY3-1)': 50000, 'ZIYUAN3-2(ZY3-2)': 50000,
                       'ZY-102D': 115000, 'ZY-102E': 115000, 'GAOFEN1': 60000, 'GAOFEN1-02': 60000, 'GAOFEN1-03': 60000,
                       'GAOFEN1-04': 60000, 'GAOFEN2': 45000, 'GAOFEN3': 130000, 'GAOFEN3-02': 130000,
                       'GAOFEN3-03': 650000, 'GAOFEN6': 90000, 'GAOFEN7': 20000,
                       'HAIYANG-1B': 512000,
                       'HAIYANG-1C': 2900000, 'HAIYANG-1D': 2900000,'GAOFEN5-01': 60000,
                       'GAOFEN5-01A': 60000, 'GAOFEN5-02': 60000}
    OrbitCalTest=OrbitCal(satellite_width=satellite_width,timezone_finder=TimezoneFinder())
    engine=OrbitCalTest.CreateConnection(database_name='postgres', database_username='postgres', database_password='ecnu2024',
                              database_host='49.52.31.105', database_post='5434')
    # engine= CreateConnection(database_name='postgres', database_username='postgres', database_password='sunjin123',database_host='49.52.31.105',database_post='5432')
    OrbitCalTest.crawl_satellite_data(start_time_interval=-1,end_time_interval=7,delete_data=False)
