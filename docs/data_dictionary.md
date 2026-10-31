# WorkforceIQ Enterprise Data Dictionary

This document specifies the complete normalized relational schema across all 15 entities.
For every field, the dictionary details: **Field Name**, **Data Type**, **Nullability (Required / Optional)**, **Allowed Values**, **Unit of Measure**, **Uniqueness**, **Validation Rules**, and **Relational Bindings**.

---

## Table of Contents
1. [roles](#1-roles)
2. [skills](#2-skills)
3. [role_skills](#3-role_skills)
4. [employees](#4-employees)
5. [employee_skills](#5-employee_skills)
6. [availabilities](#6-availabilities)
7. [projects](#7-projects)
8. [demand_plans](#8-demand_plans)
9. [allocations](#9-allocations)
10. [trainings](#10-trainings)
11. [gap_analyses](#11-gap_analyses)
12. [recommendations](#12-recommendations)
13. [scenario_runs](#13-scenario_runs)
14. [issue_records](#14-issue_records)
15. [audit_events](#15-audit_events)

---

### 1. `roles`
Standard organizational job role definitions and billing benchmarks.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `ROL-######` | String | Unique | Matches regex `^ROL-\d{6}$` | Natural Key |
| `title` | VARCHAR(150) | Required | Any non-empty string | — | Unique | Max length 150 chars | — |
| `code` | VARCHAR(50) | Required | Alphanumeric uppercase | — | Unique | Max length 50 chars | — |
| `department` | VARCHAR(100) | Required | Standard department names | — | Non-unique | Max length 100 chars | — |
| `description` | TEXT | Optional | Open text | — | Non-unique | None | — |
| `standard_hourly_rate` | NUMERIC(10,2) | Optional | Decimal $\ge 0.00$ | USD/Hour | Non-unique | `standard_hourly_rate >= 0.00` | — |
| `is_active` | BOOLEAN | Required | `TRUE`, `FALSE` | Flag | Non-unique | Default `TRUE` | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 2. `skills`
Master catalog of technical, functional, and domain competencies.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `SKL-######` | String | Unique | Matches regex `^SKL-\d{6}$` | Natural Key |
| `name` | VARCHAR(150) | Required | Any distinct skill title | — | Unique | Max length 150 chars | — |
| `category` | VARCHAR(30) | Required | `TECHNICAL`, `DOMAIN`, `LEADERSHIP`, `METHODOLOGY`, `TOOL`, `COMPLIANCE` | Enum | Non-unique | Member of `SkillCategory` | — |
| `description` | TEXT | Optional | Open text syllabus | — | Non-unique | None | — |
| `is_active` | BOOLEAN | Required | `TRUE`, `FALSE` | Flag | Non-unique | Default `TRUE` | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 3. `role_skills`
Bridge table specifying competency requirements and weights for each job role.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `ROLSKL-######` | String | Unique | Matches regex `^ROLSKL-\d{6}$` | Natural Key |
| `role_id` | VARCHAR(36) | Required | Existing `roles.id` | Foreign Key | Composite Unique (`role_id`, `skill_id`) | Must reference active role; CASCADE on delete | FK → `roles.id` |
| `skill_id` | VARCHAR(36) | Required | Existing `skills.id` | Foreign Key | Composite Unique (`role_id`, `skill_id`) | Must reference active skill; RESTRICT on delete | FK → `skills.id` |
| `required_proficiency` | INTEGER | Required | `1`, `2`, `3`, `4`, `5` | Level (1–5) | Non-unique | `required_proficiency BETWEEN 1 AND 5` | — |
| `is_mandatory` | BOOLEAN | Required | `TRUE`, `FALSE` | Flag | Non-unique | Default `TRUE` | — |
| `importance_weight` | NUMERIC(3,2) | Required | Decimal between $0.00$ and $1.00$ | Weight | Non-unique | `importance_weight BETWEEN 0.00 AND 1.00` | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 4. `employees`
Core enterprise personnel records.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `EMP-######` | String | Unique | Matches regex `^EMP-\d{6}$` | Natural Key |
| `first_name` | VARCHAR(100) | Required | Non-empty text | — | Non-unique | Max length 100 chars | — |
| `last_name` | VARCHAR(100) | Required | Non-empty text | — | Non-unique | Max length 100 chars | — |
| `email` | VARCHAR(255) | Required | Valid email syntax | — | Unique | RFC 5322 email validation | — |
| `role_id` | VARCHAR(36) | Optional | Existing `roles.id` | Foreign Key | Non-unique | Must reference valid role; SET NULL on delete | FK → `roles.id` |
| `department` | VARCHAR(100) | Required | Operating unit name | — | Non-unique | Max length 100 chars | — |
| `location` | VARCHAR(100) | Required | Office location / region | — | Non-unique | Max length 100 chars | — |
| `employment_status` | VARCHAR(25) | Required | `ACTIVE`, `ON_LEAVE`, `TERMINATED`, `CONTRACTOR`, `PROBATION` | Enum | Non-unique | Member of `EmploymentStatus` | — |
| `hire_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `exit_date` | DATE | Optional | Valid calendar date | Date | Non-unique | `exit_date IS NULL OR exit_date >= hire_date` | — |
| `standard_hours_per_week` | NUMERIC(5,2) | Required | Decimal between $0.00$ and $80.00$ | Hours/Week | Non-unique | `standard_hours_per_week > 0.00 AND standard_hours_per_week <= 80.00` | — |
| `cost_rate_per_hour` | NUMERIC(10,2) | Optional | Decimal $\ge 0.00$ | USD/Hour | Non-unique | `cost_rate_per_hour IS NULL OR cost_rate_per_hour >= 0.00` | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 5. `employee_skills`
Bridge table linking employee competencies with verification audits and validity spans.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `EMPSKL-######` | String | Unique | Matches regex `^EMPSKL-\d{6}$` | Natural Key |
| `employee_id` | VARCHAR(36) | Required | Existing `employees.id` | Foreign Key | Composite Unique (`employee_id`, `skill_id`, `effective_start_date`) | CASCADE on delete | FK → `employees.id` |
| `skill_id` | VARCHAR(36) | Required | Existing `skills.id` | Foreign Key | Composite Unique (`employee_id`, `skill_id`, `effective_start_date`) | RESTRICT on delete | FK → `skills.id` |
| `proficiency_level` | INTEGER | Required | `1`, `2`, `3`, `4`, `5` | Level (1–5) | Non-unique | `proficiency_level BETWEEN 1 AND 5` | — |
| `verification_status` | VARCHAR(30) | Required | `SELF_REPORTED`, `PEER_REVIEWED`, `MANAGER_VERIFIED`, `ASSESSMENT_CERTIFIED`, `EXPIRED`, `REVOKED` | Enum | Non-unique | Member of `VerificationStatus` | — |
| `verified_by_id` | VARCHAR(36) | Optional | Existing `employees.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `employees.id` |
| `verified_at` | TIMESTAMPTZ | Optional | Valid UTC timestamp | ISO 8601 | Non-unique | Must be on or after `effective_start_date` | — |
| `effective_start_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `effective_end_date` | DATE | Optional | Valid calendar date | Date | Non-unique | `effective_end_date IS NULL OR effective_end_date >= effective_start_date` | — |
| `is_current` | BOOLEAN | Required | `TRUE`, `FALSE` | Flag | Non-unique | Default `TRUE` | — |
| `notes` | TEXT | Optional | Certification links, remarks | — | Non-unique | None | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 6. `availabilities`
Calendar capacity, leave schedules, and availability blocks.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `AVL-YYYY-######` | String | Unique | Matches regex `^AVL-\d{4}-\d{6}$` | Natural Key |
| `employee_id` | VARCHAR(36) | Required | Existing `employees.id` | Foreign Key | Non-unique | CASCADE on delete | FK → `employees.id` |
| `start_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `end_date` | DATE | Required | Valid calendar date | Date | Non-unique | `end_date >= start_date` | — |
| `availability_type` | VARCHAR(25) | Required | `AVAILABLE`, `HOLIDAY`, `PTO`, `SICK_LEAVE`, `TRAINING`, `BENCH`, `RESERVED` | Enum | Non-unique | Member of `AvailabilityType` | — |
| `available_hours_per_day` | NUMERIC(4,2) | Required | Decimal between $0.00$ and $24.00$ | Hours/Day | Non-unique | `available_hours_per_day BETWEEN 0.00 AND 24.00` | — |
| `capacity_percentage` | NUMERIC(5,2) | Required | Decimal between $0.00$ and $100.00$ | Percent | Non-unique | `capacity_percentage BETWEEN 0.00 AND 100.00` | — |
| `reason` | VARCHAR(255) | Optional | Leave reason / notes | — | Non-unique | Max length 255 chars | — |
| `is_approved` | BOOLEAN | Required | `TRUE`, `FALSE` | Flag | Non-unique | Default `TRUE` | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 7. `projects`
Initiatives, customer engagements, and programs.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `PRJ-YYYY-######` | String | Unique | Matches regex `^PRJ-\d{4}-\d{6}$` | Natural Key |
| `name` | VARCHAR(200) | Required | Non-empty project name | — | Non-unique | Max length 200 chars | — |
| `code` | VARCHAR(50) | Required | Unique billing identifier | — | Unique | Max length 50 chars | — |
| `client_name` | VARCHAR(150) | Optional | Client / sponsor name | — | Non-unique | Max length 150 chars | — |
| `department` | VARCHAR(100) | Required | Owning business unit | — | Non-unique | Max length 100 chars | — |
| `status` | VARCHAR(25) | Required | `PIPELINE`, `DRAFT`, `APPROVED`, `ACTIVE`, `ON_HOLD`, `COMPLETED`, `CANCELLED` | Enum | Non-unique | Member of `ProjectStatus` | — |
| `start_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `end_date` | DATE | Required | Valid calendar date | Date | Non-unique | `end_date >= start_date` | — |
| `budget` | NUMERIC(14,2) | Optional | Decimal $\ge 0.00$ | USD | Non-unique | `budget IS NULL OR budget >= 0.00` | — |
| `manager_id` | VARCHAR(36) | Optional | Existing `employees.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `employees.id` |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 8. `demand_plans`
Time-phased workforce demand line items per project.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(64) | Required | `DEM-<project-code>-YYYYWww` | String | Unique | Canonical demand identifier | Natural Key |
| `project_id` | VARCHAR(36) | Required | Existing `projects.id` | Foreign Key | Non-unique | CASCADE on delete | FK → `projects.id` |
| `role_id` | VARCHAR(36) | Required | Existing `roles.id` | Foreign Key | Non-unique | RESTRICT on delete | FK → `roles.id` |
| `primary_skill_id` | VARCHAR(36) | Optional | Existing `skills.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `skills.id` |
| `min_proficiency` | INTEGER | Required | `1`, `2`, `3`, `4`, `5` | Level (1–5) | Non-unique | `min_proficiency BETWEEN 1 AND 5` | — |
| `start_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `end_date` | DATE | Required | Valid calendar date | Date | Non-unique | `end_date >= start_date` | — |
| `week_number` | VARCHAR(10) | Optional | Format `YYYYWww` | ISO Week | Non-unique | Regex `^\d{4}W\d{2}$` | — |
| `required_headcount` | INTEGER | Required | Integer $\ge 1$ | Persons | Non-unique | `required_headcount > 0` | — |
| `required_hours` | NUMERIC(8,2) | Required | Decimal $> 0.00$ | Hours | Non-unique | `required_hours > 0.00` | — |
| `fulfilled_hours` | NUMERIC(8,2) | Required | Decimal $\ge 0.00$ | Hours | Non-unique | `fulfilled_hours >= 0.00` | — |
| `status` | VARCHAR(25) | Required | `DRAFT`, `SUBMITTED`, `APPROVED`, `FULFILLED`, `PARTIALLY_FULFILLED`, `CANCELLED` | Enum | Non-unique | Member of `DemandStatus` | — |
| `priority` | INTEGER | Required | `1`, `2`, `3`, `4`, `5` | Rating (1–5) | Non-unique | `priority BETWEEN 1 AND 5` | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 9. `allocations`
Staffing allocations linking employees to projects with historical supersession.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `ALLOC-YYYY-######` | String | Unique | Matches regex `^ALLOC-\d{4}-\d{6}$` | Natural Key |
| `employee_id` | VARCHAR(36) | Required | Existing `employees.id` | Foreign Key | Non-unique | RESTRICT on delete | FK → `employees.id` |
| `project_id` | VARCHAR(36) | Required | Existing `projects.id` | Foreign Key | Non-unique | CASCADE on delete | FK → `projects.id` |
| `demand_plan_id` | VARCHAR(36) | Optional | Existing `demand_plans.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `demand_plans.id` |
| `start_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `end_date` | DATE | Required | Valid calendar date | Date | Non-unique | `end_date >= start_date` | — |
| `allocation_percentage` | NUMERIC(5,2) | Required | Decimal between $0.00$ and $100.00$ | Percent | Non-unique | `allocation_percentage BETWEEN 0.00 AND 100.00` | — |
| `allocated_hours_per_week` | NUMERIC(6,2) | Required | Decimal $\ge 0.00$ | Hours/Week | Non-unique | `allocated_hours_per_week >= 0.00` | — |
| `hourly_billing_rate` | NUMERIC(10,2) | Optional | Decimal $\ge 0.00$ | USD/Hour | Non-unique | Non-negative if supplied | — |
| `status` | VARCHAR(25) | Required | `PROPOSED`, `CONFIRMED`, `ACTIVE`, `COMPLETED`, `CANCELLED`, `RELEASED` | Enum | Non-unique | Member of `AllocationStatus` | — |
| `version` | INTEGER | Required | Integer $\ge 1$ | Version | Non-unique | `version >= 1` | — |
| `is_active` | BOOLEAN | Required | `TRUE`, `FALSE` | Flag | Non-unique | Default `TRUE` | — |
| `superseded_by_id` | VARCHAR(36) | Optional | Existing `allocations.id` | Foreign Key | Non-unique | Self-reference to newer version | FK → `allocations.id` |
| `notes` | TEXT | Optional | Reallocation justification | — | Non-unique | None | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 10. `trainings`
Skill training initiatives, certifications, and upskilling pathways.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `TRN-YYYY-######` | String | Unique | Matches regex `^TRN-\d{4}-\d{6}$` | Natural Key |
| `title` | VARCHAR(200) | Required | Course / cert title | — | Non-unique | Max length 200 chars | — |
| `target_skill_id` | VARCHAR(36) | Required | Existing `skills.id` | Foreign Key | Non-unique | RESTRICT on delete | FK → `skills.id` |
| `employee_id` | VARCHAR(36) | Required | Existing `employees.id` | Foreign Key | Non-unique | CASCADE on delete | FK → `employees.id` |
| `provider` | VARCHAR(150) | Optional | Academy or vendor name | — | Non-unique | Max length 150 chars | — |
| `status` | VARCHAR(25) | Required | `PLANNED`, `ENROLLED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED` | Enum | Non-unique | Member of `TrainingStatus` | — |
| `start_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `completion_date` | DATE | Optional | Valid calendar date | Date | Non-unique | `completion_date IS NULL OR completion_date >= start_date` | — |
| `target_proficiency` | INTEGER | Required | `1`, `2`, `3`, `4`, `5` | Level (1–5) | Non-unique | `target_proficiency BETWEEN 1 AND 5` | — |
| `estimated_cost` | NUMERIC(10,2) | Required | Decimal $\ge 0.00$ | USD | Non-unique | `estimated_cost >= 0.00` | — |
| `actual_cost` | NUMERIC(10,2) | Optional | Decimal $\ge 0.00$ | USD | Non-unique | `actual_cost IS NULL OR actual_cost >= 0.00` | — |
| `notes` | TEXT | Optional | Curriculum details | — | Non-unique | None | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 11. `gap_analyses`
Recorded capability and capacity deficits between supply and demand.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `GAP-YYYY-######` | String | Unique | Matches regex `^GAP-\d{4}-\d{6}$` | Natural Key |
| `project_id` | VARCHAR(36) | Optional | Existing `projects.id` | Foreign Key | Non-unique | CASCADE on delete | FK → `projects.id` |
| `demand_plan_id` | VARCHAR(36) | Optional | Existing `demand_plans.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `demand_plans.id` |
| `skill_id` | VARCHAR(36) | Required | Existing `skills.id` | Foreign Key | Non-unique | RESTRICT on delete | FK → `skills.id` |
| `required_proficiency` | INTEGER | Required | `1`, `2`, `3`, `4`, `5` | Level (1–5) | Non-unique | `required_proficiency BETWEEN 1 AND 5` | — |
| `required_headcount` | INTEGER | Required | Integer $\ge 1$ | Persons | Non-unique | `required_headcount > 0` | — |
| `available_headcount` | INTEGER | Required | Integer $\ge 0$ | Persons | Non-unique | `available_headcount >= 0` | — |
| `deficit_headcount` | INTEGER | Required | Integer $\ge 0$ | Persons | Non-unique | `deficit_headcount >= 0` | — |
| `severity` | VARCHAR(20) | Required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Enum | Non-unique | Member of `GapSeverity` | — |
| `status` | VARCHAR(30) | Required | `IDENTIFIED`, `UNDER_REVIEW`, `MITIGATION_PLANNED`, `RESOLVED`, `ACCEPTED_RISK` | Enum | Non-unique | Member of `GapStatus` | — |
| `target_fulfillment_date` | DATE | Required | Valid calendar date | Date | Non-unique | Format `YYYY-MM-DD` | — |
| `analysis_date` | DATE | Required | Valid calendar date | Date | Non-unique | Snapshot execution date | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 12. `recommendations`
Actionable AI-generated staffing, hiring, and upskilling advice.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `REC-YYYY-######` | String | Unique | Matches regex `^REC-\d{4}-\d{6}$` | Natural Key |
| `gap_analysis_id` | VARCHAR(36) | Optional | Existing `gap_analyses.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `gap_analyses.id` |
| `target_employee_id` | VARCHAR(36) | Optional | Existing `employees.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `employees.id` |
| `target_project_id` | VARCHAR(36) | Optional | Existing `projects.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `projects.id` |
| `type` | VARCHAR(35) | Required | `INTERNAL_REALLOCATION`, `TRAINING_UPSKILL`, `EXTERNAL_HIRE`, `CONTRACTOR_CONTINGENT`, `PROJECT_TIMELINE_SHIFT` | Enum | Non-unique | Member of `RecommendationType` | — |
| `confidence_score` | NUMERIC(4,3) | Required | Decimal between $0.000$ and $1.000$ | Score | Non-unique | `confidence_score BETWEEN 0.000 AND 1.000` | — |
| `impact_summary` | TEXT | Required | Narrative outcome justification | — | Non-unique | None | — |
| `status` | VARCHAR(25) | Required | `GENERATED`, `UNDER_REVIEW`, `ACCEPTED`, `REJECTED`, `IMPLEMENTED`, `EXPIRED` | Enum | Non-unique | Member of `RecommendationStatus` | — |
| `estimated_cost` | NUMERIC(12,2) | Required | Decimal $\ge 0.00$ | USD | Non-unique | `estimated_cost >= 0.00` | — |
| `time_to_impact_days` | INTEGER | Optional | Integer $\ge 0$ | Days | Non-unique | `time_to_impact_days IS NULL OR time_to_impact_days >= 0` | — |
| `reviewed_by_id` | VARCHAR(36) | Optional | Existing `employees.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `employees.id` |
| `reviewed_at` | TIMESTAMPTZ | Optional | Valid UTC timestamp | ISO 8601 | Non-unique | Review decision time | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 13. `scenario_runs`
Predictive simulation runs testing supply/demand variables.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `SCN-YYYY-######` | String | Unique | Matches regex `^SCN-\d{4}-\d{6}$` | Natural Key |
| `name` | VARCHAR(150) | Required | Descriptive scenario title | — | Non-unique | Max length 150 chars | — |
| `description` | TEXT | Optional | Detailed hypothesis text | — | Non-unique | None | — |
| `status` | VARCHAR(20) | Required | `DRAFT`, `RUNNING`, `COMPLETED`, `FAILED`, `ARCHIVED` | Enum | Non-unique | Member of `ScenarioStatus` | — |
| `parameters` | JSON | Required | Valid JSON dictionary | Key/Value | Non-unique | Must be valid JSON object | — |
| `simulation_results` | JSON | Optional | Valid JSON dictionary | Key/Value | Non-unique | Must be valid JSON object | — |
| `executed_by_id` | VARCHAR(36) | Optional | Existing `employees.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `employees.id` |
| `execution_duration_ms`| INTEGER | Optional | Integer $\ge 0$ | Milliseconds| Non-unique | Runtime duration | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 14. `issue_records`
Detected allocation conflicts, overbooking, and critical staffing shortages.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `ISS-YYYY-######` | String | Unique | Matches regex `^ISS-\d{4}-\d{6}$` | Natural Key |
| `project_id` | VARCHAR(36) | Optional | Existing `projects.id` | Foreign Key | Non-unique | CASCADE on delete | FK → `projects.id` |
| `employee_id` | VARCHAR(36) | Optional | Existing `employees.id` | Foreign Key | Non-unique | CASCADE on delete | FK → `employees.id` |
| `issue_type` | VARCHAR(35) | Required | `CAPACITY_OVERLOAD`, `SKILL_SHORTAGE`, `ALLOCATION_CONFLICT`, `ATTRITION_RISK`, `UNFULFILLED_DEMAND` | Enum | Non-unique | Member of `IssueType` | — |
| `severity` | VARCHAR(20) | Required | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Enum | Non-unique | Member of `IssueSeverity` | — |
| `status` | VARCHAR(20) | Required | `OPEN`, `IN_PROGRESS`, `MITIGATED`, `RESOLVED`, `IGNORED` | Enum | Non-unique | Member of `IssueStatus` | — |
| `title` | VARCHAR(200) | Required | Summary headline | — | Non-unique | Max length 200 chars | — |
| `description` | TEXT | Required | Technical diagnosis of root cause | — | Non-unique | None | — |
| `detected_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on detection | — |
| `resolved_at` | TIMESTAMPTZ | Optional | Valid UTC timestamp | ISO 8601 | Non-unique | Must be on or after `detected_at` | — |
| `created_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `updated_at` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-updated on modification | — |

---

### 15. `audit_events`
Immutable compliance audit trail tracking all state mutations.

| Field Name | Data Type | Nullability | Allowed Values | Unit | Uniqueness | Validation Rule | Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | Required | UUID v4 strings | — | Primary Key | Valid 36-char UUID format | PK |
| `business_id` | VARCHAR(32) | Required | `AUD-YYYY-######` | String | Unique | Matches regex `^AUD-\d{4}-\d{6}$` | Natural Key |
| `entity_type` | VARCHAR(50) | Required | Model class name | — | Non-unique | e.g. `Allocation`, `EmployeeSkill` | — |
| `entity_id` | VARCHAR(64) | Required | Record ID / Business ID | — | Non-unique | Max length 64 chars | — |
| `action` | VARCHAR(20) | Required | `INSERT`, `UPDATE`, `DELETE`, `VERIFY`, `ALLOCATE`, `SIMULATE` | Enum | Non-unique | Member of `AuditAction` | — |
| `performed_by_id` | VARCHAR(36) | Optional | Existing `employees.id` | Foreign Key | Non-unique | SET NULL on delete | FK → `employees.id` |
| `timestamp` | TIMESTAMPTZ | Required | Valid UTC timestamp | ISO 8601 | Non-unique | Auto-populated on creation | — |
| `ip_address` | VARCHAR(45) | Optional | IPv4 or IPv6 address | IP | Non-unique | Valid IP format | — |
| `old_values` | JSON | Optional | Valid JSON dictionary | Key/Value | Non-unique | Previous state snapshot | — |
| `new_values` | JSON | Optional | Valid JSON dictionary | Key/Value | Non-unique | Current state snapshot | — |
| `reason` | TEXT | Optional | Operator change justification | — | Non-unique | None | — |

