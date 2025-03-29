"""
Schema validation utilities for Berrys_AgentsV2.

This module provides utilities for database schema validation, including:
- Extracting schema definitions from databases
- Comparing schema definitions between different environments
- Detecting schema drift
- Validating schema consistency
"""

import difflib
import json
from typing import Dict, List, Any, Optional, Tuple, Set, Type, Union
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import inspect, MetaData, Table, Column, ForeignKey
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import class_mapper, RelationshipProperty
from sqlalchemy.engine import Engine


class SchemaComparisonResult(Enum):
    """Result of a schema comparison."""
    IDENTICAL = "identical"
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"


class SchemaValidator:
    """
    Validator for database schemas.
    
    This class provides methods for validating database schemas,
    comparing schemas between different environments, and detecting
    schema drift.
    """
    
    def __init__(self, engine: sa.engine.Engine):
        """
        Initialize the schema validator.
        
        Args:
            engine: SQLAlchemy engine instance.
        """
        self.engine = engine
        self.inspector = inspect(engine)
        
    def get_table_names(self) -> List[str]:
        """
        Get all table names in the database.
        
        Returns:
            List of table names.
        """
        return self.inspector.get_table_names()
        
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all columns for a table.
        
        Args:
            table_name: Name of the table.
            
        Returns:
            List of column definitions.
        """
        return self.inspector.get_columns(table_name)
        
    def get_table_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all foreign keys for a table.
        
        Args:
            table_name: Name of the table.
            
        Returns:
            List of foreign key definitions.
        """
        return self.inspector.get_foreign_keys(table_name)
        
    def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all indexes for a table.
        
        Args:
            table_name: Name of the table.
            
        Returns:
            List of index definitions.
        """
        return self.inspector.get_indexes(table_name)
        
    def get_table_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all constraints for a table.
        
        Args:
            table_name: Name of the table.
            
        Returns:
            List of constraint definitions.
        """
        return self.inspector.get_unique_constraints(table_name)
        
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get the complete schema for a table.
        
        Args:
            table_name: Name of the table.
            
        Returns:
            Table schema as a dictionary.
        """
        return {
            "columns": self.get_table_columns(table_name),
            "foreign_keys": self.get_table_foreign_keys(table_name),
            "indexes": self.get_table_indexes(table_name),
            "constraints": self.get_table_constraints(table_name)
        }
        
    def get_database_schema(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the complete schema for the database.
        
        Returns:
            Database schema as a dictionary.
        """
        schema = {}
        for table_name in self.get_table_names():
            schema[table_name] = self.get_table_schema(table_name)
        return schema
        
    def compare_schema_with_models(
        self, 
        base_class: Type[DeclarativeMeta]
    ) -> Dict[str, Any]:
        """
        Compare database schema with SQLAlchemy models.
        
        Args:
            base_class: SQLAlchemy declarative base class.
            
        Returns:
            Dictionary containing differences between the database schema and the models.
        """
        metadata = base_class.metadata
        model_tables = metadata.tables
        
        db_tables = self.get_table_names()
        
        # Check for missing tables
        missing_tables = set(model_tables.keys()) - set(db_tables)
        extra_tables = set(db_tables) - set(model_tables.keys())
        
        # Check for column differences
        column_differences = {}
        for table_name in set(model_tables.keys()).intersection(set(db_tables)):
            db_columns = {col["name"]: col for col in self.get_table_columns(table_name)}
            model_columns = {col.name: col for col in model_tables[table_name].columns}
            
            missing_columns = set(model_columns.keys()) - set(db_columns.keys())
            extra_columns = set(db_columns.keys()) - set(model_columns.keys())
            
            if missing_columns or extra_columns:
                column_differences[table_name] = {
                    "missing_columns": list(missing_columns),
                    "extra_columns": list(extra_columns)
                }
                
        return {
            "missing_tables": list(missing_tables),
            "extra_tables": list(extra_tables),
            "column_differences": column_differences
        }
        
    def compare_schemas(
        self, 
        other_schema: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare this database schema with another schema.
        
        Args:
            other_schema: Another database schema.
            
        Returns:
            Dictionary containing differences between the schemas.
        """
        this_schema = self.get_database_schema()
        
        # Check for missing and extra tables
        this_tables = set(this_schema.keys())
        other_tables = set(other_schema.keys())
        
        missing_tables = other_tables - this_tables
        extra_tables = this_tables - other_tables
        
        # Check for differences in common tables
        table_differences = {}
        for table_name in this_tables.intersection(other_tables):
            differences = self._compare_table_schemas(
                this_schema[table_name],
                other_schema[table_name]
            )
            if differences:
                table_differences[table_name] = differences
                
        return {
            "missing_tables": list(missing_tables),
            "extra_tables": list(extra_tables),
            "table_differences": table_differences
        }
        
    def _compare_table_schemas(
        self, 
        this_table: Dict[str, Any], 
        other_table: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two table schemas.
        
        Args:
            this_table: This table schema.
            other_table: Other table schema.
            
        Returns:
            Dictionary containing differences between the table schemas.
        """
        differences = {}
        
        # Compare columns
        this_columns = {col["name"]: col for col in this_table["columns"]}
        other_columns = {col["name"]: col for col in other_table["columns"]}
        
        missing_columns = set(other_columns.keys()) - set(this_columns.keys())
        extra_columns = set(this_columns.keys()) - set(other_columns.keys())
        
        # Compare column attributes for common columns
        column_differences = {}
        for col_name in set(this_columns.keys()).intersection(set(other_columns.keys())):
            col_diff = self._compare_column_definitions(
                this_columns[col_name],
                other_columns[col_name]
            )
            if col_diff:
                column_differences[col_name] = col_diff
                
        if missing_columns or extra_columns or column_differences:
            differences["columns"] = {
                "missing": list(missing_columns),
                "extra": list(extra_columns),
                "differences": column_differences
            }
            
        # Compare foreign keys
        differences["foreign_keys"] = self._compare_foreign_keys(
            this_table["foreign_keys"],
            other_table["foreign_keys"]
        )
        
        # Compare indexes
        differences["indexes"] = self._compare_indexes(
            this_table["indexes"],
            other_table["indexes"]
        )
        
        # Compare constraints
        differences["constraints"] = self._compare_constraints(
            this_table["constraints"],
            other_table["constraints"]
        )
        
        # Remove empty differences
        differences = {k: v for k, v in differences.items() if v}
        
        return differences
        
    def _compare_column_definitions(
        self, 
        this_column: Dict[str, Any], 
        other_column: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two column definitions.
        
        Args:
            this_column: This column definition.
            other_column: Other column definition.
            
        Returns:
            Dictionary containing differences between the column definitions.
        """
        differences = {}
        
        # Compare type
        if str(this_column.get("type")) != str(other_column.get("type")):
            differences["type"] = {
                "this": str(this_column.get("type")),
                "other": str(other_column.get("type"))
            }
            
        # Compare nullability
        if this_column.get("nullable") != other_column.get("nullable"):
            differences["nullable"] = {
                "this": this_column.get("nullable"),
                "other": other_column.get("nullable")
            }
            
        # Compare default
        if str(this_column.get("default")) != str(other_column.get("default")):
            differences["default"] = {
                "this": str(this_column.get("default")),
                "other": str(other_column.get("default"))
            }
            
        return differences
        
    def _compare_foreign_keys(
        self, 
        this_fks: List[Dict[str, Any]], 
        other_fks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare two lists of foreign key definitions.
        
        Args:
            this_fks: This list of foreign key definitions.
            other_fks: Other list of foreign key definitions.
            
        Returns:
            Dictionary containing differences between the foreign key definitions.
        """
        # Convert FKs to sets for comparison
        this_fk_set = {self._fk_to_string(fk) for fk in this_fks}
        other_fk_set = {self._fk_to_string(fk) for fk in other_fks}
        
        missing_fks = other_fk_set - this_fk_set
        extra_fks = this_fk_set - other_fk_set
        
        if missing_fks or extra_fks:
            return {
                "missing": list(missing_fks),
                "extra": list(extra_fks)
            }
            
        return {}
        
    def _fk_to_string(self, fk: Dict[str, Any]) -> str:
        """
        Convert a foreign key definition to a string for comparison.
        
        Args:
            fk: Foreign key definition.
            
        Returns:
            String representation of the foreign key.
        """
        return f"{fk.get('referred_table')}.{','.join(fk.get('referred_columns'))} <- {','.join(fk.get('constrained_columns'))}"
        
    def _compare_indexes(
        self, 
        this_indexes: List[Dict[str, Any]], 
        other_indexes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare two lists of index definitions.
        
        Args:
            this_indexes: This list of index definitions.
            other_indexes: Other list of index definitions.
            
        Returns:
            Dictionary containing differences between the index definitions.
        """
        # Convert indexes to sets for comparison
        this_index_set = {self._index_to_string(idx) for idx in this_indexes}
        other_index_set = {self._index_to_string(idx) for idx in other_indexes}
        
        missing_indexes = other_index_set - this_index_set
        extra_indexes = this_index_set - other_index_set
        
        if missing_indexes or extra_indexes:
            return {
                "missing": list(missing_indexes),
                "extra": list(extra_indexes)
            }
            
        return {}
        
    def _index_to_string(self, idx: Dict[str, Any]) -> str:
        """
        Convert an index definition to a string for comparison.
        
        Args:
            idx: Index definition.
            
        Returns:
            String representation of the index.
        """
        return f"{idx.get('name')}: {','.join(idx.get('column_names'))} (unique: {idx.get('unique', False)})"
        
    def _compare_constraints(
        self, 
        this_constraints: List[Dict[str, Any]], 
        other_constraints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare two lists of constraint definitions.
        
        Args:
            this_constraints: This list of constraint definitions.
            other_constraints: Other list of constraint definitions.
            
        Returns:
            Dictionary containing differences between the constraint definitions.
        """
        # Convert constraints to sets for comparison
        this_constraint_set = {self._constraint_to_string(c) for c in this_constraints}
        other_constraint_set = {self._constraint_to_string(c) for c in other_constraints}
        
        missing_constraints = other_constraint_set - this_constraint_set
        extra_constraints = this_constraint_set - other_constraint_set
        
        if missing_constraints or extra_constraints:
            return {
                "missing": list(missing_constraints),
                "extra": list(extra_constraints)
            }
            
        return {}
        
    def _constraint_to_string(self, constraint: Dict[str, Any]) -> str:
        """
        Convert a constraint definition to a string for comparison.
        
        Args:
            constraint: Constraint definition.
            
        Returns:
            String representation of the constraint.
        """
        return f"{constraint.get('name')}: {','.join(constraint.get('column_names'))}"


class SchemaDriftDetector:
    """
    Detector for schema drift between different environments.
    
    This class provides methods for detecting schema drift between
    different environments, such as development, staging, and production.
    """
    
    def __init__(self, engines: Dict[str, sa.engine.Engine]):
        """
        Initialize the schema drift detector.
        
        Args:
            engines: Dictionary mapping environment names to SQLAlchemy engine instances.
        """
        self.validators = {env: SchemaValidator(engine) for env, engine in engines.items()}
        
    def detect_drift(
        self, 
        reference_env: str, 
        target_env: str
    ) -> Dict[str, Any]:
        """
        Detect schema drift between two environments.
        
        Args:
            reference_env: Name of the reference environment.
            target_env: Name of the target environment.
            
        Returns:
            Dictionary containing differences between the environments.
        """
        if reference_env not in self.validators:
            raise ValueError(f"Reference environment '{reference_env}' not found")
            
        if target_env not in self.validators:
            raise ValueError(f"Target environment '{target_env}' not found")
            
        reference_schema = self.validators[reference_env].get_database_schema()
        
        return self.validators[target_env].compare_schemas(reference_schema)
        
    def detect_all_drift(self, reference_env: str) -> Dict[str, Dict[str, Any]]:
        """
        Detect schema drift between the reference environment and all other environments.
        
        Args:
            reference_env: Name of the reference environment.
            
        Returns:
            Dictionary mapping environment names to drift results.
        """
        if reference_env not in self.validators:
            raise ValueError(f"Reference environment '{reference_env}' not found")
            
        results = {}
        for env in self.validators:
            if env != reference_env:
                results[env] = self.detect_drift(reference_env, env)
                
        return results
        
    def summarize_drift(
        self, 
        drift_result: Dict[str, Any]
    ) -> SchemaComparisonResult:
        """
        Summarize the drift result.
        
        Args:
            drift_result: Drift result from detect_drift.
            
        Returns:
            Schema comparison result.
        """
        if not drift_result["missing_tables"] and not drift_result["extra_tables"] and not drift_result["table_differences"]:
            return SchemaComparisonResult.IDENTICAL
            
        # Check for incompatible differences (e.g., column type changes)
        for table_name, differences in drift_result.get("table_differences", {}).items():
            if "columns" in differences:
                column_diffs = differences["columns"]
                if column_diffs.get("differences"):
                    for col_name, col_diffs in column_diffs["differences"].items():
                        if "type" in col_diffs or "nullable" in col_diffs:
                            return SchemaComparisonResult.INCOMPATIBLE
                            
        # If we get here, the schemas are compatible but not identical
        return SchemaComparisonResult.COMPATIBLE


def format_schema_diff(
    diff_result: Dict[str, Any], 
    indent: int = 2
) -> str:
    """
    Format a schema diff result as a human-readable string.
    
    Args:
        diff_result: Schema diff result from SchemaValidator.compare_schemas.
        indent: Number of spaces to use for indentation.
        
    Returns:
        Formatted string representation of the schema diff.
    """
    lines = []
    
    if diff_result.get("missing_tables"):
        lines.append("Missing Tables:")
        for table in sorted(diff_result["missing_tables"]):
            lines.append(f"{' ' * indent}- {table}")
        lines.append("")
        
    if diff_result.get("extra_tables"):
        lines.append("Extra Tables:")
        for table in sorted(diff_result["extra_tables"]):
            lines.append(f"{' ' * indent}+ {table}")
        lines.append("")
        
    if diff_result.get("table_differences"):
        lines.append("Table Differences:")
        for table_name, differences in sorted(diff_result["table_differences"].items()):
            lines.append(f"{' ' * indent}Table: {table_name}")
            
            if "columns" in differences:
                column_diffs = differences["columns"]
                
                if column_diffs.get("missing"):
                    lines.append(f"{' ' * (indent * 2)}Missing Columns:")
                    for col in sorted(column_diffs["missing"]):
                        lines.append(f"{' ' * (indent * 3)}- {col}")
                        
                if column_diffs.get("extra"):
                    lines.append(f"{' ' * (indent * 2)}Extra Columns:")
                    for col in sorted(column_diffs["extra"]):
                        lines.append(f"{' ' * (indent * 3)}+ {col}")
                        
                if column_diffs.get("differences"):
                    lines.append(f"{' ' * (indent * 2)}Column Differences:")
                    for col_name, col_diffs in sorted(column_diffs["differences"].items()):
                        lines.append(f"{' ' * (indent * 3)}Column: {col_name}")
                        for attr, values in sorted(col_diffs.items()):
                            lines.append(f"{' ' * (indent * 4)}{attr}:")
                            lines.append(f"{' ' * (indent * 5)}- {values['this']}")
                            lines.append(f"{' ' * (indent * 5)}+ {values['other']}")
                            
            if "foreign_keys" in differences:
                fk_diffs = differences["foreign_keys"]
                
                if fk_diffs.get("missing"):
                    lines.append(f"{' ' * (indent * 2)}Missing Foreign Keys:")
                    for fk in sorted(fk_diffs["missing"]):
                        lines.append(f"{' ' * (indent * 3)}- {fk}")
                        
                if fk_diffs.get("extra"):
                    lines.append(f"{' ' * (indent * 2)}Extra Foreign Keys:")
                    for fk in sorted(fk_diffs["extra"]):
                        lines.append(f"{' ' * (indent * 3)}+ {fk}")
                        
            if "indexes" in differences:
                idx_diffs = differences["indexes"]
                
                if idx_diffs.get("missing"):
                    lines.append(f"{' ' * (indent * 2)}Missing Indexes:")
                    for idx in sorted(idx_diffs["missing"]):
                        lines.append(f"{' ' * (indent * 3)}- {idx}")
                        
                if idx_diffs.get("extra"):
                    lines.append(f"{' ' * (indent * 2)}Extra Indexes:")
                    for idx in sorted(idx_diffs["extra"]):
                        lines.append(f"{' ' * (indent * 3)}+ {idx}")
                        
            if "constraints" in differences:
                constraint_diffs = differences["constraints"]
                
                if constraint_diffs.get("missing"):
                    lines.append(f"{' ' * (indent * 2)}Missing Constraints:")
                    for c in sorted(constraint_diffs["missing"]):
                        lines.append(f"{' ' * (indent * 3)}- {c}")
                        
                if constraint_diffs.get("extra"):
                    lines.append(f"{' ' * (indent * 2)}Extra Constraints:")
                    for c in sorted(constraint_diffs["extra"]):
                        lines.append(f"{' ' * (indent * 3)}+ {c}")
                        
            lines.append("")
            
    return "\n".join(lines)


def get_model_relationships(model_class: Type) -> Dict[str, Any]:
    """
    Get all relationships for a model class.
    
    Args:
        model_class: SQLAlchemy model class.
        
    Returns:
        Dictionary mapping relationship names to relationship properties.
    """
    mapper = class_mapper(model_class)
    return {rel.key: rel for rel in mapper.relationships}


def visualize_schema_relationships(
    base_class: Type[DeclarativeMeta]
) -> str:
    """
    Visualize schema relationships as a PlantUML diagram.
    
    Args:
        base_class: SQLAlchemy declarative base class.
        
    Returns:
        PlantUML diagram string.
    """
    lines = ["@startuml", ""]
    
    # Get all models from the base class
    models = {}
    for cls in base_class.__subclasses__():
        if hasattr(cls, "__tablename__"):
            models[cls.__tablename__] = cls
            
    # For each model, add a class definition
    for table_name, model in sorted(models.items()):
        lines.append(f"class {model.__name__} {{")
        
        # Add columns
        for column in model.__table__.columns:
            nullable = "?" if column.nullable else ""
            default = f" = {column.default.arg}" if column.default is not None and not callable(column.default.arg) else ""
            lines.append(f"  {column.name} : {column.type}{nullable}{default}")
            
        lines.append("}")
        lines.append("")
        
    # For each model, add relationships
    for table_name, model in sorted(models.items()):
        relationships = get_model_relationships(model)
        
        for rel_name, rel in sorted(relationships.items()):
            target_cls = rel.mapper.class_
            multiplicity = "--" if rel.uselist else "-"
            
            lines.append(f"{model.__name__} {multiplicity}> {target_cls.__name__} : {rel_name}")
            
    lines.append("")
    lines.append("@enduml")
    
    return "\n".join(lines)
