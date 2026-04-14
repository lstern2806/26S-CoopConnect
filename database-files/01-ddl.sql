DROP DATABASE IF EXISTS coopconnect;
CREATE DATABASE coopconnect;
USE coopconnect;

USE coopconnect;
DROP TABLE IF EXISTS USER;
CREATE TABLE USER (
    userId      INT             NOT NULL AUTO_INCREMENT,
    firstName   VARCHAR(50)     NOT NULL,
    lastName    VARCHAR(50)     NOT NULL,
    email       VARCHAR(100)    NOT NULL UNIQUE,
    password    VARCHAR(255)    NOT NULL,
    accountStatus VARCHAR(20)   NOT NULL DEFAULT 'active',
    PRIMARY KEY (userId)
);


DROP TABLE IF EXISTS COMPANY;
CREATE TABLE COMPANY (
    companyId   INT             NOT NULL AUTO_INCREMENT,
    companyName VARCHAR(100)    NOT NULL,
    industry    VARCHAR(100),
    location    VARCHAR(100),
    website     VARCHAR(200),
    PRIMARY KEY (companyId)
);


DROP TABLE IF EXISTS ADMIN;
CREATE TABLE ADMIN (
    adminId     INT             NOT NULL AUTO_INCREMENT,
    userId      INT             NOT NULL,
    lastLogin   DATETIME,
    PRIMARY KEY (adminId),
    FOREIGN KEY (userId) REFERENCES USER (userId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


DROP TABLE IF EXISTS ADVISOR;
CREATE TABLE ADVISOR (
    advisorId   INT             NOT NULL AUTO_INCREMENT,
    userId      INT             NOT NULL,
    department  VARCHAR(100),
    PRIMARY KEY (advisorId),
    FOREIGN KEY (userId) REFERENCES USER (userId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


DROP TABLE IF EXISTS STUDENT;
CREATE TABLE STUDENT (
    studentId   INT             NOT NULL AUTO_INCREMENT,
    userId      INT             NOT NULL,
    advisorId   INT,
    major       VARCHAR(100),
    GPA         DOUBLE,
    gradYear    YEAR,
    PRIMARY KEY (studentId),
    FOREIGN KEY (userId) REFERENCES USER (userId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (advisorId) REFERENCES ADVISOR (advisorId)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);


DROP TABLE IF EXISTS EMPLOYER;
CREATE TABLE EMPLOYER (
    employerId  INT             NOT NULL AUTO_INCREMENT,
    userId      INT             NOT NULL,
    companyId   INT             NOT NULL,
    jobTitle    VARCHAR(100),
    PRIMARY KEY (employerId),
    FOREIGN KEY (userId) REFERENCES USER (userId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (companyId) REFERENCES COMPANY (companyId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


DROP TABLE IF EXISTS COOPROLE;
CREATE TABLE COOPROLE (
    roleId      INT             NOT NULL AUTO_INCREMENT,
    companyId   INT             NOT NULL,
    title       VARCHAR(100)    NOT NULL,
    department  VARCHAR(100),
    salary      DECIMAL(10,2),
    duration    VARCHAR(50),
    PRIMARY KEY (roleId),
    FOREIGN KEY (companyId)
        REFERENCES COMPANY (companyId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

DROP TABLE IF EXISTS COOPEXPERIENCE;
CREATE TABLE COOPEXPERIENCE (
    experienceId    INT             NOT NULL AUTO_INCREMENT,
    studentId       INT             NOT NULL,
    companyId       INT             NOT NULL,
    roleId          INT,
    semester        VARCHAR(20),
    year            YEAR,
    notes           TEXT,
    PRIMARY KEY (experienceId),
    FOREIGN KEY (studentId) REFERENCES STUDENT (studentId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (companyId) REFERENCES COMPANY (companyId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (roleId) REFERENCES COOPROLE (roleId)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);


DROP TABLE IF EXISTS STUDENTOUTREACH;
CREATE TABLE STUDENTOUTREACH (
    messageId       INT             NOT NULL AUTO_INCREMENT,
    senderId        INT             NOT NULL,
    recipientId     INT             NOT NULL,
    content         TEXT,
    dateSent        DATETIME,
    responseStatus  VARCHAR(50)     DEFAULT 'pending',
    PRIMARY KEY (messageId),
    FOREIGN KEY (senderId) REFERENCES STUDENT (studentId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (recipientId) REFERENCES STUDENT (studentId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

DROP TABLE IF EXISTS EMPLOYEROUTREACH;
CREATE TABLE EMPLOYEROUTREACH (
    empMessageId    INT             NOT NULL AUTO_INCREMENT,
    employerId      INT             NOT NULL,
    studentId       INT             NOT NULL,
    content         TEXT,
    dateSent        DATETIME,
    response        TEXT,
    responseDate    DATETIME,
    status          VARCHAR(50)     DEFAULT 'pending',
    PRIMARY KEY (empMessageId),
    FOREIGN KEY (employerId) REFERENCES EMPLOYER (employerId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (studentId) REFERENCES STUDENT (studentId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

DROP TABLE IF EXISTS ALERT;
CREATE TABLE ALERT (
    alertId     INT             NOT NULL AUTO_INCREMENT,
    advisorId   INT             NOT NULL,
    studentId   INT             NOT NULL,
    messageId   INT,
    message     TEXT,
    dateTrigger DATETIME,
    PRIMARY KEY (alertId),
    FOREIGN KEY (advisorId) REFERENCES ADVISOR (advisorId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (studentId) REFERENCES STUDENT (studentId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (messageId) REFERENCES STUDENTOUTREACH (messageId)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

DROP TABLE IF EXISTS SYSTEMSETTING;
CREATE TABLE SYSTEMSETTING (
    settingId           INT             NOT NULL AUTO_INCREMENT,
    updatedBy           INT             NOT NULL,
    settingName         VARCHAR(100)    NOT NULL,
    settingValue        VARCHAR(255),
    settingDescription  TEXT,
    updatedAt           DATETIME,
    PRIMARY KEY (settingId),
    FOREIGN KEY (updatedBy) REFERENCES ADMIN (adminId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

DROP TABLE IF EXISTS AUDITLOG;
CREATE TABLE AUDITLOG (
    logId           INT             NOT NULL AUTO_INCREMENT,
    adminId         INT             NOT NULL,
    actionType      VARCHAR(50),
    actionDetails   TEXT,
    affectedRecord  VARCHAR(100),
    actionTimestamp DATETIME,
    PRIMARY KEY (logId),
    FOREIGN KEY (adminId) REFERENCES ADMIN (adminId)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);