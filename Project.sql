-- 1. Create the database
CREATE DATABASE IF NOT EXISTS AUTOSERVICEDB;

-- 2. Select the database to use
USE AUTOSERVICEDB;

-- 3. Create Independent Tables (no foreign keys)
-- ---------------------------------------------------
CREATE TABLE customers (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Phone VARCHAR(15),
    Address VARCHAR(255)
);

CREATE TABLE mechanics (
    MechanicID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Specialization VARCHAR(100)
);

CREATE TABLE services (
    ServiceID INT AUTO_INCREMENT PRIMARY KEY,
    ServiceName VARCHAR(100) NOT NULL,
    Description TEXT,
    StandardCost DECIMAL(10, 2) NOT NULL CHECK (StandardCost >= 0)
);

CREATE TABLE parts (
    PartID INT AUTO_INCREMENT PRIMARY KEY,
    PartName VARCHAR(100) NOT NULL,
    Manufacturer VARCHAR(100),
    Price DECIMAL(10, 2) NOT NULL CHECK (Price >= 0),
    StockQuantity INT NOT NULL DEFAULT 0 CHECK (StockQuantity >= 0)
);

-- 4. Create Dependent Tables (with foreign keys)
-- -------------------------------------------------
CREATE TABLE vehicles (
    VehicleID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    Make VARCHAR(50),
    Model VARCHAR(50),
    Year INT,
    VIN VARCHAR(17) UNIQUE,
    FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID) ON DELETE CASCADE
    -- ON DELETE CASCADE means if a customer is deleted, their vehicles are also deleted.
);

CREATE TABLE orders (
    OrderID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    OrderDate DATE NOT NULL DEFAULT (CURRENT_DATE),
    TotalAmount DECIMAL(10, 2) DEFAULT 0.00,
    Status VARCHAR(20) DEFAULT 'Pending',
    FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID)
);

CREATE TABLE serviceappointments (
    AppointmentID INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID INT NOT NULL,
    VehicleID INT NOT NULL,
    MechanicID INT NOT NULL,
    ServiceID INT NOT NULL,
    AppointmentDate DATETIME NOT NULL,
    Status VARCHAR(20) DEFAULT 'Scheduled',
    DurationMinutes INT DEFAULT 60, -- Added from your new diagram
    
    FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID),
    FOREIGN KEY (VehicleID) REFERENCES vehicles(VehicleID),
    FOREIGN KEY (MechanicID) REFERENCES mechanics(MechanicID),
    FOREIGN KEY (ServiceID) REFERENCES services(ServiceID)
);

CREATE TABLE orderitems (
    OrderItemID INT AUTO_INCREMENT PRIMARY KEY,
    OrderID INT NOT NULL,
    PartID INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    UnitPrice DECIMAL(10, 2), -- Price at the time of order
    
    FOREIGN KEY (OrderID) REFERENCES orders(OrderID),
    FOREIGN KEY (PartID) REFERENCES parts(PartID)
);

-- Select the database to use
USE AUTOSERVICEDB;

-- 1. Insert data into independent tables
-- ---------------------------------------
INSERT INTO customers (FirstName, LastName, Email, Phone, Address) VALUES
('Alice', 'Smith', 'alice.smith@email.com', '555-0101', '123 Main St, Anytown'),
('Bob', 'Johnson', 'bob.johnson@email.com', '555-0102', '456 Oak Ave, Sometown'),
('Charlie', 'Brown', 'charlie.b@email.com', '555-0103', '789 Pine Ln, Yourtown');

INSERT INTO mechanics (FirstName, LastName, Specialization) VALUES
('Carlos', 'Ray', 'Engine Specialist'),
('Diana', 'Prince', 'Tires and Brakes'),
('Evan', 'Wright', 'General Maintenance');

INSERT INTO services (ServiceName, Description, StandardCost) VALUES
('Standard Oil Change', 'Includes up to 5 quarts of conventional oil and a new filter.', 49.99),
('Brake Inspection', 'Inspect front and rear brake systems for wear and tear.', 25.00),
('Tire Rotation', 'Rotate all four tires to ensure even tread wear.', 19.95),
('Engine Diagnostic', 'Full computer diagnostic scan to identify check engine light causes.', 99.50);

INSERT INTO parts (PartName, Manufacturer, Price, StockQuantity) VALUES
('Oil Filter', 'AutoPartsCo', 15.00, 150),
('Brake Pads (Set)', 'StopWell', 75.50, 80),
('Wiper Blade (Pair)', 'ClearView', 22.00, 120),
('Air Filter', 'BreatheEasy', 18.50, 200),
('Spark Plug', 'IgniteCo', 8.75, 500);

