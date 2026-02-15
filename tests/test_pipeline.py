"""
週次パイプラインの基本テスト
"""
import pytest
from pathlib import Path
import subprocess
import pandas as pd
import os

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "out"

def test_pipeline_execution():
    """パイプラインが正常に実行されることを確認"""
    result = subprocess.run(
        ["python", str(BASE / "src" / "pipeline_weekly.py")],
        cwd=str(BASE),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    assert "Weekly Pipeline Completed" in result.stdout

def test_output_files_exist():
    """必須の出力ファイルが生成されることを確認"""
    required_files = ["theme_strength.csv", "signals.csv", "orders.csv", "regime.csv"]
    
    for filename in required_files:
        filepath = OUT / filename
        assert filepath.exists(), f"Required file not found: {filename}"

def test_theme_strength_csv_structure():
    """theme_strength.csvの構造を検証"""
    df = pd.read_csv(OUT / "theme_strength.csv")
    
    # 必須カラムの確認
    required_columns = ["asof", "theme", "strength"]
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # データが存在することを確認
    assert len(df) > 0, "theme_strength.csv is empty"
    
    # テーマ名が正しいことを確認
    expected_themes = {"半導体", "AIインフラ", "レアメタル", "ロボティクス"}
    actual_themes = set(df["theme"].values)
    assert expected_themes == actual_themes, f"Unexpected themes: {actual_themes}"

def test_signals_csv_structure():
    """signals.csvの構造を検証"""
    df = pd.read_csv(OUT / "signals.csv")
    
    # 必須カラムの確認
    required_columns = ["asof", "symbol", "action", "score", "theme", "reason", "side", "qty_jpy"]
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # データが存在することを確認（最低1件）
    assert len(df) > 0, "signals.csv is empty"

def test_orders_csv_structure():
    """orders.csvの構造を検証"""
    df = pd.read_csv(OUT / "orders.csv")
    
    # 必須カラムの確認
    required_columns = ["asof", "symbol", "market", "side", "order_type", "limit_price", "qty", "note"]
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # データが存在することを確認（最低1件）
    assert len(df) > 0, "orders.csv is empty"

def test_pipeline_error_handling_missing_config():
    """設定ファイルがない場合のエラーハンドリングを確認"""
    # config.yamlを一時的にリネーム
    config_path = BASE / "config.yaml"
    config_backup = BASE / "config.yaml.backup"
    
    if config_path.exists():
        config_path.rename(config_backup)
    
    try:
        result = subprocess.run(
            ["python", str(BASE / "src" / "pipeline_weekly.py")],
            cwd=str(BASE),
            capture_output=True,
            text=True
        )
        
        # エラーで終了すること
        assert result.returncode != 0, "Pipeline should fail without config.yaml"
        
    finally:
        # 元に戻す
        if config_backup.exists():
            config_backup.rename(config_path)

def test_regime_csv_structure():
    """regime.csvの構造を検証"""
    df = pd.read_csv(OUT / "regime.csv")
    
    # 必須カラムの確認
    required_columns = ["date", "regime", "score", "reasons"]
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # データが存在することを確認
    assert len(df) > 0, "regime.csv is empty"
    
    # regimeが有効な値であることを確認
    valid_regimes = {"RISK_ON", "RISK_OFF", "NEUTRAL"}
    actual_regime = df.iloc[-1]["regime"]
    assert actual_regime in valid_regimes, f"Invalid regime: {actual_regime}"

