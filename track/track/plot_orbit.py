import geopandas as gpd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

def CreateConnection(database_name, database_username, database_password, database_host, database_post):
    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(database_username, database_password, database_host, database_post, database_name)
    engine = create_engine(url)
    conn = engine.connect()
    return engine
engine=CreateConnection(database_name='postgres', database_username='postgres', database_password='ecnu2024',
                              database_host='49.52.31.105', database_post='5434')

# Replace 'your_view' with your actual view name
gdf = gpd.read_postgis('SELECT * FROM orbit_transit_30days_8h_16h_1min', engine, geom_col='geometry')

# Plotting the geometries
gdf.plot()
plt.savefig('轨道.png')
plt.show()  # This will display the plot