-- 2. Insert data into dependent tables
-- -------------------------------------
-- (Note: We use the CustomerIDs 1, 2, 3 from above)
INSERT INTO vehicles (CustomerID, Make, Model, Year, VIN) VALUES
(1, 'Toyota', 'Camry', 2018, 'VIN123456789ABC'),
(1, 'Ford', 'F-150', 2020, 'VIN23456789ABCD'),
(2, 'Honda', 'Civic', 2021, 'VIN987654321XYZ');

-- (Create orders for Customer 1 and 2)
INSERT INTO orders (CustomerID, OrderDate, Status) VALUES
(1, '2025-10-28', 'Shipped'),
(2, '2025-11-03', 'Pending');

-- (Add items to Order 1 - OrderID 1)
-- (Note: The UnitPrice is a snapshot of the part price)
INSERT INTO orderitems (OrderID, PartID, Quantity, UnitPrice) VALUES
(1, 1, 1, 15.00), -- Order 1, Oil Filter
(1, 3, 1, 22.00); -- Order 1, Wiper Blade

-- (Add items to Order 2 - OrderID 2)
INSERT INTO orderitems (OrderID, PartID, Quantity, UnitPrice) VALUES
(2, 5, 4, 8.75); -- Order 2, Spark Plug

-- (Book appointments for customers)
-- (CustomerID, VehicleID, MechanicID, ServiceID, AppointmentDate, DurationMinutes)
INSERT INTO serviceappointments (CustomerID, VehicleID, MechanicID, ServiceID, AppointmentDate, DurationMinutes) VALUES
(1, 1, 3, 1, '2025-11-10 09:00:00', 45), -- Alice, Camry, Evan, Oil Change
(2, 3, 2, 2, '2025-11-11 14:00:00', 60), -- Bob, Civic, Diana, Brake Inspection
(1, 2, 1, 4, '2025-11-12 10:30:00', 90); -- Alice, F-150, Carlos, Engine Diagnostic

DELIMITER $$

CREATE TRIGGER trg_CheckMechanicName
BEFORE INSERT ON mechanics
FOR EACH ROW
BEGIN
    -- Check if FirstName or LastName contains any number (0-9)
    IF NEW.FirstName REGEXP '[0-9]' OR NEW.LastName REGEXP '[0-9]' THEN
        -- Raise a custom error
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Mechanic name cannot contain numbers.';
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE sp_AddMechanic(
    IN p_FirstName VARCHAR(50),
    IN p_LastName VARCHAR(50),
    IN p_Specialization VARCHAR(100)
)
BEGIN
    -- The trigger trg_CheckMechanicName will
    -- automatically run before this INSERT.
    INSERT INTO mechanics (FirstName, LastName, Specialization)
    VALUES (p_FirstName, p_LastName, p_Specialization);
END$$

DELIMITER ;
DELIMITER $$

CREATE FUNCTION fn_GetMechanicDetails(
    p_FirstName VARCHAR(50),
    p_LastName VARCHAR(50),
    p_Specialization VARCHAR(100)
)
RETURNS VARCHAR(255)
DETERMINISTIC
BEGIN
    RETURN CONCAT(p_FirstName, ' ', p_LastName, ' (', p_Specialization, ')');
END$$

DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_AddCustomer(
    IN p_FirstName VARCHAR(50),
    IN p_LastName VARCHAR(50),
    IN p_Email VARCHAR(100),
    IN p_Phone VARCHAR(15),
    IN p_Address VARCHAR(255)
)
BEGIN
    INSERT INTO customers (FirstName, LastName, Email, Phone, Address)
    VALUES (p_FirstName, p_LastName, p_Email, p_Phone, p_Address);
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_UpdateCustomer(
    IN p_CustomerID INT,
    IN p_FirstName VARCHAR(50),
    IN p_LastName VARCHAR(50),
    IN p_Email VARCHAR(100),
    IN p_Phone VARCHAR(15),
    IN p_Address VARCHAR(255)
)
BEGIN
    UPDATE customers
    SET 
        FirstName = p_FirstName,
        LastName = p_LastName,
        Email = p_Email,
        Phone = p_Phone,
        Address = p_Address
    WHERE CustomerID = p_CustomerID;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_AddVehicle(
    IN p_CustomerID INT,
    IN p_Make VARCHAR(50),
    IN p_Model VARCHAR(50),
    IN p_Year INT,
    IN p_VIN VARCHAR(17)
)
BEGIN
    INSERT INTO vehicles (CustomerID, Make, Model, Year, VIN)
    VALUES (p_CustomerID, p_Make, p_Model, p_Year, p_VIN);
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_UpdateVehicle(
    IN p_VehicleID INT,
    IN p_Make VARCHAR(50),
    IN p_Model VARCHAR(50),
    IN p_Year INT,
    IN p_VIN VARCHAR(17)
)
BEGIN
    UPDATE vehicles
    SET 
        Make = p_Make,
        Model = p_Model,
        Year = p_Year,
        VIN = p_VIN
    WHERE VehicleID = p_VehicleID;
