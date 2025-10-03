# EDI 810 Mandatory Fields Summary

## Complete List of Mandatory Fields with Specifications

This document lists all mandatory EDI 810 fields with their exact names, usage descriptions, cardinality, data types, and field lengths as implemented in the system.

### Interchange Control Header (ISA) - All Mandatory

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| ISA01 | Authorization Information Qualifier | Code to identify the type of information in the Authorization Information | 1/1 | ID | 2/2 |
| ISA02 | Authorization Information | Information used for additional identification or authorization of the interchange sender or the data in the interchange | 1/1 | AN | 10/10 |
| ISA03 | Security Information Qualifier | Code to identify the type of information in the Security Information | 1/1 | ID | 2/2 |
| ISA04 | Security Information | Information used for identifying the security information about the interchange sender or the data in the interchange | 1/1 | AN | 10/10 |
| ISA05 | Interchange ID Qualifier | Qualifier to designate the system/method of code structure used to designate the sender or receiver ID element being qualified | 1/1 | ID | 2/2 |
| ISA06 | Interchange Sender ID | Identification code published by the sender for other parties to use as the receiver ID to route data to them | 1/1 | AN | 15/15 |
| ISA07 | Interchange ID Qualifier | Qualifier to designate the system/method of code structure used to designate the sender or receiver ID element being qualified | 1/1 | ID | 2/2 |
| ISA08 | Interchange Receiver ID | Identification code published by the receiver of the data | 1/1 | AN | 15/15 |
| ISA09 | Interchange Date | Date of the interchange | 1/1 | DT | 6/6 |
| ISA10 | Interchange Time | Time of the interchange | 1/1 | TM | 4/4 |
| ISA11 | Interchange Control Standards Identifier | Code to identify the agency responsible for the control standard used by the message that is enclosed by the interchange header and trailer | 1/1 | ID | 1/1 |
| ISA12 | Interchange Control Version Number | This version number covers the interchange control segments | 1/1 | ID | 5/5 |
| ISA13 | Interchange Control Number | A control number assigned by the interchange sender | 1/1 | N0 | 9/9 |
| ISA14 | Acknowledgment Requested | Code sent by the sender to request an interchange acknowledgment (TA1) | 1/1 | ID | 1/1 |
| ISA15 | Usage Indicator | Code to indicate whether data enclosed by this interchange envelope is test, production or information | 1/1 | ID | 1/1 |
| ISA16 | Component Element Separator | Type is not applicable; the component element separator is a delimiter and not a data element | 1/1 | AN | 1/1 |

### Functional Group Header (GS) - All Mandatory

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| GS01 | Functional Identifier Code | Code identifying a group of application related transaction sets | 1/1 | ID | 2/2 |
| GS02 | Application Sender's Code | Code identifying party sending transmission; codes agreed to by trading partners | 1/1 | AN | 2/15 |
| GS03 | Application Receiver's Code | Code identifying party receiving transmission; codes agreed to by trading partners | 1/1 | AN | 2/15 |
| GS04 | Date | Date expressed as CCYYMMDD | 1/1 | DT | 8/8 |
| GS05 | Time | Time expressed in 24-hour clock time as follows: HHMM, or HHMMSS, or HHMMSSD, or HHMMSSDD | 1/1 | TM | 4/8 |
| GS06 | Group Control Number | Assigned number originated and maintained by the sender | 1/1 | N0 | 1/9 |
| GS07 | Responsible Agency Code | Code used in conjunction with Data Element 480 to identify the issuer of the standard | 1/1 | ID | 1/2 |
| GS08 | Version / Release / Industry Identifier Code | Code indicating the version, release, subrelease, and industry identifier of the EDI standard being used | 1/1 | AN | 1/12 |

