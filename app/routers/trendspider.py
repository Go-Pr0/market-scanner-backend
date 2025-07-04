"""
TrendSpider API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging

from ..core.security import require_auth
from ..services.trendspider_service import trendspider_service
from ..models.trendspider import (
    ScanRequest, ScanResponse, ConfigurationModel, ConfigurationResponse,
    ConfigurationListResponse, SymbolListResponse, TimeframeOptionsResponse
)

router = APIRouter(prefix="/trendspider", tags=["trendspider"])
logger = logging.getLogger(__name__)

@router.post("/scan", response_model=ScanResponse)
async def run_scan(request: ScanRequest, _: str = Depends(require_auth)):
    """
    Run an EMA scan with the specified parameters
    
    Args:
        request: Scan request parameters
        
    Returns:
        Scan results with EMA calculations and filtering
    """
    try:
        result = await trendspider_service.run_scan(
            symbols_list=request.symbols,
            timeframe=request.timeframe,
            ema_periods=request.ema_periods,
            filter_conditions=request.filter_conditions,
            sort_by=request.sort_by,
            show_only_matching=request.show_only_matching,
            batch_size=request.batch_size
        )
        
        return ScanResponse(**result)
        
    except Exception as e:
        logger.error(f"Error running scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/{scan_id}/csv")
async def get_scan_csv(scan_id: str, _: str = Depends(require_auth)):
    """
    Get scan results in CSV format for TradingView import
    
    Args:
        scan_id: ID of the scan to export
        
    Returns:
        CSV content as plain text
    """
    # Note: This is a placeholder endpoint. In a real implementation,
    # you would store scan results and retrieve them by ID.
    raise HTTPException(status_code=501, detail="CSV export not yet implemented")

@router.get("/configurations", response_model=ConfigurationListResponse)
async def list_configurations(user_configs: bool = True, _: str = Depends(require_auth)):
    """
    List available configurations
    
    Args:
        user_configs: Whether to list user configs (True) or system configs (False)
        
    Returns:
        List of configuration names
    """
    try:
        configs = trendspider_service.list_configurations(user_configs)
        return ConfigurationListResponse(
            success=True,
            configurations=configs
        )
        
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configurations/{config_name}", response_model=ConfigurationResponse)
async def get_configuration(config_name: str, user_config: bool = True, _: str = Depends(require_auth)):
    """
    Get a specific configuration
    
    Args:
        config_name: Name of the configuration
        user_config: Whether to look in user configs (True) or system configs (False)
        
    Returns:
        Configuration data
    """
    try:
        config_data = trendspider_service.get_configuration(config_name, user_config)
        
        if config_data is None:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")
        
        return ConfigurationResponse(
            success=True,
            configuration=ConfigurationModel(**config_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/configurations", response_model=ConfigurationResponse)
async def create_configuration(
    config_name: str,
    config_data: ConfigurationModel,
    user_config: bool = True,
    _: str = Depends(require_auth)
):
    """
    Create a new configuration
    
    Args:
        config_name: Name for the new configuration
        config_data: Configuration data
        user_config: Whether to save as user config (True) or system config (False)
        
    Returns:
        Success status and configuration data
    """
    try:
        success = trendspider_service.save_configuration(
            config_data.dict(), config_name, user_config
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
        
        return ConfigurationResponse(
            success=True,
            message=f"Configuration '{config_name}' created successfully",
            configuration=config_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/configurations/{config_name}", response_model=ConfigurationResponse)
async def update_configuration(
    config_name: str,
    config_data: ConfigurationModel,
    user_config: bool = True,
    _: str = Depends(require_auth)
):
    """
    Update an existing configuration
    
    Args:
        config_name: Name of the configuration to update
        config_data: Updated configuration data
        user_config: Whether to update user config (True) or system config (False)
        
    Returns:
        Success status and updated configuration data
    """
    try:
        success = trendspider_service.save_configuration(
            config_data.dict(), config_name, user_config
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update configuration")
        
        return ConfigurationResponse(
            success=True,
            message=f"Configuration '{config_name}' updated successfully",
            configuration=config_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/configurations/{config_name}")
async def delete_configuration(config_name: str, user_config: bool = True, _: str = Depends(require_auth)):
    """
    Delete a configuration
    
    Args:
        config_name: Name of the configuration to delete
        user_config: Whether to delete from user configs (True) or system configs (False)
        
    Returns:
        Success status
    """
    try:
        success = trendspider_service.delete_configuration(config_name, user_config)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")
        
        return {"success": True, "message": f"Configuration '{config_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configurations/active/current", response_model=ConfigurationResponse)
async def get_active_configuration(_: str = Depends(require_auth)):
    """
    Get the currently active configuration
    
    Returns:
        Active configuration data
    """
    try:
        active_config_name = trendspider_service.get_active_configuration()
        config_data = trendspider_service.get_current_config()
        
        return ConfigurationResponse(
            success=True,
            message=f"Active configuration: {active_config_name}",
            configuration=ConfigurationModel(**config_data)
        )
        
    except Exception as e:
        logger.error(f"Error getting active configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/configurations/active/{config_name}")
async def set_active_configuration(config_name: str, _: str = Depends(require_auth)):
    """
    Set the active configuration
    
    Args:
        config_name: Name of the configuration to make active
        
    Returns:
        Success status
    """
    try:
        success = trendspider_service.set_active_configuration(config_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_name}' not found")
        
        return {"success": True, "message": f"Configuration '{config_name}' is now active"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols", response_model=SymbolListResponse)
async def get_available_symbols(_: str = Depends(require_auth)):
    """
    Get the list of available symbols for scanning
    
    Returns:
        List of available symbols
    """
    try:
        symbols = trendspider_service.get_available_symbols()
        
        return SymbolListResponse(
            success=True,
            symbols=symbols,
            count=len(symbols)
        )
        
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeframes", response_model=TimeframeOptionsResponse)
async def get_timeframe_options(_: str = Depends(require_auth)):
    """
    Get available timeframe options
    
    Returns:
        Dictionary of timeframe codes and labels
    """
    try:
        timeframes = trendspider_service.get_timeframe_options()
        
        return TimeframeOptionsResponse(
            success=True,
            timeframes=timeframes
        )
        
    except Exception as e:
        logger.error(f"Error getting timeframes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 