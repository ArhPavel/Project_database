CREATE TABLE customers_data
(
	customer_id varchar(100) PRIMARY KEY,
	company_name varchar(100) NOT NULL,
	contact_name varchar(100) NOT NULL
);

CREATE TABLE employees_data
(
	employee_id SERIAL PRIMARY KEY,
	first_name varchar(100) NOT NULL,
	last_name varchar(100) NOT NULL,
	title varchar(100) NOT NULL,
	birth_date date NOT NULL,
	notes text NOT NULL
);

CREATE TABLE orders_data
(
	order_id int PRIMARY KEY,
	customer_id	varchar(100) NOT NULL,
	employee_id int NOT NULL,
	order_date date NOT NULL,
	ship_city varchar(100) NOT NULL,
	FOREIGN KEY (customer_id) REFERENCES customers_data(customer_id),
	FOREIGN KEY (employee_id) REFERENCES employees_data(employee_id)

);