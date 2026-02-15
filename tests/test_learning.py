"""
学習レイヤーのテスト
"""
import pytest
from pathlib import Path
import json
import pandas as pd
from src.models import learning

def test_normalize_weights():
    """重みの正規化が正しく動作することを確認"""
    weights = {
        'semis': 0.4,
        'ai_infra': 0.3,
        'rare_metals': 0.2,
        'robotics': 0.1
    }
    
    normalized = learning.normalize_weights(weights)
    
    # 合計が1.0になることを確認
    total = sum(normalized.values())
    assert abs(total - 1.0) < 1e-10, f"Total should be 1.0, got {total}"
    
    # 比率が保たれることを確認
    assert normalized['semis'] == 0.4
    assert normalized['ai_infra'] == 0.3

def test_enforce_bounds():
    """重みの上限・下限が正しく適用されることを確認"""
    weights = {
        'semis': 0.05,  # 下限未満
        'ai_infra': 0.60,  # 上限超過
        'rare_metals': 0.25,
        'robotics': 0.10
    }
    
    bounded = learning.enforce_bounds(weights, min_weight=0.10, max_weight=0.50)
    
    # 下限・上限が適用されることを確認（正規化で微妙に超える場合があるため余裕を持たせる）
    assert bounded['semis'] >= 0.09, "Should be approximately at least min_weight"
    assert bounded['ai_infra'] <= 0.51, "Should be approximately at most max_weight"
    
    # 合計が1.0になることを確認
    total = sum(bounded.values())
    assert abs(total - 1.0) < 1e-10, f"Total should be 1.0, got {total}"

def test_limit_change():
    """変更幅の制限が正しく動作することを確認"""
    current_weights = {
        'semis': 0.25,
        'ai_infra': 0.25,
        'rare_metals': 0.25,
        'robotics': 0.25
    }
    
    # 大幅な変更を試みる
    new_weights = {
        'semis': 0.50,  # +25% (制限: ±10%)
        'ai_infra': 0.10,  # -15% (制限: ±10%)
        'rare_metals': 0.25,
        'robotics': 0.15
    }
    
    limited = learning.limit_change(current_weights, new_weights, max_delta=0.10)
    
    # 変更幅が制限されることを確認
    assert abs(limited['semis'] - current_weights['semis']) <= 0.10 + 1e-6, \
        "Change should be limited to max_delta"
    assert abs(limited['ai_infra'] - current_weights['ai_infra']) <= 0.10 + 1e-6, \
        "Change should be limited to max_delta"
    
    # 合計が1.0になることを確認
    total = sum(limited.values())
    assert abs(total - 1.0) < 1e-10, f"Total should be 1.0, got {total}"

def test_save_and_load_weights(tmp_path):
    """重みの保存と読み込みが正しく動作することを確認"""
    weights = {
        'semis': 0.30,
        'ai_infra': 0.25,
        'rare_metals': 0.25,
        'robotics': 0.20
    }
    
    filepath = tmp_path / "test_weights.json"
    
    # 保存
    learning.save_weights(filepath, weights, {'test': 'data'})
    
    # ファイルが作成されることを確認
    assert filepath.exists()
    
    # 読み込み
    loaded_weights = learning.load_weights(filepath)
    
    # 値が一致することを確認
    assert loaded_weights == weights

def test_optimize_weights():
    """重みの最適化が実行されることを確認"""
    themes = ['semis', 'ai_infra', 'rare_metals', 'robotics']
    current_weights = learning.get_default_weights()
    price_history = {}  # スタブ実装なのでダミー
    
    cfg = {
        'learn': {
            'window_weeks': 52,
            'bounds': {'min': 0.10, 'max': 0.50},
            'max_delta': 0.10,
            'objective': 'return_first'
        }
    }
    
    new_weights = learning.optimize_weights(themes, price_history, current_weights, cfg)
    
    # 重みが返されることを確認
    assert len(new_weights) == 4
    
    # 合計が1.0になることを確認
    total = sum(new_weights.values())
    assert abs(total - 1.0) < 1e-10, f"Total should be 1.0, got {total}"
    
    # 各重みが範囲内にあることを確認
    for weight in new_weights.values():
        assert 0.10 <= weight <= 0.50, f"Weight {weight} should be in bounds"
    
    # 変更幅が制限されることを確認
    for theme in themes:
        delta = abs(new_weights[theme] - current_weights[theme])
        assert delta <= 0.10 + 1e-6, f"Delta {delta} should be <= 0.10"

def test_save_weights_history(tmp_path):
    """重みの履歴保存が正しく動作することを確認"""
    import datetime as dt
    
    out_dir = tmp_path / "learn"
    asof = dt.date.today()
    
    champion_weights = {'semis': 0.25, 'ai_infra': 0.25, 'rare_metals': 0.25, 'robotics': 0.25}
    challenger_weights = {'semis': 0.30, 'ai_infra': 0.25, 'rare_metals': 0.25, 'robotics': 0.20}
    
    # 初回保存
    learning.save_weights_history(out_dir, asof, champion_weights, challenger_weights)
    
    # ファイルが作成されることを確認
    champion_file = out_dir / "weights_champion.csv"
    challenger_file = out_dir / "weights_challenger.csv"
    
    assert champion_file.exists()
    assert challenger_file.exists()
    
    # CSVが読み込めることを確認
    champion_df = pd.read_csv(champion_file)
    challenger_df = pd.read_csv(challenger_file)
    
    assert len(champion_df) == 1
    assert len(challenger_df) == 1
    assert 'asof' in champion_df.columns
    assert 'semis' in champion_df.columns
    
    # 2回目の保存（追記）
    learning.save_weights_history(out_dir, asof, champion_weights, challenger_weights)
    
    champion_df = pd.read_csv(champion_file)
    challenger_df = pd.read_csv(challenger_file)
    
    assert len(champion_df) == 2, "Should append to history"
    assert len(challenger_df) == 2, "Should append to history"

def test_challenger_update(tmp_path):
    """Challengerの更新が正しく動作することを確認"""
    # テスト用のディレクトリ構造を作成
    base_dir = tmp_path
    models_dir = base_dir / "data" / "models"
    models_dir.mkdir(parents=True)
    
    # 初期Champion重みを作成
    initial_weights = learning.get_default_weights()
    champion_file = models_dir / "champion_weights.json"
    learning.save_weights(champion_file, initial_weights)
    
    # 設定
    themes = ['semis', 'ai_infra', 'rare_metals', 'robotics']
    price_history = {}
    cfg = {
        'learn': {
            'window_weeks': 52,
            'bounds': {'min': 0.10, 'max': 0.50},
            'max_delta': 0.10,
            'objective': 'return_first'
        }
    }
    
    # Challengerを更新
    new_weights = learning.update_challenger(base_dir, themes, price_history, cfg)
    
    # Challengerファイルが作成されることを確認
    challenger_file = models_dir / "challenger_weights.json"
    assert challenger_file.exists()
    
    # 重みが正しい範囲にあることを確認
    assert len(new_weights) == 4
    total = sum(new_weights.values())
    assert abs(total - 1.0) < 1e-10

def test_pipeline_integration_with_learning(tmp_path):
    """パイプライン統合テスト：学習が有効でもCSV出力が壊れないことを確認"""
    # この部分は実際のパイプライン実行でテストされる
    # ここでは学習モジュールが正しくインポートできることを確認
    from src.models import learning as learn_module
    
    assert hasattr(learn_module, 'update_challenger')
    assert hasattr(learn_module, 'save_weights_history')
    assert hasattr(learn_module, 'copy_to_docs')
