"""
週次パイプライン（オーケストレーション）
責務：各モジュールを呼び出して、データ取得→分析→出力を実行
"""
import logging
import sys
from pathlib import Path
import datetime as dt
import yaml

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# パス設定
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "out"
CFG = BASE / "config.yaml"

# モジュールインポート
from data_sources import price_source, macro_source, filings_source
from models import theme_strength, screener, scoring, risk_guard, learning
from exporters import csv_export
from regime import detect_regime, RegimeState

def load_config():
    """設定ファイルを読み込み"""
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    """週次パイプラインのメイン処理"""
    try:
        logger.info("=== Weekly Pipeline Started ===")
        
        # 設定読み込み
        cfg = load_config()
        asof = dt.date.today()
        OUT.mkdir(exist_ok=True)
        
        # 0. レジーム判定
        logger.info("Phase 0: Regime Detection")
        regime_result = detect_regime(cfg)
        csv_export.export_regime(regime_result, asof, OUT)
        
        # docs用にもコピー
        docs_dir = BASE / "docs" / "data"
        docs_dir.mkdir(parents=True, exist_ok=True)
        csv_export.export_regime(regime_result, asof, docs_dir)
        
        logger.info(f"Regime: {regime_result['state'].value} (score: {regime_result['score']})")
        
        # 1. データ取得フェーズ
        logger.info("Phase 1: Data Collection")
        macro_data = macro_source.fetch_macro_indicators()
        
        # 2. テーマ強度計算
        logger.info("Phase 2: Theme Strength Calculation")
        theme_df = theme_strength.calculate_theme_strength(asof, {}, macro_data)
        csv_export.export_theme_strength(theme_df, OUT)
        
        # トップテーマを取得
        top_theme = theme_df.iloc[0]["theme"] if len(theme_df) > 0 else "半導体"
        logger.info(f"Top theme: {top_theme}")
        
        # 3. 銘柄スクリーニング
        logger.info("Phase 3: Stock Screening")
        symbols = screener.screen_stocks(top_theme, {}, {})
        logger.info(f"Screened {len(symbols)} stocks")
        
        # 価格データと開示情報を取得
        price_data = price_source.fetch_price_data(symbols)
        price_history = price_source.fetch_price_history(symbols, days=90)
        filings_data = filings_source.fetch_filings_data(symbols)
        
        # 4. スコアリングとシグナル生成
        logger.info("Phase 4: Scoring & Signal Generation")
        signals = scoring.score_stocks(asof, top_theme, symbols, price_data, price_history, filings_data, cfg)
        
        # 5. リスク管理
        logger.info("Phase 5: Risk Management")
        signals = risk_guard.apply_risk_controls(signals, cfg)
        csv_export.export_signals(signals, OUT)
        
        # 6. 注文生成と出力
        logger.info("Phase 6: Order Generation")
        
        # RISK_OFF の場合は新規買い注文を停止
        if regime_result['state'] == RegimeState.RISK_OFF:
            logger.info("RISK_OFF detected: Filtering out BUY orders")
            # SELLのみ残す（保有継続）
            signals_filtered = signals[signals['side'] != 'BUY'].copy()
            orders = csv_export.build_orders(asof, signals_filtered)
            logger.info(f"Filtered orders: {len(orders)} (removed BUY orders due to RISK_OFF)")
        else:
            orders = csv_export.build_orders(asof, signals)
        
        csv_export.export_orders(orders, OUT)
        
        # スコア詳細（将来拡張用）
        csv_export.export_scores(asof, OUT)
        
        # 7. 学習レイヤー（シャドーモード）
        learn_cfg = cfg.get('learn', {})
        if learn_cfg.get('enabled', False):
            logger.info("Phase 7: Learning Layer (Shadow Mode)")
            
            # Champion重みを読み込み（本番で使用）
            models_dir = BASE / "data" / "models"
            champion_file = models_dir / "champion_weights.json"
            champion_weights = learning.load_weights(champion_file)
            
            # Challenger重みを生成（学習提案）
            themes_list = [t['name'] for t in cfg['strategy']['themes']]
            challenger_weights = learning.update_challenger(
                BASE, themes_list, price_history, cfg
            )
            
            # 履歴を保存
            learn_out = OUT / "learn"
            learning.save_weights_history(learn_out, asof, champion_weights, challenger_weights)
            
            # GitHub Pages用にコピー
            learning.copy_to_docs(BASE)
            
            logger.info(f"Learning completed: Champion={champion_weights}, Challenger={challenger_weights}")
        else:
            logger.info("Phase 7: Learning Layer (Disabled)")
        
        logger.info(f"=== Weekly Pipeline Completed: {asof}, Top Theme: {top_theme} ===")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
