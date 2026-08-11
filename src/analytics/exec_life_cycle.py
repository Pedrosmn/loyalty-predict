# %%

import pandas as pd
import sqlalchemy

from tqdm import tqdm
import datetime

# %%

def import_query(path):
    with open(path) as open_file:
        query = open_file.read()
    return query

query = import_query("life_cycle.sql")
print(query)

# %%


engine_app = sqlalchemy.create_engine("sqlite:///../../data/loyalty-system/database.db")

engine_analytical = sqlalchemy.create_engine("sqlite:///../../data/analytics/database.db")

# %%

def date_range(start, stop):
    dates = []

    while start <= stop:
        dates.append(start)

        dt_start = datetime.datetime.strptime(start, '%Y-%m-%d')
        dt_start += datetime.timedelta(days=1)

        start = dt_start.strftime('%Y-%m-%d')

    return dates


dates = date_range('2024-09-01', '2025-10-01')

for i in tqdm(dates):


    with engine_analytical.connect() as con:
        try:
            query_delete = f"DELETE FROM life_cycle WHERE dtRef = date('{i}', '-1 day')"
            # print(query_delete)
            con.execute(sqlalchemy.text(query_delete))
            con.commit()
        except Exception as err:
            print(err)
    query_format = query.format(date=i)
    df = pd.read_sql(query_format, con=engine_app)
    df.to_sql(con=engine_analytical, if_exists='append', name="life_cycle", index=False)

# %%
