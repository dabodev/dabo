/* Run this script to set up the unittest database on your server */


/****************** GENERATORS ********************/

CREATE GENERATOR GEN_DABO_UNITTEST_TBL;
CREATE GENERATOR GEN_JOBID;

/******************** TABLES **********************/

CREATE TABLE DABO_UNITTEST_TBL
(
  PK Numeric(18,0) NOT NULL,
  CFIELD Char(32),
  IFIELD Integer,
  NFIELD Decimal(8,2),
  JOBID Numeric(18,0) NOT NULL,
  PRIMARY KEY (PK)
);

/******************** TRIGGERS ********************/

SET TERM ^ ;
CREATE TRIGGER BI_DABO_UNITTEST_TBL FOR DABO_UNITTEST_TBL ACTIVE
BEFORE INSERT POSITION 0
AS
BEGIN
    if (NEW.PK is NULL) THEN
        NEW.PK = GEN_ID(GEN_DABO_UNITTEST_TBL, 1);
END^
SET TERM ; ^

GRANT DELETE, INSERT, REFERENCES, SELECT, UPDATE
 ON DABO_UNITTEST_TBL TO  SYSDBA WITH GRANT OPTION;