### Transaction Set Header (ST) - All Mandatory

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| ST01 | Transaction Set Identifier Code | Code uniquely identifying a Transaction Set (must be 810 for Invoice) | 1/1 | ID | 3/3 |
| ST02 | Transaction Set Control Number | Identifying control number that must be unique within the transaction set functional group assigned by the originator for a transaction set | 1/1 | AN | 4/9 |

### Invoice Information (BIG) - Mandatory Fields

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| BIG01 | Invoice Date | Date expressed as CCYYMMDD | 1/1 | DT | 8/8 |
| BIG02 | Invoice Number | Identifying number assigned by issuer | 1/1 | AN | 1/22 |

### Name Information (N1) - Mandatory Fields

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| N101 | Entity Identifier Code | Code identifying an organizational entity, a physical location, property or an individual | 1/1 | ID | 2/3 |

### Additional Name Information (N2) - Mandatory Fields

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| N201 | Name | Free-form name | 1/1 | AN | 1/60 |

### Address Information (N3) - Mandatory Fields

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| N301 | Address Information | Address information | 1/1 | AN | 1/55 |

### Line Item (IT1) - Mandatory Fields

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| IT102 | Quantity Invoiced | Number of units invoiced (supplier units) | 1/1 | R | 1/15 |
| IT103 | Unit or Basis for Measurement Code | Code specifying the units in which a value is being expressed, or manner in which a measurement has been taken | 1/1 | ID | 2/2 |
| IT104 | Unit Price | Price per unit of product, service, commodity, etc. | 1/1 | R | 1/17 |

### Total Invoice Amount (TDS) - Mandatory Fields

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| TDS01 | Amount | Monetary amount | 1/1 | N2 | 1/18 |

### Transaction Totals (CTT) - Mandatory Fields

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| CTT01 | Number of Line Items | Total number of line items in the transaction set | 1/1 | N0 | 1/6 |

### Transaction Set Trailer (SE) - All Mandatory

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| SE01 | Number of Included Segments | Total number of segments included in a transaction set including ST and SE segments | 1/1 | N0 | 1/10 |
| SE02 | Transaction Set Control Number | Identifying control number that must be unique within the transaction set functional group assigned by the originator for a transaction set | 1/1 | AN | 4/9 |

### Functional Group Trailer (GE) - All Mandatory

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| GE01 | Number of Transaction Sets Included | A count of the number of transaction sets included in the functional group | 1/1 | N0 | 1/6 |
| GE02 | Group Control Number | Assigned number originated and maintained by the sender | 1/1 | N0 | 1/9 |

### Interchange Control Trailer (IEA) - All Mandatory

| Field Code | Field Name | Usage | Cardinality | Type | Length |
|------------|------------|--------|-------------|------|--------|
| IEA01 | Number of Included Functional Groups | A count of the number of functional groups included in an interchange | 1/1 | N0 | 1/5 |
| IEA02 | Interchange Control Number | A control number assigned by the interchange sender | 1/1 | N0 | 9/9 |

## Field Length Validation

The system now performs automatic field length validation:

- **Green Background**: Mandatory field present with correct length
- **Red Background**: Mandatory field missing OR present with incorrect length
- **Yellow Background**: Optional field present with correct length
- **White Background**: Optional field missing

### Length Error Display

When a field length doesn't match the specification, the system displays:
- ⚠ Field length error with actual vs expected length
- Red highlighting of the affected field
- Detailed error message showing the mismatch

## Data Types Legend

- **ID**: Identifier - Fixed format codes
- **AN**: Alphanumeric - Letters and numbers
- **DT**: Date - Date format (CCYYMMDD)
- **TM**: Time - Time format (HHMM or HHMMSS)
- **N0**: Numeric - Whole numbers
- **N2**: Numeric with 2 decimal places
- **R**: Real number - Decimal numbers

## Cardinality Legend

- **1/1**: Mandatory, exactly one occurrence
- **0/1**: Optional, zero or one occurrence

## Length Format

- **Min/Max**: Minimum and maximum allowed character length
- Example: **1/22** means minimum 1 character, maximum 22 characters
