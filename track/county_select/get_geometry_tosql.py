import geopandas as gpd
import os
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, TIMESTAMP, Float
from geoalchemy2 import Geometry
districts_data = []
directory = r'D:\kewei_git\track\county_select'
def CreateConnection(database_name,database_username,database_password,database_host,database_post):
    url = 'postgresql://{}:{}@{}:{}/{}'
    url=url.format(database_username,database_password,database_host,database_post,database_name)
    engine = create_engine(url)
    conn=engine.connect()
    return engine
# engine= CreateConnection(database_name='postgres', database_username='postgres', database_password='sunjin123',database_host='49.52.31.105',database_post='5432')
engine=CreateConnection(database_name='postgres', database_username='postgres', database_password='ecnu2024',
                              database_host='49.52.31.105', database_post='5434')
for filename in os.listdir(directory):
    if filename.endswith(".shp"):
        shp_path = os.path.join(directory, filename)

        gdf = gpd.read_file(shp_path, encoding='utf-8')

        gdf['geometry'] = gdf['geometry'].buffer(0)

        province_name = os.path.splitext(filename)[0]

        province_geometry = gdf.unary_union
        for _, row in gdf.iterrows():
            district_name = row['name']
            district_adcode= row['gb']
            district_geometry = row['geometry']
            districts_data.append({
                'province_name': province_name,
                'district_name': district_name,
                'district_adcode': district_adcode,
                'district_geometry': district_geometry
            })
        districts_data.append({
            'province_name': '中国',
            'district_name': province_name,
            'district_adcode': str(district_adcode)[0: -4] + '0000',
            'district_geometry': province_geometry
        })
districts_gdf = gpd.GeoDataFrame(districts_data,crs='EPSG:4326', geometry='district_geometry')
# 创建一个元数据对象
metadata = MetaData()
Base = declarative_base()

class Tb_countys(Base):
    __tablename__ = 'tb_countys'
    id = Column(Integer, primary_key=True, autoincrement=True)
    province_name=Column(Text)
    district_name=Column(Text)
    district_adcode=Column(Text)
    district_geometry=Column(Geometry( srid=4326))

# Create the table if it doesn't exist
Base.metadata.create_all(engine, checkfirst=True)
with engine.connect() as connection:
    districts_gdf.to_postgis('tb_countys', con=connection, schema='postgres', if_exists='append', index=False)
print("数据已存入数据库。")
