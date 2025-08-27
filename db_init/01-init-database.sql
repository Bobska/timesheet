-- Initial database setup for FamilyHub Timesheet
-- This script creates the database and configures basic settings

USE master;
GO

-- Create the database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'timesheet_prod')
BEGIN
    CREATE DATABASE timesheet_prod
    COLLATE SQL_Latin1_General_CP1_CI_AS;
    PRINT 'Database "timesheet_prod" created successfully.';
END
ELSE
BEGIN
    PRINT 'Database "timesheet_prod" already exists.';
END
GO

-- Use the timesheet database
USE timesheet_prod;
GO

-- Configure database settings for optimal performance
ALTER DATABASE timesheet_prod SET READ_COMMITTED_SNAPSHOT ON;
ALTER DATABASE timesheet_prod SET ALLOW_SNAPSHOT_ISOLATION ON;
GO

-- Create a test connection function
CREATE OR ALTER FUNCTION dbo.TestConnection()
RETURNS NVARCHAR(50)
AS
BEGIN
    RETURN 'FamilyHub Timesheet DB Ready';
END
GO

-- Test the function
SELECT dbo.TestConnection() AS Status;
GO

PRINT 'Database initialization completed successfully.';
PRINT 'Database: timesheet_prod';
PRINT 'Collation: SQL_Latin1_General_CP1_CI_AS';
PRINT 'Ready for Django migrations.';
GO
