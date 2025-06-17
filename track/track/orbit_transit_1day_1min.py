import warnings
# 例如，忽略所有的运行时警告
warnings.filterwarnings("ignore")
import pandas as pd
from timezonefinder import TimezoneFinder
from orbit_transit_30days_8h_16h_10s_utm import OrbitCal
if __name__ == "__main__":
    pd.set_option('display.encoding', 'utf-8')
    satellite_width = {'ZIYUAN1-02C(ZY1-02C)': 60000, 'ZIYUAN3-1(ZY3-1)': 50000, 'ZIYUAN3-2(ZY3-2)': 50000,
                       'ZY-102D': 115000, 'ZY-102E': 115000, 'GAOFEN1': 60000, 'GAOFEN1-02': 60000, 'GAOFEN1-03': 60000,
                       'GAOFEN1-04': 60000, 'GAOFEN2': 45000, 'GAOFEN3': 130000, 'GAOFEN3-02': 130000,
                       'GAOFEN3-03': 650000, 'GAOFEN6': 90000, 'GAOFEN7': 20000,
                       'HAIYANG-1B': 512000,
                       'HAIYANG-1C': 2900000, 'HAIYANG-1D': 2900000,'GAOFEN5-01': 60000,
                       'GAOFEN5-01A': 60000, 'GAOFEN5-02': 60000}
    OrbitCalTest2=OrbitCal(satellite_width=satellite_width,timezone_finder=TimezoneFinder())
    # engine=OrbitCalTest.CreateConnection(database_name='postgres', database_username='postgres', database_password='ecnu2024',
    #                           database_host='49.52.31.105', database_post='5434')
    engine = OrbitCalTest2.CreateConnection(database_name='postgres', database_username='postgres',
                                            database_password='sunjin123', database_host='43.128.24.169',
                                            database_post='5435')
    # engine= CreateConnection(database_name='postgres', database_username='postgres', database_password='sunjin123',database_host='49.52.31.105',database_post='5432')
    OrbitCalTest2.crawl_satellite_data(start_time_interval=6,end_time_interval=1,delete_data=True,freq='1min')