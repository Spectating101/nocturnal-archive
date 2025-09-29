#!/usr/bin/env python3
"""
Data Loaders - CSV loading and dataframe registry
"""

import os
import pandas as pd
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DataInfo:
    shape: tuple
    columns: List[str]
    sample: List[Dict[str, Any]]
    dtypes: Dict[str, str]
    file_path: str

class DataLoader:
    """Data loading and registry management"""
    
    def __init__(self):
        self.dataframe_registry: Dict[str, pd.DataFrame] = {}
        self.data_info_registry: Dict[str, DataInfo] = {}
    
    def load_csv(self, path: str, sample_rows: int = 20) -> Dict[str, Any]:
        """
        Load CSV file and return info + sample data
        
        Args:
            path: Path to CSV file
            sample_rows: Number of rows to sample for preview
        
        Returns:
            Dict with shape, columns, sample, dtypes, registry_key
        """
        try:
            # Check if file exists
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"File not found: {path}",
                    "shape": None,
                    "columns": None,
                    "sample": None,
                    "dtypes": None,
                    "registry_key": None
                }
            
            # Load CSV
            df = pd.read_csv(path)
            
            # Generate registry key
            registry_key = f"df_{len(self.dataframe_registry)}"
            
            # Store in registry
            self.dataframe_registry[registry_key] = df
            
            # Get sample data
            sample_df = df.head(sample_rows)
            sample_data = sample_df.to_dict('records')
            
            # Get data types
            dtypes = df.dtypes.astype(str).to_dict()
            
            # Create data info
            data_info = DataInfo(
                shape=df.shape,
                columns=df.columns.tolist(),
                sample=sample_data,
                dtypes=dtypes,
                file_path=path
            )
            
            # Store data info
            self.data_info_registry[registry_key] = data_info
            
            return {
                "success": True,
                "error": None,
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "sample": sample_data,
                "dtypes": dtypes,
                "registry_key": registry_key,
                "file_path": path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error loading CSV: {str(e)}",
                "shape": None,
                "columns": None,
                "sample": None,
                "dtypes": None,
                "registry_key": None
            }
    
    def list_data(self, workspace: str = ".", glob_pattern: str = "*.csv") -> Dict[str, Any]:
        """
        List data files in workspace
        
        Args:
            workspace: Directory to search
            glob_pattern: File pattern to match
        
        Returns:
            Dict with list of files and their info
        """
        try:
            workspace_path = Path(workspace)
            if not workspace_path.exists():
                return {
                    "success": False,
                    "error": f"Workspace not found: {workspace}",
                    "files": []
                }
            
            files = []
            for file_path in workspace_path.glob(glob_pattern):
                if file_path.is_file():
                    file_info = {
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    }
                    files.append(file_info)
            
            return {
                "success": True,
                "error": None,
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing files: {str(e)}",
                "files": []
            }
    
    def get_dataframe(self, registry_key: str) -> Optional[pd.DataFrame]:
        """Get dataframe from registry"""
        return self.dataframe_registry.get(registry_key)
    
    def get_data_info(self, registry_key: str) -> Optional[DataInfo]:
        """Get data info from registry"""
        return self.data_info_registry.get(registry_key)
    
    def list_registry(self) -> Dict[str, Any]:
        """List all registered dataframes"""
        registry_info = {}
        for key, data_info in self.data_info_registry.items():
            registry_info[key] = {
                "shape": data_info.shape,
                "columns": data_info.columns,
                "file_path": data_info.file_path
            }
        return registry_info

# Global instance
data_loader = DataLoader()

def load_csv(path: str, sample_rows: int = 20) -> Dict[str, Any]:
    """Load CSV file and return info"""
    return data_loader.load_csv(path, sample_rows)

def list_data(workspace: str = ".", glob_pattern: str = "*.csv") -> Dict[str, Any]:
    """List data files in workspace"""
    return data_loader.list_data(workspace, glob_pattern)

def get_dataframe(registry_key: str) -> Optional[pd.DataFrame]:
    """Get dataframe from registry"""
    return data_loader.get_dataframe(registry_key)

def list_registry() -> Dict[str, Any]:
    """List all registered dataframes"""
    return data_loader.list_registry()
