import os
import re
import zipfile
import pandas as pd
import requests
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from typing import Optional, List, Union
import io

class GoldenCopyDownload:
    """Downloader for GLEIF Golden Copy files."""

    EXT_BY_TYPE = {
        "csv": ".csv", 
        "json": ".json",
        "xml": ".xml",
    }
    TARGET_DATETIME = re.compile(r"(20\d{6})[-_](\d{4})")  # e.g., 20250813-0800

    def __init__(self, page_url, save_dir="./gc_downloads"):
        """
        Args:
            page_url (str): page URL to search (first success wins)
            save_dir (str): Folder where downloaded files are stored
        """
        self.page_url = page_url
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    @classmethod
    async def download_for_date(cls, date: str, save_dir: str = "./gc_downloads"):
        """
        Class method to download GLEIF Golden Copy for a specific date.
        This is a more convenient way to use the downloader.

        Args:
            date (str): Date in YYYY-MM-DD format
            save_dir (str): Directory to save the downloaded file

        Returns:
            str: Path to downloaded file, or None if failed
        """
        downloader = cls(
            page_url="https://goldencopy.gleif.org/api/v2/golden-copies/publishes/",
            save_dir=save_dir,
        )
        return await downloader.prepare_download(date)

    @classmethod
    def _extract_timestamp_from_url(cls, url: str):
        """Extract a datetime object from a URL based on the filename token."""
        match = cls.TARGET_DATETIME.search(url)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M")
        except ValueError:
            return None

    async def find_download_url(
        self, date_str: str, time_str: str, filetype: str, variant: str
    ):
        """
        Search for the matching download link.

        Args:
            date_str (str): YYYY-MM-DD
            time_str (str): HH:MM (24h) or "" to ignore time
            filetype (str): "csv", "json", "xml"
            variant (str): "lei2", "rr", "repex"

        Returns:
            str: Download URL
        """
        filetype = filetype.lower()
        variant = variant.lower()

        if filetype not in self.EXT_BY_TYPE:
            raise ValueError(
                f"Invalid filetype '{filetype}'. Choose from: {list(self.EXT_BY_TYPE)}"
            )

        want_ext = self.EXT_BY_TYPE[filetype]

        # Build token like 20250922-0000 from date and time (default 00:00)
        normalized_time = time_str if time_str else "00:00"
        dt_obj = datetime.strptime(f"{date_str} {normalized_time}", "%Y-%m-%d %H:%M")
        time_token = dt_obj.strftime("%Y%m%d-%H%M")

        base = self.page_url.rstrip("/")
        return f"{base}/{variant}/{time_token}{want_ext}"


    def download_file(self, url: str):
        """
        Download a file from URL to save_dir, using server filename if provided.
        If file already exists, skip download.

        Returns:
            str: Path to the file
        """
        filename = (
            url.split("/")[-1] or f"download-{int(datetime.now().timestamp())}.zip"
        )
        save_path = os.path.join(self.save_dir, filename)

        # Skip if already exists
        if os.path.exists(save_path):
            print(f"File already exists, skipping download: {save_path}")
            return os.path.abspath(save_path)

        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            cd = r.headers.get("Content-Disposition", "")
            match = re.search(r'filename="?([^"]+)"?', cd, re.I)
            if match and match.group(1):
                filename = match.group(1)
                save_path = os.path.join(self.save_dir, filename)

            with open(save_path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)

        print(f"Downloaded file: {save_path}")
        return os.path.abspath(save_path)

    async def prepare_download(self, date: str):
        """
        Prepare the downloader for the given date.
        Returns the file path if successful, None if failed.
        """
        try:
            # Try to get available file
            url = await self.find_download_url(date, "00:00", "csv", "lei2")
            print(url)
            print("Found URL for:", url)

            # Download the file (your downloader should skip if it already exists)
            file_path = self.download_file(url)
            print("File ready at:", file_path)
            return file_path

        except Exception as e:
            print(f"Failed to download file for date {date}: {e}")
            return None

    def unzip_and_read_csv(zip_path, extract_dir="./gc_downloads", chunksize=None):
        """
        Unzips the first CSV in the ZIP file and reads it into a DataFrame.
        If chunksize is provided, returns an iterator over DataFrame chunks.
        """
        # Find CSV inside ZIP
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_files = [
                name for name in zf.namelist() if name.lower().endswith(".csv")
            ]
            if not csv_files:
                raise RuntimeError("No CSV found inside ZIP.")
            csv_name = csv_files[0]
            csv_path = os.path.join(extract_dir, os.path.basename(csv_name))

            # Extract only if not already present
            if not os.path.exists(csv_path):
                os.makedirs(extract_dir, exist_ok=True)
                zf.extract(csv_name, path=extract_dir)
                # If the ZIP had subfolders, move the CSV to extract_dir root
                extracted_path = os.path.join(extract_dir, csv_name)
                if extracted_path != csv_path and os.path.exists(extracted_path):
                    os.rename(extracted_path, csv_path)

        # Read CSV
        if chunksize:
            return pd.read_csv(csv_path, chunksize=chunksize, dtype="str")
        else:
            return pd.read_csv(csv_path, dtype="str")

    def download_and_read_csv_in_memory(self, url: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Download CSV from URL and read it directly into memory without saving to disk.
        
        Args:
            url: URL to download the CSV from
            columns: Optional list of column names to read. If None, reads all columns.
            
        Returns:
            pandas.DataFrame: The CSV data
        """
        print(f"Downloading CSV directly to memory from: {url}")
        
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            
            # Read the response content
            content = r.content
            
            # Create a BytesIO object to read the CSV
            csv_buffer = io.BytesIO(content)
            
            # Read CSV with optional column selection
            if columns:
                print(f"Reading only selected columns: {len(columns)} columns")
                df = pd.read_csv(csv_buffer, usecols=columns, dtype="str")
            else:
                print("Reading all columns")
                df = pd.read_csv(csv_buffer, dtype="str")
                
        print(f"Successfully loaded {len(df):,} rows and {len(df.columns)} columns into memory")
        return df

    def download_zip_and_read_csv_in_memory(self, url: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Download ZIP file and read CSV directly into memory without saving to disk.
        
        Args:
            url: URL to download the ZIP file from
            columns: Optional list of column names to read. If None, reads all columns.
            
        Returns:
            pandas.DataFrame: The CSV data from the ZIP file
        """
        print(f"Downloading ZIP file directly to memory from: {url}")
        
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            
            # Read the response content
            zip_content = r.content
            
            # Create a BytesIO object to read the ZIP
            zip_buffer = io.BytesIO(zip_content)
            
            # Find CSV inside ZIP
            with zipfile.ZipFile(zip_buffer, "r") as zf:
                csv_files = [
                    name for name in zf.namelist() if name.lower().endswith(".csv")
                ]
                if not csv_files:
                    raise RuntimeError("No CSV found inside ZIP.")
                csv_name = csv_files[0]
                
                # Read CSV from ZIP
                with zf.open(csv_name) as csv_file:
                    if columns:
                        print(f"Reading only selected columns: {len(columns)} columns")
                        df = pd.read_csv(csv_file, usecols=columns, dtype="str")
                    else:
                        print("Reading all columns")
                        df = pd.read_csv(csv_file, dtype="str")
                        
        print(f"Successfully loaded {len(df):,} rows and {len(df.columns)} columns into memory")
        return df

    @classmethod
    async def download_for_date_in_memory(
        cls, 
        date: str, 
        save_dir: str = "./gc_downloads",
        columns: Optional[List[str]] = None,
        keep_in_memory: bool = False
    ) -> Union[str, pd.DataFrame]:
        """
        Enhanced class method to download GLEIF Golden Copy for a specific date.
        Supports column selection and in-memory processing.
        
        Args:
            date: Date in YYYY-MM-DD format
            save_dir: Directory to save the downloaded file (ignored if keep_in_memory=True)
            columns: Optional list of column names to read. If None, reads all columns.
            keep_in_memory: If True, returns DataFrame directly. If False, returns file path.
            
        Returns:
            str: Path to downloaded file (if keep_in_memory=False)
            pd.DataFrame: The CSV data (if keep_in_memory=True)
        """
        downloader = cls(
            page_url="https://goldencopy.gleif.org/api/v2/golden-copies/publishes/",
            save_dir=save_dir,
        )
        
        if keep_in_memory:
            return await downloader.prepare_download_in_memory(date, columns)
        else:
            return await downloader.prepare_download(date)

    async def prepare_download_in_memory(self, date: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Prepare the downloader for the given date and return data in memory.
        
        Args:
            date: Date in YYYY-MM-DD format
            columns: Optional list of column names to read
            
        Returns:
            pd.DataFrame: The CSV data
        """
        try:
            # Try to get available file
            url = await self.find_download_url(date, "00:00", "csv", "lei2")
            print(f"Found URL for: {url}")
            
            # Download and read directly into memory
            df = self.download_zip_and_read_csv_in_memory(url, columns)
            print("Data loaded successfully into memory")
            return df
            
        except Exception as e:
            print(f"Failed to download file for date {date}: {e}")
            raise

    @classmethod
    async def download_with_config(
        cls,
        date: str,
        save_to_disk: bool = True,
        use_full_dataset: bool = True,
        essential_columns: Optional[List[str]] = None,
        save_dir: str = "./gc_downloads"
    ) -> pd.DataFrame:
        """
        Download GLEIF Golden Copy data with configuration options.
        
        Args:
            date: Date in YYYY-MM-DD format
            save_to_disk: If True, save to disk; if False, keep in memory only
            use_full_dataset: If True, use all columns; if False, use only essential_columns
            essential_columns: List of column names to use when use_full_dataset=False
            save_dir: Directory to save files (ignored if save_to_disk=False)
            
        Returns:
            pd.DataFrame: The loaded data
        """
        print(f"Downloading data for date: {date}")
        
        if not save_to_disk:
            print("Downloading data directly to memory...")
            if not use_full_dataset and essential_columns:
                print(f"Using subset of {len(essential_columns)} columns")
                level_1_data = await cls.download_for_date_in_memory(
                    date, 
                    columns=essential_columns, 
                    keep_in_memory=True
                )
            else:
                print("Using full dataset - Download may take a while")
                level_1_data = await cls.download_for_date_in_memory(
                    date, 
                    keep_in_memory=True
                )
            print(f"Data loaded in memory: {level_1_data.shape[0]:,} rows × {level_1_data.shape[1]} columns")
            
        else:
            print("Downloading data to disk...")
            file_path = await cls.download_for_date(date, save_dir)
            
            # Read from disk with optional column selection
            if not use_full_dataset and essential_columns:
                print(f"Reading subset of {len(essential_columns)} columns from disk")
                level_1_data = cls.unzip_and_read_csv(file_path)
                # Filter columns after reading
                available_columns = [col for col in essential_columns if col in level_1_data.columns]
                missing_columns = [col for col in essential_columns if col not in level_1_data.columns]
                
                if missing_columns:
                    print(f"Warning: Some columns not found: {missing_columns}")
                
                level_1_data = level_1_data[available_columns]
                print(f"Data loaded from disk: {level_1_data.shape[0]:,} rows × {level_1_data.shape[1]} columns")
            else:
                print("Reading full dataset from disk")
                level_1_data = cls.unzip_and_read_csv(file_path)
                print(f"Data loaded from disk: {level_1_data.shape[0]:,} rows × {level_1_data.shape[1]} columns")

        print(f"Memory usage: {level_1_data.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        return level_1_data