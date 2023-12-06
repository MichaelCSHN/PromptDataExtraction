import pylogg as log
from backend.post_process.validator import DataValidator

class NameValidator(DataValidator):
    def __init__(self, db, method, meta) -> None:
        """ For a specific extraction method, identify the rows
        of extracted_properties having invalid property names.
        """
        super().__init__(db, method)

        # Set required parameters
        self.filter_name = 'invalid_property_name'
        self.table_name = 'extracted_properties'
        self.prop_meta = meta

    def _get_record_sql(self) -> str:
        return """
            SELECT * FROM (
                SELECT
                    ep.id,
                    ep.entity_name
                FROM extracted_properties ep
                -- filter with extraction method
                WHERE ep.method_id = :mid
                AND ep.id > :last ORDER BY ep.id
            ) AS ft
            -- Ignore previously processed ones
            WHERE NOT EXISTS (
                SELECT 1 FROM filtered_data fd 
                WHERE fd.filter_name = :filter
                AND fd.target_table = :table
                AND fd.target_id = ft.id
            );
        """
    
    def _check_filter(self, row) -> bool:
        """ Returns True if row passes the invalid name filter. """

        # Lowercase
        name = row.entity_name.lower()
        namelist = [n.lower() for n in self.prop_meta.other_names]

        if name in namelist:
            return False

        log.warn("Invalid property name: {} ({})", row.entity_name, row.id)
        return True


class RangeValidator(DataValidator):
    def __init__(self, db, method, meta) -> None:
        """ For a specific extraction method, identify the rows
        of extracted_properties having out of range values.
        """
        super().__init__(db, method)

        # Set required parameters
        self.filter_name = 'out_of_range'
        self.table_name = 'extracted_properties'
        self.prop_meta = meta


    def _get_record_sql(self) -> str:
        return """
            SELECT * FROM (
                SELECT
                    ep.id,
                    ep.numeric_value as value
                FROM extracted_properties ep
                -- filter with extraction method
                WHERE ep.method_id = :mid
                AND ep.id > :last ORDER BY ep.id
            ) AS ft
            -- Ignore previously processed ones
            WHERE NOT EXISTS (
                SELECT 1 FROM filtered_data fd 
                WHERE fd.filter_name = :filter
                AND fd.target_table = :table
                AND fd.target_id = ft.id
            );
        """
    
    def _check_filter(self, row) -> bool:
        """ Return True if row passes the out of range filter. """

        criteria = [
            row.value <= self.prop_meta.upper_limit,
            row.value >= self.prop_meta.lower_limit,
        ]

        if all(criteria):
            return False
        
        log.warn("Out of range property value: {} ({})", row.value, row.id)
        return True


class UnitValidator(DataValidator):
    """ For a specific extraction method, identify the rows
    of extracted_properties having invalid unit.
    """
    def __init__(self, db, method, meta) -> None:
        super().__init__(db, method)

        # Set required parameters
        self.filter_name = 'invalid_property_unit'
        self.table_name = 'extracted_properties'
        self.prop_meta = meta


    def _get_record_sql(self) -> str:
        return """
            SELECT * FROM (
                SELECT
                    ep.id,
                    ep.unit as value
                FROM extracted_properties ep
                -- filter with extraction method
                WHERE ep.method_id = :mid
                AND ep.id > :last ORDER BY ep.id
            ) AS ft
            -- Ignore previously processed ones
            WHERE NOT EXISTS (
                SELECT 1 FROM filtered_data fd 
                WHERE fd.filter_name = :filter
                AND fd.target_table = :table
                AND fd.target_id = ft.id
            );
        """
    
    def _check_filter(self, row) -> bool:
        """ Return True if row passes the invalid unit filter. """

        # Handle None, lowercase
        unit = row.value.lower() if row.value else ""
        unitlist = [u.lower() for u in self.prop_meta.units]

        criteria = [
            unit in unitlist,
            # no unit
            len(unit) == 0 and len(unitlist) == 0
        ]

        if any(criteria):
            return False
        
        log.warn("Invalid property unit: {} ({})", unit, row.id)
        return True


class NERNameValidator(DataValidator):
    def __init__(self, db, method, meta) -> None:
        """ For a specific property meta information, identify the rows
        of extracted_properties having matching property names.
        """
        super().__init__(db, method)

        # Set required parameters
        self.filter_name = 'valid_property_name'
        self.table_name = 'extracted_properties'
        self.prop_meta = meta

    def _get_record_sql(self) -> str:
        return """
            SELECT * FROM (
                SELECT
                    ep.id,
                    ep.entity_name
                FROM extracted_properties ep
                -- filter with extraction method
                WHERE ep.method_id = :mid
                AND ep.id > :last ORDER BY ep.id
            ) AS ft
            -- Ignore previously processed ones
            WHERE NOT EXISTS (
                SELECT 1 FROM filtered_data fd 
                WHERE fd.filter_name = :filter
                AND fd.target_table = :table
                AND fd.target_id = ft.id
            );
        """
    
    def _check_filter(self, row) -> bool:
        """ Returns True if row passes the matching name filter. """

        # Lowercase
        name = row.entity_name.lower()
        namelist = [n.lower() for n in self.prop_meta.other_names]

        if name in namelist:
            log.info("Matching property name: {} ({})", row.entity_name, row.id)
            return True

        return False
