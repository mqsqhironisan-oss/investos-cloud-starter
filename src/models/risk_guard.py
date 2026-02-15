"""
リスク管理モジュール
"""
import logging
import pandas as pd
from typing import Dict

logger = logging.getLogger(__name__)

def apply_risk_controls(signals: pd.DataFrame, cfg: dict, portfolio_state: Dict = None) -> pd.DataFrame:
    """
    リスク管理ルールを適用
    
    Args:
        signals: シグナルDataFrame
        cfg: 設定（risk: dd_warn, dd_stop, max_weight）
        portfolio_state: ポートフォリオ状態（将来実装用、現在は未使用）
    
    Returns:
        リスク管理適用後のシグナルDataFrame
    
    TODO: 実装の詳細化
    - portfolio_stateを使用したドローダウン制御（DD警告/停止）
    - 最大ポジションサイズ制限
    - 構造破壊検知（テーマ強度低下＋イベント悪化）
    - トレンド破壊検知
    - 売却ルールの自動化
    """
    logger.info(f"Applying risk controls to {len(signals)} signals")
    
    # スタブ: そのまま返す（リスク管理は将来実装）
    # TODO: ポートフォリオ状態（portfolio_state）を追跡し、DD制御を実装
    
    dd_warn = cfg["risk"]["dd_warn"]
    dd_stop = cfg["risk"]["dd_stop"]
    max_weight = cfg["risk"]["max_weight"]
    
    logger.info(f"Risk params: DD warn={dd_warn}, DD stop={dd_stop}, max_weight={max_weight}")
    
    return signals
