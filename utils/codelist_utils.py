import pandas as pd
import requests
import os
from typing import Dict


class Codelists:
    """
    Utility class for working with GLEIF code lists and adding descriptive information
    to dataframes.
    """

    def __init__(self, cache_dir: str = "./cache"):
        """
        Initialize the Codelists class.

        Args:
            cache_dir: Directory to cache downloaded files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._ra_mapping = None

    def _download_ra_list(self) -> pd.DataFrame:
        """
        Download the GLEIF Registration Authorities list from the GLEIF website.

        Returns:
            DataFrame with registration authority codelist
        """
        url = "https://www.gleif.org/lei-data/code-lists/gleif-registration-authorities-list/2024-11-20_ra-list-v1.8.1.csv"
        cache_file = os.path.join(self.cache_dir, "ra-list-v1.8.1.csv")

        # Check if file is already cached
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file, encoding="utf-8")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save to cache with UTF-8 encoding
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(response.text)

            print("Registration authorities list downloaded and cached successfully")
            return pd.read_csv(cache_file, encoding="utf-8")

        except Exception as e:
            print(f"Error downloading registration authorities list: {e}")
            raise

    def _create_ra_mapping(self) -> Dict[str, str]:
        """
        Create a mapping from Registration Authority Code to any available name.

        Returns:
            Dictionary mapping RA codes to concatenated names
        """
        if self._ra_mapping is not None:
            return self._ra_mapping

        df = self._download_ra_list()

        # Create concatenated name combining the three required fields
        def create_concatenated_name(row):
            parts = []

            # International name of Register
            if (
                pd.notna(row.get("International name of Register"))
                and row.get("International name of Register").strip()
            ):
                parts.append(str(row.get("International name of Register")).strip())

            # International name of organisation responsible for the Register
            if (
                pd.notna(
                    row.get(
                        "International name of organisation responsible for the Register"
                    )
                )
                and row.get(
                    "International name of organisation responsible for the Register"
                ).strip()
            ):
                parts.append(
                    str(
                        row.get(
                            "International name of organisation responsible for the Register"
                        )
                    ).strip()
                )

            # Local name of organisation responsible for the Register
            if (
                pd.notna(
                    row.get("Local name of organisation responsible for the Register")
                )
                and row.get(
                    "Local name of organisation responsible for the Register"
                ).strip()
            ):
                parts.append(
                    str(
                        row.get(
                            "Local name of organisation responsible for the Register"
                        )
                    ).strip()
                )

            # Join with " | " separator if multiple parts exist
            return " | ".join(parts) if parts else None

        # Find the correct column name for Registration Authority Code
        ra_code_col = None
        for col in df.columns:
            if (
                "registration" in col.lower()
                and "authority" in col.lower()
                and "code" in col.lower()
            ):
                ra_code_col = col
                break

        if ra_code_col is None:
            raise ValueError(
                f"Could not find Registration Authority Code column. Available columns: {list(df.columns)}"
            )

        # Create the mapping
        self._ra_mapping = {}
        for _, row in df.iterrows():
            ra_code = row.get(ra_code_col)
            if pd.notna(ra_code):
                self._ra_mapping[str(ra_code)] = create_concatenated_name(row)

        return self._ra_mapping

    def addRegistrationauthorityName(self, ra_codes_column) -> pd.DataFrame:
        """
        Add registration authority names based on Registration Authority codes.

        Args:
            ra_codes_column: Pandas Series, list, or array containing Registration Authority codes

        Returns:
            DataFrame with original RA codes column and added 'registration_authority_name' column
        """
        # Convert input to pandas Series if it isn't already
        if not isinstance(ra_codes_column, pd.Series):
            ra_codes_column = pd.Series(ra_codes_column)

        # Get the RA mapping
        ra_mapping = self._create_ra_mapping()

        # Create result DataFrame with original column (reset index to avoid showing index numbers)
        df_result = pd.DataFrame(
            {"registration_authority_code": ra_codes_column},
            index=ra_codes_column.index,
        ).reset_index(drop=True)

        # Map the registration authority codes to names
        df_result["registration_authority_name"] = df_result[
            "registration_authority_code"
        ].map(ra_mapping)

        # Replace NaN values with empty strings for cleaner output
        df_result["registration_authority_name"] = df_result[
            "registration_authority_name"
        ].fillna("")

        return df_result.reset_index(drop=True)
