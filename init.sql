-- Initialize database for todoapp
-- This file is automatically executed when MySQL container starts

-- Create database if it doesn't exist (already handled by environment variables)
-- CREATE DATABASE IF NOT EXISTS todoapp;

-- Grant permissions to todoapp user (already handled by environment variables)
-- GRANT ALL PRIVILEGES ON todoapp.* TO 'todoapp'@'%';
-- FLUSH PRIVILEGES;

-- Set timezone
SET time_zone = '+00:00';

-- Create tables will be handled by Flask-SQLAlchemy/Flask-Migrate