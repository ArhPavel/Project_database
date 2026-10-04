import psycopg2
import csv

from psycopg2 import connect
from psycopg2._psycopg import cursor


def fill_table_from_csv(table_name, csv_file):
    connection = psycopg2.connect(
    dbname="north",
    user="postgres",
    password="afro25",
    host="localhost",
    port="5432",)
    cursor = connection.cursor()

    with open(csv_file) as csvfile:
        csv_reader = csv.reader(csvfile)
        header = next(csv_reader)
        for row in csv_reader:
            insert_query = f"INSERT INTO {table_name} ({', '.join(header)}) VALUES ({', '.join(['%s'] * len(row))})"
            cursor.execute(insert_query, row)

    connection.commit()
    cursor.close()
    connection.close()


def main():
    fill_table_from_csv("customers_data", "data/customers_data.csv")
    fill_table_from_csv("employees_data", "data/employees_data.csv")
    fill_table_from_csv("orders_data", "data/orders_data.csv")



if __name__ == "__main__":
    main()