END$$
DELIMITER ;



DELIMITER $$
CREATE PROCEDURE sp_AddService(
    IN p_ServiceName VARCHAR(100),
    IN p_Description TEXT,
    IN p_StandardCost DECIMAL(10, 2)
)
BEGIN
    INSERT INTO services (ServiceName, Description, StandardCost)
    VALUES (p_ServiceName, p_Description, p_StandardCost);
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_UpdateService(
    IN p_ServiceID INT,
    IN p_ServiceName VARCHAR(100),
    IN p_Description TEXT,
    IN p_StandardCost DECIMAL(10, 2)
)
BEGIN
    UPDATE services
    SET ServiceName = p_ServiceName,
        Description = p_Description,
        StandardCost = p_StandardCost
    WHERE ServiceID = p_ServiceID;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_AddPart(
    IN p_PartName VARCHAR(100),
    IN p_Manufacturer VARCHAR(100),
    IN p_Price DECIMAL(10, 2),
    IN p_StockQuantity INT
)
BEGIN
    INSERT INTO parts (PartName, Manufacturer, Price, StockQuantity)
    VALUES (p_PartName, p_Manufacturer, p_Price, p_StockQuantity);
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_UpdatePart(
    IN p_PartID INT,
    IN p_PartName VARCHAR(100),
    IN p_Manufacturer VARCHAR(100),
    IN p_Price DECIMAL(10, 2),
    IN p_StockQuantity INT
)
BEGIN
    UPDATE parts
    SET PartName = p_PartName,
        Manufacturer = p_Manufacturer,
        Price = p_Price,
        StockQuantity = p_StockQuantity
    WHERE PartID = p_PartID;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_BookAppointment(
    IN p_CustomerID INT,
    IN p_VehicleID INT,
    IN p_MechanicID INT,
    IN p_ServiceID INT,
    IN p_AppointmentDate DATETIME,
    IN p_DurationMinutes INT
)
BEGIN
    INSERT INTO serviceappointments (CustomerID, VehicleID, MechanicID, ServiceID, AppointmentDate, DurationMinutes)
    VALUES (p_CustomerID, p_VehicleID, p_MechanicID, p_ServiceID, p_AppointmentDate, p_DurationMinutes);
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_UpdateAppointmentStatus(
    IN p_AppointmentID INT,
    IN p_Status VARCHAR(20)
)
BEGIN
    UPDATE serviceappointments
    SET Status = p_Status
    WHERE AppointmentID = p_AppointmentID;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_CancelAppointment(
    IN p_AppointmentID INT
)
BEGIN
    DELETE FROM serviceappointments WHERE AppointmentID = p_AppointmentID;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_CreateOrder(
    IN p_CustomerID INT,
    OUT out_OrderID INT
)
BEGIN
    INSERT INTO orders (CustomerID) VALUES (p_CustomerID);
    SET out_OrderID = LAST_INSERT_ID();
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_AddOrderItem(
    IN p_OrderID INT,
    IN p_PartID INT,
    IN p_Quantity INT
)
BEGIN
    DECLARE v_Price DECIMAL(10, 2);
    
    -- Get the current price from the parts table
    SELECT Price INTO v_Price FROM parts
    WHERE PartID = p_PartID;
    
    -- Insert the item with the snapshot of the price
    INSERT INTO orderitems (OrderID, PartID, Quantity, UnitPrice)
    VALUES (p_OrderID, p_PartID, p_Quantity, v_Price);
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE sp_UpdateOrderStatus(
    IN p_OrderID INT,
    IN p_Status VARCHAR(20)
)
BEGIN
    UPDATE orders
    SET Status = p_Status
    WHERE OrderID = p_OrderID;
END$$
DELIMITER ;


-- --- Complex Triggers in our project --- --
DELIMITER $$
CREATE TRIGGER trg_CheckStockBeforeOrder
BEFORE INSERT ON orderitems
FOR EACH ROW
BEGIN
    DECLARE v_Stock INT;
    
    SELECT StockQuantity INTO v_Stock FROM parts
    WHERE PartID = NEW.PartID;
    
    IF v_Stock < NEW.Quantity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Insufficient stock for this item.';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_UpdateStockAfterOrder
AFTER INSERT ON orderitems
FOR EACH ROW
BEGIN
    UPDATE parts
    SET StockQuantity = StockQuantity - NEW.Quantity
    WHERE PartID = NEW.PartID;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_UpdateOrderTotal
AFTER INSERT ON orderitems
FOR EACH ROW
BEGIN
    UPDATE orders
    SET TotalAmount = TotalAmount + (NEW.Quantity * NEW.UnitPrice)
    WHERE OrderID = NEW.OrderID;
END$$
DELIMITER ;