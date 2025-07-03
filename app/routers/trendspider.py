"""
TrendSpider API Router

FastAPI router for TrendSpider EMA scanner endpoints.
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from typing import Dict, List, Optional
import logging

from ..services.trendspider_service import trendspider_service
from ..models.trendspider import (
    ScanRequest, ScanResponse, SymbolResult,
    ConfigurationModel, ConfigurationCreateRequest, ConfigurationUpdateRequest,
    ConfigurationResponse, ConfigurationListResponse, ValidationResponse,
    TimeframeOptionsResponse, SymbolsResponse, ActiveConfigResponse,
    SetActiveConfigRequest, BasicResponse
)

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/trendspider", tags=["TrendSpider EMA Scanner"])

@router.post("/scan", response_model=ScanResponse)
async def run_ema_scan(request: ScanRequest):
    """
    Run an EMA scan with the specified parameters
    
    This endpoint performs an EMA (Exponential Moving Average) scan on cryptocurrency symbols
    using data from the bybit_data_fetcher database.
    """
    try:
        logger.info(f"Starting EMA scan with parameters: {request.dict()}")
        
        # Run the scan
        scan_results = await trendspider_service.run_scan(
            symbols_list=request.symbols,
            timeframe=request.timeframe,
            ema_periods=request.ema_periods,
            filter_conditions=request.filter_conditions,
            sort_by=request.sort_by,
            show_only_matching=request.show_only_matching,
            batch_size=request.batch_size
        )
        
        # Convert to response model
        if scan_results.get("success", False):
            # Convert results to SymbolResult models
            symbol_results = []
            for result in scan_results.get("results", []):
                symbol_results.append(SymbolResult(**result))
            
            matching_results = []
            for result in scan_results.get("matching_results", []):
                matching_results.append(SymbolResult(**result))
            
            return ScanResponse(
                success=True,
                scan_id=scan_results.get("scan_id"),
                timestamp=scan_results.get("timestamp"),
                duration_seconds=scan_results.get("duration_seconds"),
                timeframe=scan_results.get("timeframe"),
                timeframe_label=scan_results.get("timeframe_label"),
                ema_periods=scan_results.get("ema_periods"),
                filter_conditions=scan_results.get("filter_conditions"),
                sort_by=scan_results.get("sort_by"),
                show_only_matching=scan_results.get("show_only_matching"),
                total_symbols_scanned=scan_results.get("total_symbols_scanned"),
                successful_scans=scan_results.get("successful_scans"),
                failed_scans=scan_results.get("failed_scans"),
                matching_symbols=scan_results.get("matching_symbols"),
                results=symbol_results,
                matching_results=matching_results,
                formatted_text=scan_results.get("formatted_text"),
                failed_symbols=scan_results.get("failed_symbols")
            )
        else:
            return ScanResponse(
                success=False,
                timestamp=scan_results.get("timestamp"),
                error=scan_results.get("error")
            )
            
    except Exception as e:
        logger.error(f"Error running EMA scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running EMA scan: {str(e)}")

@router.post("/scan/csv")
async def run_ema_scan_csv(request: ScanRequest):
    """
    Run an EMA scan and return results as CSV
    
    This endpoint performs an EMA scan and returns the results in CSV format
    suitable for importing into TradingView or other platforms.
    """
    try:
        logger.info(f"Starting EMA scan for CSV export with parameters: {request.dict()}")
        
        # Run the scan
        scan_results = await trendspider_service.run_scan(
            symbols_list=request.symbols,
            timeframe=request.timeframe,
            ema_periods=request.ema_periods,
            filter_conditions=request.filter_conditions,
            sort_by=request.sort_by,
            show_only_matching=request.show_only_matching,
            batch_size=request.batch_size
        )
        
        if not scan_results.get("success", False):
            raise HTTPException(status_code=500, detail=scan_results.get("error", "Scan failed"))
        
        # Generate CSV
        csv_content, filename = trendspider_service.get_scan_results_csv(scan_results)
        
        # Return CSV response
        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running EMA scan for CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running EMA scan: {str(e)}")

@router.get("/configurations", response_model=ConfigurationListResponse)
async def list_configurations(user_configs: bool = True):
    """
    List available configurations
    
    Args:
        user_configs: Whether to list user configurations (True) or system configurations (False)
    """
    try:
        configurations = trendspider_service.list_configurations(user_configs)
        active_config = trendspider_service.get_active_configuration()
        
        return ConfigurationListResponse(
            success=True,
            configurations=configurations,
            active_config=active_config
        )
        
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        return ConfigurationListResponse(
            success=False,
            configurations=[],
            active_config="",
            error=str(e)
        )

@router.post("/configurations", response_model=ConfigurationResponse)
async def create_configuration(request: ConfigurationCreateRequest):
    """
    Create a new configuration
    """
    try:
        # Validate the configuration
        is_valid, errors = trendspider_service.validate_configuration(request.config.dict())
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {', '.join(errors)}")
        
        # Save the configuration
        success = trendspider_service.save_configuration(
            request.config.dict(),
            request.name,
            request.user_config
        )
        
        if success:
            return ConfigurationResponse(
                success=True,
                message=f"Configuration '{request.name}' created successfully",
                config=request.config
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating configuration: {str(e)}")

@router.get("/configurations/{config_name}", response_model=ConfigurationResponse)
async def get_configuration(config_name: str, user_config: bool = True):
    """
    Get a specific configuration
    
    Args:
        config_name: Name of the configuration
        user_config: Whether to look in user configurations (True) or system configurations (False)
    """
    try:
        config_data = trendspider_service.get_configuration(config_name, user_config)
        
        if config_data is None:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")
        
        return ConfigurationResponse(
            success=True,
            config=ConfigurationModel(**config_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configuration '{config_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting configuration: {str(e)}")

@router.put("/configurations/{config_name}", response_model=ConfigurationResponse)
async def update_configuration(config_name: str, request: ConfigurationUpdateRequest):
    """
    Update an existing configuration
    
    Args:
        config_name: Name of the configuration to update
    """
    try:
        # Check if configuration exists
        existing_config = trendspider_service.get_configuration(config_name, request.user_config)
        if existing_config is None:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")
        
        # Validate the new configuration
        is_valid, errors = trendspider_service.validate_configuration(request.config.dict())
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {', '.join(errors)}")
        
        # Save the updated configuration
        success = trendspider_service.save_configuration(
            request.config.dict(),
            config_name,
            request.user_config
        )
        
        if success:
            return ConfigurationResponse(
                success=True,
                message=f"Configuration '{config_name}' updated successfully",
                config=request.config
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration '{config_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")

@router.delete("/configurations/{config_name}", response_model=BasicResponse)
async def delete_configuration(config_name: str, user_config: bool = True):
    """
    Delete a configuration
    
    Args:
        config_name: Name of the configuration to delete
        user_config: Whether to delete from user configurations (True) or system configurations (False)
    """
    try:
        # Check if configuration exists
        existing_config = trendspider_service.get_configuration(config_name, user_config)
        if existing_config is None:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")
        
        # Don't allow deleting the default configuration
        if config_name == "default" and not user_config:
            raise HTTPException(status_code=400, detail="Cannot delete the default system configuration")
        
        # Delete the configuration
        success = trendspider_service.delete_configuration(config_name, user_config)
        
        if success:
            return BasicResponse(
                success=True,
                message=f"Configuration '{config_name}' deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration '{config_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting configuration: {str(e)}")

@router.get("/configurations/active/current", response_model=ActiveConfigResponse)
async def get_active_configuration():
    """
    Get the currently active configuration
    """
    try:
        active_config_name = trendspider_service.get_active_configuration()
        current_config = trendspider_service.get_current_config()
        
        return ActiveConfigResponse(
            active_config=active_config_name,
            config_data=ConfigurationModel(**current_config)
        )
        
    except Exception as e:
        logger.error(f"Error getting active configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting active configuration: {str(e)}")

@router.post("/configurations/active/set", response_model=BasicResponse)
async def set_active_configuration(request: SetActiveConfigRequest):
    """
    Set the active configuration
    """
    try:
        # Check if configuration exists
        config_data = trendspider_service.get_configuration(request.config_name, user_config=True)
        if config_data is None:
            # Try system configs
            config_data = trendspider_service.get_configuration(request.config_name, user_config=False)
            if config_data is None:
                raise HTTPException(status_code=404, detail=f"Configuration '{request.config_name}' not found")
        
        # Set as active
        success = trendspider_service.set_active_configuration(request.config_name)
        
        if success:
            return BasicResponse(
                success=True,
                message=f"Configuration '{request.config_name}' is now active"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to set active configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting active configuration: {str(e)}")

@router.post("/configurations/validate", response_model=ValidationResponse)
async def validate_configuration(config: ConfigurationModel):
    """
    Validate a configuration
    """
    try:
        is_valid, errors = trendspider_service.validate_configuration(config.dict())
        
        return ValidationResponse(
            is_valid=is_valid,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error validating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating configuration: {str(e)}")

@router.get("/timeframes", response_model=TimeframeOptionsResponse)
async def get_timeframe_options():
    """
    Get available timeframe options
    """
    try:
        timeframes = trendspider_service.get_timeframe_options()
        return TimeframeOptionsResponse(timeframes=timeframes)
        
    except Exception as e:
        logger.error(f"Error getting timeframe options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting timeframe options: {str(e)}")

@router.get("/symbols", response_model=SymbolsResponse)
async def get_available_symbols():
    """
    Get the list of available symbols for scanning
    """
    try:
        symbols = trendspider_service.get_available_symbols()
        return SymbolsResponse(symbols=symbols, count=len(symbols))
        
    except Exception as e:
        logger.error(f"Error getting available symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting available symbols: {str(e)}")

@router.post("/configurations/apply", response_model=BasicResponse)
async def apply_configuration_temporarily(config: ConfigurationModel):
    """
    Apply configuration settings temporarily (without saving)
    
    This endpoint allows you to apply configuration settings for the current session
    without permanently saving them. The changes will be lost when the service restarts.
    """
    try:
        # Validate the configuration
        is_valid, errors = trendspider_service.validate_configuration(config.dict())
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {', '.join(errors)}")
        
        # Apply the configuration
        success = trendspider_service.apply_configuration(config.dict())
        
        if success:
            return BasicResponse(
                success=True,
                message="Configuration applied temporarily"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to apply configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error applying configuration: {str(e)}") 