import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(__file__), 'species.db')
TREES_TABLE = 'species'


class DbHandler:
    def __init__(self, path: str, table: str) -> None:
        self._db = sqlite3.connect(path)
        self.table = table

    def _exec_query(self, query: str) -> sqlite3.Cursor:
        cur = self._db.cursor()
        cur.execute(query)
        return cur

    def select_species_by_soil_type(self, soil_type: str, category: str):
        res = self._exec_query(f"""SELECT {category}, species_native_name from {self.table}
                               WHERE {category} LIKE '%{soil_type}%';""")

        rows = [row[1] for row in res.fetchall(
        ) if self._double_check_species(row[0], soil_type)]

        res.close()

        return rows

    def _double_check_species(self, soil_type: str, searched_type: str) -> bool:
        return searched_type in soil_type.split(';')

    def select_species_info(self, species_names: str):
        res = self._exec_query(f"""SELECT species_native_name, target_height, target_width, shape, 
                               insolation_level, habitat, soil_moisture_level from {self.table}
                               WHERE species_native_name in {species_names};""")
        rows = [row for row in res.fetchall()]

        res.close()

        return rows

    def insert_new_rows(self, new_rows: list):

        new_values_combined = []
        for row in new_rows:
            row = [f'"{value}"' for value in row]
            row_values = f'({", ".join(row)})'
            new_values_combined.append(row_values)

        self._exec_query(f"""INSERT INTO {self.table} 
            (species_native_name, species_latin_name, target_height, target_width, shape, soil_type_optimum, 
            soil_type_medium, soil_type_low, habitat, insolation_level, soil_moisture_level)
            VALUES {", ".join(new_values_combined)};""")

        self._db.commit()

    def get_all_data(self):
        res = self._exec_query(f'SELECT * FROM {self.table}')

        rows = [row for row in res.fetchall()]

        res.close()

        return rows


db_handler = DbHandler(path=DB_PATH, table=TREES_TABLE)
