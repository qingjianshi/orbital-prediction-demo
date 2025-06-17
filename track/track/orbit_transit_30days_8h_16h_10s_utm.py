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
from sqlalchemy.orm import sessionmaker
class OrbitCal():
    def __init__(self,satellite_width,timezone_finder):
        self.satellite_width=satellite_width
        self.timezone_finder=timezone_finder


    def crawl_satellite_data(self,start_time_interval,end_time_interval,delete_data,freq):
        # 计算当前utc时间，设置时间段和间隔
        now = datetime.now()
        utc_now = now.astimezone(timezone('UTC')).replace(hour=0, minute=0, second=0, microsecond=0)
        tstart = utc_now + timedelta(days=start_time_interval)
        stop_offset = '86400s'
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
                Lines_day=[]
                Lines_day_part=[]
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
                    local_time=datetime.strptime(str(local_time), "%Y-%m-%d %H:%M:%S%z")
                    if local_time.hour >=8 and local_time.hour <=16:
                        geodetic_orbit.append({'time_utc': time,
                                               'lat': geodetic.lat.value,
                                               'lon': geodetic.lon.value,
                                               'time_local': local_time,
                                               'time_local_day':local_time.strftime('%Y-%m-%d'),
                                               })
                        Lines.append(Point(geodetic.lon.value,geodetic.lat.value))
                        Lines_day.append([time.strftime('%Y-%m-%d'),local_time.strftime('%Y-%m-%d'),(geodetic.lon.value,geodetic.lat.value)])
                    else:
                        if len(Lines)>=2:
                            # 寻找跨越180度经线的点对
                            crossing_indices = [i for i in range(1, len(Lines)) if abs(Lines[i].x - Lines[i - 1].x) > 180]
                            # 如果有穿越点，分割线段
                            if crossing_indices:
                                last_index = 0
                                for index in crossing_indices:
                                    # 创建当前分段的LineString并添加到列表中
                                    line_part = Lines[last_index:index]
                                    line_day_part=Lines_day[last_index:index]
                                    if len(line_part) >= 2:
                                        Lines_day_part.append(line_day_part)
                                    last_index = index
                                # 添加最后一个分段
                                line_part = Lines[last_index:]
                                line_day_part = Lines_day[last_index:]
                                if len(line_part) >= 2:
                                    Lines_day_part.append(line_day_part)
                            else:
                                # 如果没有穿越点，整个Lines是一个线段
                                Lines_day_part.append(Lines_day)
                            Lines=[]
                            Lines_day=[]
                        else:
                            Lines=[]
                            Lines_day=[]
                        geodetic_orbit.append({'time_utc': time,
                                               'lat': geodetic.lat.value,
                                               'lon': geodetic.lon.value,
                                               'time_local': local_time,
                                               'time_local_day': local_time.strftime('%Y-%m-%d'),
                                               })
                    df = pd.DataFrame(geodetic_orbit)
                    df.index = df['time_utc']
                    df['name'] = name.strip().replace(" ", "")
                    df['time_utc'] = pd.to_datetime(df['time_utc'])
                    # df['time_iso'] = df['time_utc'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    df.drop_duplicates(inplace=True)
                    dfs.append(df)
                grouped_list = []  # 创建一个空列表来存储最终的分组DataFrame
                for i in range(len(Lines_day_part)):
                    gdf = gpd.GeoDataFrame(Lines_day_part[i], columns=['time_utc','time_local', 'geometry'])
                    gdf['time_utc'] = pd.to_datetime(gdf['time_utc'])
                    gdf['time_local'] = pd.to_datetime(gdf['time_local'])
                    grouped = gdf.groupby(['time_utc','time_local'])['geometry'].apply(lambda x: LineString(x) if len(x) > 1 else None).reset_index()
                    grouped = grouped.dropna(subset=['geometry'])
                    grouped_list.append(grouped)
                final_gdf = gpd.GeoDataFrame(pd.concat(grouped_list, ignore_index=True))
                final_gdf.set_geometry('geometry', inplace=True)
                final_gdf.set_crs(epsg=4326, inplace=True)
                final_gdf.to_crs(epsg=3857, inplace=True)
                grouped_multiline = final_gdf.groupby(['time_utc','time_local'])['geometry'].apply(lambda x: MultiLineString(x.tolist()).buffer(width/2,cap_style=2)).reset_index()
                final_multiline_gdf = gpd.GeoDataFrame(grouped_multiline, crs='EPSG:3857',geometry='geometry')
                final_multiline_gdf['name']=name
                final_multiline_gdf['storage_time']= datetime.combine(datetime.today().date(), datetime.min.time())
                final_multiline_gdf = final_multiline_gdf[
                    ['name', 'time_utc', 'time_local','geometry','storage_time']]
                metadata = MetaData()
                Base = declarative_base()

                class OrbitPrediction(Base):
                    __tablename__ = f'orbit_transit_30days_8h_16h_1min'
                    id = Column(Integer, primary_key=True, autoincrement=True)
                    name = Column(Text)
                    time_utc = Column(TIMESTAMP(timezone=False))
                    time_local = Column(TIMESTAMP(timezone=False))
                    geometry = Column(Geometry(srid=3857))
                    storage_time=Column(TIMESTAMP(timezone=False))
                # Create the table if it doesn't exist
                Base.metadata.create_all(self.engine, checkfirst=True)
                with self.engine.connect() as connection:
                    final_multiline_gdf.to_postgis(f'orbit_transit_30days_8h_16h_1min', con=connection, schema='postgres', if_exists='append',
                                   index=False)
                    print(f"第{tstart}天,{name}文件数据已成功添加到数据库表orbit_transit_30days_8h_16h_1min中")
        # if delete_data:
        #     today = datetime.today().date()  # 获取今天的日期
        #     today = datetime.combine(today, datetime.min.time())
        #     delete_query = text(
        #         "DELETE FROM orbit_transit_30days_8h_16h_1min WHERE time_utc < :today"
        #     )
        #     try:
        #         with self.engine.connect() as connection:
        #             result = connection.execute(delete_query, {"today": today})
        #             connection.commit()  # 显式提交事务
        #             print(f"删除的行数: {result.rowcount}")
        #         print(f'已经删除{today}之前的数据')
        #     except Exception as e:
        #         print(f'删除数据时发生错误: {e}')
        if delete_data:
            today = datetime.today().date()  # 获取今天的日期
            today = datetime.combine(today, datetime.min.time())
            delete_query = text(
                "DELETE FROM orbit_transit_30days_8h_16h_1min WHERE storage_time < :today"
            )
            try:
                Session = sessionmaker(bind=self.engine)
                session = Session()
                result = session.execute(delete_query, {"today": today})
                session.commit()  # 提交事务
                print(f"删除的行数: {result.rowcount}")
                print(f'已经删除{today}之前的数据')
            except Exception as e:
                session.rollback()  # 回滚事务
                print(f'删除数据时发生错误: {e}')
            finally:
                session.close()  # 关闭会话

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
    # engine=OrbitCalTest.CreateConnection(database_name='postgres', database_username='postgres', database_password='ecnu2024',
    #                           database_host='49.52.31.105', database_post='5434')
    engine = OrbitCalTest.CreateConnection(database_name='postgres', database_username='postgres',
                                            database_password='sunjin123', database_host='43.128.24.169',
                                            database_post='5435')
    # engine= CreateConnection(database_name='postgres', database_username='postgres', database_password='sunjin123',database_host='49.52.31.105',database_post='5432')
    OrbitCalTest.crawl_satellite_data(start_time_interval=-1,end_time_interval=30,delete_data=True,freq='1min')
