import warnings
import math
import requests
# 例如，忽略所有的运行时警告
warnings.filterwarnings("ignore")
from sgp4.api import Satrec
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
from shapely.geometry import Point, LineString,Polygon,MultiPolygon
from geoalchemy2 import Geometry
from pyproj import Transformer
from sqlalchemy.orm import sessionmaker
class Tle_Requests():
    def tle_requests_totxt(self):
        tle_para = []
        satellite_names = {'ZIYUAN1-02C(ZY1-02C)': '资源一号02C星', 'ZIYUAN3-1(ZY3-1)': '资源三号01星',
                           'ZIYUAN3-2(ZY3-2)': '资源三号02星', 'ZY-102D': '资源一号01星2D星',
                           'ZY-102E': '资源一号02E星',
                           'GAOFEN-1': '高分一号', 'GAOFEN-102': '高分一号02星', 'GAOFEN-103': '高分一号03星',
                           'GAOFEN-104': '高分一号04星', 'GAOFEN-2': '高分二号',
                           'GAOFEN-6': '高分六号',
                           'GAOFEN-7': '高分七号', 'HAIYANG-1B': '海洋一号B星', 'HAIYANG-1C': '海洋一号C星',
                           'HAIYANG-1D': '海洋一号D星',
                            'GAOFEN-501A': '高分五号01A星', 'GAOFEN-502': '高分五号02星'}
        satellite_names2 = ['ZIYUAN1-02C(ZY1-02C)', 'ZIYUAN3-1(ZY3-1)',
                           'ZIYUAN3-2(ZY3-2)', 'ZY-102D',
                           'ZY-102E',
                           'GAOFEN1', 'GAOFEN1-02', 'GAOFEN1-03',
                           'GAOFEN1-04', 'GAOFEN2',
                           'GAOFEN6',
                           'GAOFEN7', 'HAIYANG-1B', 'HAIYANG-1C',
                           'HAIYANG-1D',
                           'GAOFEN5-01A', 'GAOFEN5-02']
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"  # 想要爬取的网页地址
        response = requests.get(url)
        url_info = response.text.splitlines()
        matches = []
        for ind_satellite,satellite_name in enumerate(satellite_names):
            pattern = r"^" + re.escape(satellite_name) + r"$"
            for index, item in enumerate(url_info):
                if re.search(pattern, item.replace(" ","")):
                    matches.append((satellite_names2[ind_satellite], url_info.index(item)))
        if len(matches) > 0:
            for match in matches:
                tle_para.append(match[0])
                tle_para.append(url_info[match[1] + 1])
                tle_para.append(url_info[match[1] + 2])
        else:
            print("没有找到匹配")

        def write_list_to_file(lst, filename):
            with open(filename, 'w') as file:
                for i, element in enumerate(lst):
                    file.write(element)
                    if i != len(lst) - 1:
                        file.write('\n')
        write_list_to_file(tle_para, 'tle_para_updateday.txt')
class OrbitCal():
    def __init__(self,satellite_width,timezone_finder):
        self.satellite_width=satellite_width
        self.timezone_finder=timezone_finder

    def crawl_satellite_data(self,start_time_interval,end_time_interval,delete_data):
        # 计算当前utc时间，设置时间段和间隔
        now = datetime.now()
        utc_now = now.astimezone(timezone('UTC')).replace(hour=0, minute=0, second=0, microsecond=0)
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

                    geodetic_orbit.append({'time_utc': time,
                                           'height': geodetic.height.value * 1000,
                                           'lat': geodetic.lat.value,
                                           'lon': geodetic.lon.value,
                                           # 'time_local': local_time,
                                           # 'time_zone': target_timezone_str,
                                           })
                    # 数据存为dataframe，csv
                    df = pd.DataFrame(geodetic_orbit)
                    df.index = df['time_utc']
                    df['name'] = name.strip().replace(" ", "")
                    df['time_utc'] = pd.to_datetime(df['time_utc'])
                    # df['time_iso'] = df['time_utc'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    df.drop_duplicates(inplace=True)
                    dfs.append(df)
                all_data = pd.concat(dfs, ignore_index=True)
                all_data.drop_duplicates(inplace=True)
                all_data.reset_index(drop=True, inplace=True)

                all_data['time_utc'] = all_data['time_utc'].dt.tz_localize(None)
                all_data['storage_time']=datetime.combine(datetime.today().date(), datetime.min.time())
                all_data = all_data[
                    ['name', 'time_utc', 'lat', 'lon', 'height','storage_time']]
                # 使用PyProj的CRS格式
                gdf = pd.DataFrame(all_data)
                metadata = MetaData()
                Base = declarative_base()

                class OrbitPrediction(Base):
                    __tablename__ = 'orbit_prediction_30days'

                    id = Column(Integer, primary_key=True, autoincrement=True)
                    name = Column(Text)
                    time_utc = Column(TIMESTAMP(timezone=False))
                    lat = Column(Float)
                    lon = Column(Float)
                    height = Column(Float)
                    storage_time = Column(TIMESTAMP(timezone=False))

                # Create the table if it doesn't exist
                Base.metadata.create_all(self.engine, checkfirst=True)
                with self.engine.connect() as connection:
                    gdf.to_sql('orbit_prediction_30days', con=connection, schema='postgres', if_exists='append',
                                   index=False)
                    print(f"第{tstart}天,{name}文件数据已成功添加到数据库表中")
        if delete_data:
            today = datetime.today().date()  # 获取今天的日期
            today = datetime.combine(today, datetime.min.time())
            delete_query = text(
                "DELETE FROM orbit_prediction_30days WHERE storage_time < :today"
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
    tle_now=Tle_Requests()
    tle_now.tle_requests_totxt()
    satellite_width = {'ZIYUAN1-02C(ZY1-02C)': 60000, 'ZIYUAN3-1(ZY3-1)': 50000, 'ZIYUAN3-2(ZY3-2)': 50000,
                       'ZY-102D': 115000, 'ZY-102E': 115000, 'GAOFEN1': 60000, 'GAOFEN1-02': 60000, 'GAOFEN1-03': 60000,
                       'GAOFEN1-04': 60000, 'GAOFEN2': 45000, 'GAOFEN3': 130000, 'GAOFEN3-02': 130000,
                       'GAOFEN3-03': 650000, 'GAOFEN6': 90000, 'GAOFEN7': 20000,
                       'HAIYANG-1B': 512000,
                       'HAIYANG-1C': 2900000, 'HAIYANG-1D': 2900000,
                       'GAOFEN5-01A': 60000, 'GAOFEN5-02': 60000}
    OrbitCalTest=OrbitCal(satellite_width=satellite_width,timezone_finder=TimezoneFinder())
    # engine=OrbitCalTest.CreateConnection(database_name='postgres', database_username='postgres', database_password='ecnu2024',
    #                           database_host='49.52.31.105', database_post='5434')
    engine= OrbitCalTest.CreateConnection(database_name='postgres', database_username='postgres', database_password='sunjin123',database_host='43.128.24.169',database_post='5435')
    OrbitCalTest.crawl_satellite_data(start_time_interval=-1,end_time_interval=30,delete_data=True)
